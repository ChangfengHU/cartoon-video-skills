#!/usr/bin/env python3
"""Check recorded evidence against frozen files; never judge artistic quality."""
import argparse
import hashlib
import json
import math
from pathlib import Path

PROFILES = {
    'audio': {'technical', 'intelligibility', 'performance', 'reference'},
    'video': {'technical', 'editorial', 'identity', 'composition', 'motion',
              'intelligibility', 'performance', 'mix', 'captions', 'ending', 'reference'},
}
REVIEW = {'editorial', 'identity', 'composition', 'motion', 'performance', 'mix', 'ending', 'reference'}

def digest(path):
    with path.open('rb') as f:
        h = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
        return h.hexdigest()

def evaluate(report, root):
    root = Path(root).resolve()
    issues = []
    def problem(message):
        issues.append(message)
    def file_ok(item, label):
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not item['path']:
            problem(label + ': missing file'); return False
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root):
            problem(label + ': file outside project'); return False
        if not path.is_file():
            problem(label + ': file missing'); return False
        if item.get('sha256') != digest(path):
            problem(label + ': hash mismatch'); return False
        return True
    profile = report.get('profile')
    if profile not in PROFILES:
        raise ValueError('profile must be audio or video')
    target = report.get('target', {})
    file_ok(target, 'target')
    duration = target.get('duration_seconds')
    if isinstance(duration, bool) or not isinstance(duration, (float, int)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError('positive finite target duration required')
    reference = report.get('reference', {})
    if reference.get('required') is True:
        file_ok(reference, 'reference')
        if not reference.get('source') or not reference.get('selection_basis'):
            problem('reference: source and selection basis required')
    elif reference.get('required') is not False or not reference.get('reason'):
        problem('reference: explicitly require a reference or explain why not applicable')
    checks = report.get('checks', [])
    if not isinstance(checks, list): raise ValueError('checks must be a list')
    by_dimension = {}
    for check in checks:
        if not isinstance(check, dict): raise ValueError('check must be an object')
        dim = check.get('dimension')
        if dim not in PROFILES[profile]:
            problem('unknown dimension: ' + str(dim)); continue
        if dim in by_dimension: problem(dim + ': duplicate dimension')
        by_dimension[dim] = check
        status = check.get('status')
        if status == 'not_applicable':
            if dim not in {'captions', 'reference'} or not check.get('reason'):
                problem(dim + ': invalid exemption')
            if dim == 'reference' and reference.get('required') is not False:
                problem('reference: required comparison cannot be exempt')
            continue
        if status != 'pass': problem(dim + ': ' + str(status)); continue
        if check.get('target_sha256') != target.get('sha256'):
            problem(dim + ': stale target')
        if not check.get('finding') or not check.get('reviewer'):
            problem(dim + ': finding and reviewer required')
        method = check.get('method')
        if method not in {'automated', 'direct_review', 'model_assisted'}:
            problem(dim + ': unknown review method')
        if dim in REVIEW and method != 'direct_review':
            problem(dim + ': assistance alone cannot clear perceptual review')
        evidence = check.get('evidence', [])
        if not isinstance(evidence, list) or not evidence:
            problem(dim + ': evidence required')
        else:
            for item in evidence: file_ok(item, dim + ' evidence')
        ranges = check.get('ranges', [])
        if not isinstance(ranges, list) or not ranges:
            problem(dim + ': inspected ranges required'); continue
        valid = []
        for span in ranges:
            if (not isinstance(span, list) or len(span) != 2 or
                any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in span) or
                not 0 <= span[0] < span[1] <= duration):
                problem(dim + ': invalid range'); continue
            valid.append(span)
        if check.get('coverage') == 'whole':
            end = 0
            for start, stop in sorted(valid):
                if start > end: problem(dim + ': whole coverage has gaps')
                end = max(end, stop)
            if end < duration: problem(dim + ': whole coverage incomplete')
        elif check.get('coverage') != 'sampled':
            problem(dim + ': specify sampled or whole coverage')
        if dim == 'reference' and reference.get('required'):
            if check.get('reference_sha256') != reference.get('sha256'):
                problem('reference: stale comparison')
    for dim in sorted(PROFILES[profile] - by_dimension.keys()): problem(dim + ': missing')
    return {'status': 'candidate' if issues else 'evidence_complete', 'issues': issues,
            'note': 'Verifies recorded files and coverage only; does not prove observations are true, quality is stable, or user approval. Candidate delivery remains allowed with limitations.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.report.read_text()), args.report.parent)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(2 if result['issues'] else 0)
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        parser.exit(1, 'Invalid report: ' + str(exc) + '\n')
