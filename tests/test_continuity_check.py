"""Evidence association regression tests, not visual-quality or video-decode tests.

Files here are deliberately tiny synthetic byte fixtures. The independent forward
experiment also ran sample_motion on an actual FFmpeg MP4 and viewed its frames.
"""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/studio-quality/scripts/continuity_check.py'
spec = importlib.util.spec_from_file_location('continuity_check', SCRIPT)
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


class EvidenceAssociationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('reference.mp4', 'clip.mp4', 'new.mp4', 'input.png', 'one.png', 'two.png'):
            (self.root / name).write_bytes(('SYNTHETIC UNIT FIXTURE ' + name).encode())
        sample = {'source_sha256': self.asset('clip.mp4')['sha256'], 'frame_count': 2,
                  'files': [self.asset('one.png'), self.asset('two.png')]}
        (self.root / 'sample.json').write_text(json.dumps(sample))
        seq = {'id': 'other-character', 'range': [0, 2], 'intent': 'reaction',
               'contact': 'feet grounded', 'end_state': 'relaxed',
               'states': [{'at': 0, 'pose': 'alert', 'gaze': 'front'},
                          {'at': 1, 'pose': 'relaxed', 'gaze': 'down'}],
               'inputs': [self.asset('input.png')]}
        seq['preflight'] = {'inputs_digest': cc.inputs_digest(seq['inputs']),
                            'plan_digest': cc.plan_digest(seq),
                            'clip': self.asset('clip.mp4'), 'sample': self.asset('sample.json'),
                            'review': {'status': 'pass', 'method': 'direct_review',
                                       'finding': 'Synthetic recorded-observation fixture only.',
                                       'evidence': [self.asset('one.png'), self.asset('two.png')]}}
        self.data = {'reference': dict(self.asset('reference.mp4'), selection_basis='test fixture',
                                      preserve='test identity', feedback_scope='fixture only'),
                     'sequences': [seq], 'target': self.asset('clip.mp4'),
                     'final_samples': [self.asset('sample.json')]}

    def asset(self, name):
        return {'path': name, 'sha256': cc.digest(self.root / name)}

    def check(self, complete, finding=None):
        result = cc.evaluate(self.data, self.root, 'final')
        self.assertEqual(result['status'], 'evidence_complete' if complete else 'candidate')
        if finding:
            self.assertTrue(any(finding in x['finding'] for x in result['issues']), result)

    def test_complete(self):
        self.check(True)

    def test_replaced_input(self):
        (self.root / 'input.png').write_bytes(b'replacement')
        self.check(False, 'stale file hash')

    def test_updated_input_hash_old_preflight(self):
        (self.root / 'input.png').write_bytes(b'replacement')
        self.data['sequences'][0]['inputs'] = [self.asset('input.png')]
        self.check(False, 'no longer matches inputs')

    def test_old_mp4_samples(self):
        self.data['target'] = self.asset('new.mp4')
        self.check(False, 'old MP4')

    def test_missing_sample(self):
        del self.data['sequences'][0]['preflight']['sample']
        self.check(False, 'missing file')

    def test_model_assisted_not_direct(self):
        self.data['sequences'][0]['preflight']['review']['method'] = 'model_assisted'
        self.check(False, 'actual visual observation')

    def test_reasoned_single_state_hold(self):
        seq = self.data['sequences'][0]
        seq['states'] = seq['states'][:1]
        seq['hold_reason'] = 'Reaction pause lets the audience read the expression.'
        seq['preflight']['plan_digest'] = cc.plan_digest(seq)
        self.check(True)

    def test_changed_timing_old_preflight(self):
        self.data['sequences'][0]['states'][1]['at'] = 1.9
        self.check(False, 'action plan/timing')

    def test_one_frame_claims_two(self):
        p = self.root / 'sample.json'
        sample = json.loads(p.read_text())
        sample['files'] = sample['files'][:1]
        p.write_text(json.dumps(sample))
        self.data['sequences'][0]['preflight']['sample'] = self.asset('sample.json')
        self.data['final_samples'] = [self.asset('sample.json')]
        self.check(False, 'frame count/paths inconsistent')

    def test_empty_states_with_hold_reason(self):
        seq = self.data['sequences'][0]
        seq['states'] = []
        seq['hold_reason'] = 'Pause'
        seq['preflight']['plan_digest'] = cc.plan_digest(seq)
        self.check(False)


if __name__ == '__main__':
    unittest.main()
