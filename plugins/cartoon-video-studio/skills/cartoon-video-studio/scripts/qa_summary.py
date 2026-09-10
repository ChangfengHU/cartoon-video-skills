#!/usr/bin/env python3
"""Summarize declared evidence coverage; never generate an approval or quality score."""
import argparse,json

def summarize(report):
    checks=report.get('checks',[])
    if not isinstance(checks,list):raise ValueError('checks must be a list')
    groups={d:[] for d in ['technical','visual','audio','editorial']}
    for c in checks:
        if c.get('dimension') not in groups or c.get('status') not in ['pass','fail','pending']:raise ValueError('Invalid check')
        if c['status']!='pending' and (not isinstance(c.get('evidence'),str) or not c['evidence'].strip()):raise ValueError('Observed result requires evidence')
        if not isinstance(c.get('finding'),str) or not c['finding'].strip():raise ValueError('Specific finding required')
        groups[c['dimension']].append(c)
    results={d:('fail' if any(c['status']=='fail' for c in cs) else 'pending' if not cs or any(c['status']=='pending' for c in cs) else 'reported_pass') for d,cs in groups.items()}
    return {'dimensions':results,'needs_review':any(v!='reported_pass' for v in results.values()),'note':'Based on supplied observations only; does not verify listening, visual evidence, whole-film coverage or user approval.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('report');a=p.parse_args()
    try:print(json.dumps(summarize(json.load(open(a.report))),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
