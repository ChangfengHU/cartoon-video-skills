#!/usr/bin/env python3
"""Validate editorial traceability. Never select topics, approve quality or submit jobs."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate(data, root, stage='plan'):
    errors, pending = [], []
    root = Path(root).resolve()
    def need(ok, code):
        if not ok: errors.append(code)
        return ok
    def nonempty(v): return isinstance(v, str) and bool(v.strip())
    def table(key):
        rows = data.get(key)
        if not need(isinstance(rows, list), key + ':list_required'): return {}
        result = {}
        for row in rows:
            if not need(isinstance(row, dict) and nonempty(row.get('id')), key + ':id_required'): continue
            if not need(row['id'] not in result, key + ':duplicate:' + row['id']): continue
            result[row['id']] = row
        return result
    def refs(value, known, label):
        if not need(isinstance(value, list) and all(isinstance(x, str) for x in value), label + ':list_required'): return []
        need(len(value) == len(set(value)), label + ':duplicate_reference')
        need(all(x in known for x in value), label + ':unknown_reference')
        return value
    def local_file(name):
        if not nonempty(name): return None
        path = (root / name).resolve()
        return path if path.is_relative_to(root) and path.is_file() else None
    if not isinstance(data, dict): return {'errors':['object_required'], 'pending':[], 'record_status':'invalid', 'quality_approved':False}
    need(data.get('schema_version') == 1, 'schema_version')
    need(nonempty(data.get('topic')), 'topic_required')
    style = data.get('style', {})
    need(isinstance(style, dict) and all(nonempty(style.get(k)) for k in ['name','reason']), 'style_reason_required')
    sources, findings, beats = table('sources'), table('findings'), table('beats')
    need(bool(findings), 'findings_required'); need(bool(beats), 'beats_required')
    for sid, s in sources.items():
        need(all(nonempty(s.get(k)) for k in ['locator','scope']), sid + ':source_scope_required')
    selected = set()
    for fid, f in findings.items():
        need(nonempty(f.get('claim')) and nonempty(f.get('reason')), fid + ':claim_and_reason_required')
        need(f.get('kind') in ['fact','observation','interpretation','hypothetical'], fid + ':kind')
        rr = refs(f.get('source_ids'), sources, fid)
        if f.get('kind') in ['fact','observation']: need(bool(rr), fid + ':evidence_required')
        need(f.get('decision') in ['include','omit','defer'], fid + ':decision')
        if f.get('decision') == 'include': selected.add(fid)
    covered = set()
    for bid, b in beats.items():
        rr = refs(b.get('finding_ids'), findings, bid)
        need(bool(rr), bid + ':finding_required')
        need(all(x in selected for x in rr), bid + ':unselected_finding')
        covered.update(rr)
        need(all(nonempty(b.get(k)) for k in ['message','visual','audio']), bid + ':delivery_required')
        need(b.get('evidence_role') in ['evidence','illustration','commentary'], bid + ':evidence_role')
    for fid in sorted(selected - covered): errors.append(fid + ':not_in_beats')
    if stage == 'final':
        a = data.get('artifact', {})
        if not isinstance(a, dict): a = {}
        path = local_file(a.get('path'))
        need(path is not None, 'artifact_missing_or_outside_project')
        digest = None
        if path:
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''): h.update(chunk)
            digest = h.hexdigest()
        need(digest is not None and digest == a.get('sha256'), 'artifact_hash_mismatch')
        duration = a.get('duration')
        valid_duration = isinstance(duration, (int,float)) and not isinstance(duration,bool) and math.isfinite(duration) and duration > 0
        need(valid_duration, 'artifact_duration')
        reviews = data.get('reviews', [])
        if not isinstance(reviews,list): errors.append('reviews:list_required'); reviews=[]
        seen=set()
        for r in reviews:
            if not isinstance(r,dict): errors.append('review:object_required'); continue
            bid, dim, status = r.get('beat_id'), r.get('dimension'), r.get('status')
            if not need(isinstance(bid,str) and bid in beats and dim in ['editorial','visual','audio'], 'review:unknown_target'): continue
            key=(bid,dim)
            need(key not in seen, 'review:duplicate:' + bid + ':' + dim); seen.add(key)
            need(status in ['pass','fail','pending'], 'review:status')
            need(nonempty(r.get('note')), 'review:note_required')
            if status == 'pending': pending.append(bid + ':' + dim); continue
            need(r.get('artifact_sha256') == digest and digest is not None, 'review:stale:' + bid)
            interval = r.get('range')
            valid_range = isinstance(interval,list) and len(interval)==2 and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in interval)
            need(valid_range and valid_duration and 0 <= interval[0] < interval[1] <= duration, 'review:range:' + bid)
            need(local_file(r.get('evidence')) is not None, 'review:evidence_missing:' + bid)
            if status == 'fail': errors.append('review:reported_fail:' + bid + ':' + dim)
        for bid in beats:
            for dim in ['editorial','visual','audio']:
                if (bid,dim) not in seen: pending.append(bid + ':' + dim)
    return {'errors':errors, 'pending':pending, 'record_status':'invalid' if errors else 'pending' if pending else 'plan_complete' if stage=='plan' else 'reported_pass', 'quality_approved':False, 'note':'Validates supplied records only; no semantic verification, viewing, listening or user approval.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');p.add_argument('--stage',choices=['plan','final'],default='plan');a=p.parse_args()
    try:
        report=validate(json.loads(Path(a.file).read_text()),Path(a.file).parent,a.stage)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        raise SystemExit(1 if report['errors'] else 2 if report['pending'] else 0)
    except (OSError,ValueError) as exc: p.exit(1,str(exc)+'\n')
