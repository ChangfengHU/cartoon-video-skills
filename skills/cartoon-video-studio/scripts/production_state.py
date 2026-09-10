#!/usr/bin/env python3
"""Local, locked task ledger. Never submits, retries, deletes or approves cloud work."""
import argparse, contextlib, fcntl, hashlib, json, os, re, tempfile, uuid
from pathlib import Path
from datetime import datetime, timezone

def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text())
def files(root, paths):
    result=[]
    for name in paths:
        p=(root/name).resolve()
        if not p.is_relative_to(root) or not p.is_file(): raise ValueError('Missing file or path outside project: '+name)
        result.append({'path':str(p.relative_to(root)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    return result

@contextlib.contextmanager
def ledger(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/'.production.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        target=root/'PRODUCTION.json'
        state=read(target) if target.exists() else {'schema_version':1,'tasks':{},'history':[]}
        yield root,state
        fd,name=tempfile.mkstemp(prefix='.production-',dir=root)
        try:
            with os.fdopen(fd,'w') as f:json.dump(state,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(name,target)
        finally:
            if os.path.exists(name):os.unlink(name)

def stale(root,tasks,key,seen=None):
    seen=set() if seen is None else seen
    if key in seen:raise ValueError('Cyclic dependencies')
    seen=seen|{key};t=tasks[key]
    if t['status']!='done':return True
    try:
        for field in ['inputs','outputs']:
            expected=t.get(field,[])
            if files(root,[x['path'] for x in expected])!=expected:return True
    except (ValueError,OSError):return True
    return any(stale(root,tasks,d,seen) or t.get('dependency_runs',{}).get(d)!=tasks[d].get('run_id') for d in t['deps'])

def operate(root,action,key=None,**opts):
    with ledger(root) as (root,state):
        tasks=state['tasks']
        if action=='status':
            return {k:{**t,'reusable':not stale(root,tasks,k)} for k,t in tasks.items()}
        if not key or not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',key):raise ValueError('Invalid task id')
        if action=='add':
            deps=opts.get('deps',[])
            if key in tasks:raise ValueError('Task already exists; invalidate rather than overwrite')
            if any(d not in tasks for d in deps):raise ValueError('Dependencies must be registered first')
            tasks[key]={'status':'pending','deps':deps,'input_paths':opts.get('inputs',[]),'outputs':[]}
        else:
            if key not in tasks:raise ValueError('Unknown task')
            t=tasks[key]
            if action=='begin':
                if t['status']=='running':raise ValueError('Recover running task; do not submit again')
                if t.get('remote_job') and t.get('remote_status') not in ['succeeded','failed','cancelled']:raise ValueError('Remote outcome unknown; inspect original job first')
                if not stale(root,tasks,key):raise ValueError('Task is reusable')
                if any(stale(root,tasks,d) for d in t['deps']):raise ValueError('Dependency incomplete or stale')
                t.update(status='running',run_id=uuid.uuid4().hex,inputs=files(root,t['input_paths']),dependency_runs={d:tasks[d]['run_id'] for d in t['deps']},outputs=[],remote_job=None,remote_status=None)
            elif action=='invalidate':
                affected={key}
                while True:
                    expanded=affected|{k for k,v in tasks.items() if any(d in affected for d in v['deps'])}
                    if expanded==affected:break
                    affected=expanded
                if any(tasks[k]['status']=='running' for k in affected):raise ValueError('Resolve running tasks before invalidating')
                for k in affected:tasks[k]['status']='stale'
            else:
                if t.get('run_id')!=opts.get('run_id') or (t['status']!='running' and not (action=='remote' and t['status']=='failed')):raise ValueError('Stale attempt or task is not running')
                if action=='remote':
                    job=opts.get('job');provider=opts.get('provider')
                    if not job or not provider or len(job)>300 or len(provider)>100 or '://' in job:raise ValueError('Use plain provider and job ID, no credential URLs')
                    if t.get('remote_job') and t['remote_job']!={'provider':provider,'id':job}:raise ValueError('Do not overwrite original remote job')
                    rs=opts.get('remote_status','unknown')
                    if rs not in ['unknown','running','succeeded','failed','cancelled']:raise ValueError('Invalid remote status')
                    t.update(remote_job={'provider':provider,'id':job},remote_status=rs)
                    if rs=='succeeded' and t['status']=='failed':t['status']='running'
                elif action=='finish':
                    if t.get('remote_job') and t.get('remote_status')!='succeeded':raise ValueError('Remote result not confirmed successful')
                    if any(stale(root,tasks,d) or t['dependency_runs'][d]!=tasks[d]['run_id'] for d in t['deps']):raise ValueError('Dependencies changed during task')
                    if files(root,t['input_paths'])!=t['inputs']:raise ValueError('Inputs changed during task')
                    outputs=files(root,opts.get('outputs',[]))
                    if not outputs:raise ValueError('At least one actual output required')
                    t.update(status='done',outputs=outputs)
                elif action=='fail':
                    reason=opts.get('reason','').strip()
                    if not reason:raise ValueError('Failure reason required')
                    t.update(status='failed',reason=reason)
                else:raise ValueError('Unknown action')
        state['history'].append({'at':now(),'action':action,'task':key,'snapshot':json.loads(json.dumps(tasks))})
        return tasks[key]

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);p.add_argument('action',choices=['add','begin','remote','finish','fail','invalidate','status']);p.add_argument('task',nargs='?');p.add_argument('--deps',nargs='*',default=[]);p.add_argument('--inputs',nargs='*',default=[]);p.add_argument('--outputs',nargs='*',default=[]);p.add_argument('--run-id');p.add_argument('--job');p.add_argument('--provider');p.add_argument('--remote-status',default='unknown');p.add_argument('--reason')
    a=vars(p.parse_args());root=a.pop('project');action=a.pop('action');key=a.pop('task')
    try:print(json.dumps(operate(root,action,key,**a),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as e:p.exit(1,str(e)+'\n')
