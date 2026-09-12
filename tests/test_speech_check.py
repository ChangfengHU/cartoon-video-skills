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


if __name__ == '__main__':
    unittest.main()
