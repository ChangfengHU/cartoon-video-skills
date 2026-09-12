import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('speech', Path(__file__).resolve().parents[1] / 'skills/studio-quality/scripts/speech_check.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SpeechCheck(unittest.TestCase):
    def test_missing_word_is_not_hidden_by_high_similarity(self):
        _, issues = m.compare([{'index': 3, 'text': '剧情刚好下饭。优惠券也不用来回找。'}], '刚好下饭优惠券也不用来回找')
        self.assertEqual(issues[0]['expected'], '剧情')
        self.assertEqual(issues[0]['segment_indices'], [3])

    def test_repeated_words_and_trailing_extra(self):
        _, issues = m.compare([{'index': 0, 'text': '工作翻倍'}, {'index': 1, 'text': '工资翻倍'}], '工作翻倍工资翻倍谢谢')
        self.assertEqual(issues[0]['observed'], '谢谢')
        self.assertEqual(issues[0]['segment_indices'], [1])

    def test_punctuation_is_ignored_but_homophones_are_not(self):
        self.assertFalse(m.compare([{'index': 0, 'text': '你好，ＡＩ！'}], '你好ai')[1])
        self.assertTrue(m.compare([{'index': 0, 'text': '钱包'}], '请包')[1])

    def test_hash_change_invalidates_previous_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'timeline').write_text(json.dumps({'segments': [{'index': 0, 'text': '你好'}]}))
            (p/'audio').write_bytes(b'old audio')
            (p/'asr').write_text(json.dumps({'audio_sha256': m.digest(b'old audio'), 'stage': 'final', 'text': '你好'}))
            r = m.check(p/'timeline', p/'audio', p/'asr')
            self.assertEqual(r['content_gate'], 'pass')
            self.assertFalse(r['quality_approved'])
            (p/'audio').write_bytes(b'new audio')
            with self.assertRaises(ValueError):
                m.check(p/'timeline', p/'audio', p/'asr')

    def test_empty_and_unbound_evidence_are_blocked(self):
        with self.assertRaises(ValueError):
            m.compare([{'index': 0, 'text': '台词'}], '')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'audio').write_bytes(b'audio')
            (p/'asr').write_text('{"text":"台词"}')
            with self.assertRaises(ValueError):
                m.check(p/'missing-timeline', p/'audio', p/'asr')

    def test_independent_asr_requires_complete_matching_speech(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p/'timeline').write_text(json.dumps({'segments': [{'index': 0, 'text': '剧情刚好下饭'}]}))
            (p/'audio').write_bytes(b'current audio')
            ah = m.digest((p/'audio').read_bytes())
            (p/'asr').write_text(json.dumps({'audio_sha256': ah, 'stage': 'source', 'text': '刚好下饭'}))
            r = m.check(p/'timeline', p/'audio', p/'asr')
            (p/'clip').write_bytes(b'current excerpt')
            (p/'other-asr').write_text(json.dumps({'text': '剧情刚好下饭'}))
            alt = {'parent_audio_sha256': ah, 'segment_indices': [0], 'clip': 'clip', 'clip_sha256': m.digest((p/'clip').read_bytes()), 'raw_asr': 'other-asr', 'raw_asr_sha256': m.digest((p/'other-asr').read_bytes())}
            (p/'alt').write_text(json.dumps(alt))
            review = {'audio_sha256': ah, 'script_sha256': r['script_sha256'], 'resolutions': [{'id': r['issues'][0]['id'], 'basis': 'independent_asr', 'reason': 'Independent complete segment recognition', 'evidence': 'alt', 'evidence_sha256': m.digest((p/'alt').read_bytes())}]}
            (p/'review').write_text(json.dumps(review))
            self.assertEqual(m.check(p/'timeline', p/'audio', p/'asr', p/'review')['content_gate'], 'pass')
            (p/'other-asr').write_text(json.dumps({'text': '刚好下饭'}))
            alt['raw_asr_sha256'] = m.digest((p/'other-asr').read_bytes())
            (p/'alt').write_text(json.dumps(alt))
            review['resolutions'][0]['evidence_sha256'] = m.digest((p/'alt').read_bytes())
            (p/'review').write_text(json.dumps(review))
            with self.assertRaises(ValueError):
                m.check(p/'timeline', p/'audio', p/'asr', p/'review')


if __name__ == '__main__':
    unittest.main()
