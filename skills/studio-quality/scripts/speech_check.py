#!/usr/bin/env python3
"""Compare locked speech with observed ASR. This is a content gate, not listening."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import unicodedata


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    # Keep letters and numbers (including Chinese). Do not silently map homophones.
    return ''.join(c.lower() for c in unicodedata.normalize('NFKC', text)
                   if unicodedata.category(c)[0] in 'LN')


def compare(segments, observed):
    parts = [normalize(s['text']) for s in segments]
    expected = ''.join(parts)
    actual = normalize(observed)
    if not expected or not actual:
        raise ValueError('Empty script/transcript cannot pass')
    spans = []
    cursor = 0
    for s, part in zip(segments, parts):
        if not part:
            raise ValueError('Empty speech segment')
        spans.append((s['index'], cursor, cursor + len(part)))
        cursor += len(part)
    issues = []
    for tag, a, b, c, d in difflib.SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        affected = [i for i, start, end in spans if
                    (start < b and end > a) or (a == b and start <= a < end)]
        if not affected:
            affected = [spans[-1][0]]
        issues.append(dict(operation=tag, expected=expected[a:b], observed=actual[c:d],
                           segment_indices=affected, expected_span=[a, b],
                           context=expected[max(0, a-8):min(len(expected), b+8)]))
    return expected, issues


def check(timeline, audio, transcript, review=None):
    audio_hash = digest(audio.read_bytes())
    evidence = json.loads(transcript.read_text())
    if evidence.get('audio_sha256') != audio_hash:
        raise ValueError('ASR evidence is missing or bound to a different audio hash')
    if evidence.get('stage') not in ('source', 'final'):
        raise ValueError('ASR evidence needs stage: source or final')
    segments = json.loads(timeline.read_text())['segments']
    if len({s['index'] for s in segments}) != len(segments):
        raise ValueError('Duplicate segment index')
    expected, issues = compare(segments, evidence['text'])
    script_hash = digest(expected.encode())
    for issue in issues:
        issue['id'] = digest(json.dumps([audio_hash, script_hash, issue], sort_keys=True).encode())[:20]
        issue['status'] = 'unresolved'
    if review is not None:
        record = json.loads(review.read_text())
        if record.get('audio_sha256') != audio_hash or record.get('script_sha256') != script_hash:
            raise ValueError('Review is stale after audio/script changes')
        lookup = {i['id']: i for i in issues}
        seen = set()
        for resolution in record.get('resolutions', []):
            key = resolution['id']
            if key not in lookup or key in seen:
                raise ValueError('Unknown/duplicate issue resolution')
            seen.add(key)
            if resolution.get('basis') not in ('listened_asr_error', 'orthographic_equivalence', 'independent_asr'):
                raise ValueError('A real audio defect must be repaired, not waived')
            if not resolution.get('reason', '').strip():
                raise ValueError('Resolution requires a specific reason')
            if resolution['basis'] == 'orthographic_equivalence':
                item = lookup[key]
                if item['operation'] != 'replace' or len(item['expected']) != len(item['observed']):
                    raise ValueError('Missing/extra speech is not an orthographic equivalence')
            path = review.parent / resolution['evidence']
            if not path.is_file() or digest(path.read_bytes()) != resolution.get('evidence_sha256'):
                raise ValueError('Resolution evidence absent or changed')
            if resolution['basis'] == 'independent_asr':
                alternative = json.loads(path.read_text())
                if alternative.get('parent_audio_sha256') != audio_hash:
                    raise ValueError('Independent ASR belongs to another parent audio')
                ids = alternative['segment_indices']
                if not ids or len(set(ids)) != len(ids) or not set(lookup[key]['segment_indices']).issubset(ids):
                    raise ValueError('Independent ASR does not cover affected segments')
                selected = [s for s in segments if s['index'] in ids]
                if len(selected) != len(ids):
                    raise ValueError('Independent ASR includes unknown segments')
                clip = path.parent / alternative['clip']
                raw = path.parent / alternative['raw_asr']
                if digest(clip.read_bytes()) != alternative['clip_sha256'] or digest(raw.read_bytes()) != alternative['raw_asr_sha256']:
                    raise ValueError('Independent audio/ASR changed')
                alternative_text = json.loads(raw.read_text())['text']
                if compare(selected, alternative_text)[1]:
                    raise ValueError('Independent ASR itself still contains a difference')
                # Corroboration proves a second recognition matches; it does not establish listening.
            lookup[key].update(status='reviewed', resolution=resolution)
    unresolved = [i for i in issues if i['status'] == 'unresolved']
    return dict(stage=evidence['stage'], audio_sha256=audio_hash, script_sha256=script_hash,
                asr_evidence_sha256=digest(transcript.read_bytes()),
                segment_count=len(segments), issues=issues, unresolved_count=len(unresolved),
                content_gate='blocked' if unresolved else 'pass',
                subjective_listening='not established by this check', quality_approved=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--timeline', type=Path, required=True)
    p.add_argument('--audio', type=Path, required=True)
    p.add_argument('--transcript', type=Path, required=True)
    p.add_argument('--review', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        report = check(a.timeline, a.audio, a.transcript, a.review)
        a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps({'content_gate': report['content_gate'], 'unresolved': report['unresolved_count']}))
        return 2 if report['unresolved_count'] else 0
    except (ValueError, KeyError, OSError, TypeError) as e:
        p.exit(2, 'Speech check blocked: ' + str(e) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
