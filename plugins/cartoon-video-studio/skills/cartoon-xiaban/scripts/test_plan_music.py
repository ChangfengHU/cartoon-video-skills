import unittest
import tempfile
from pathlib import Path
from plan_music import rank

class MusicPlanTests(unittest.TestCase):
    def test_scene_intent_switches_track_and_respects_silence(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,"one.wav").touch()
            def track(id,tags,energy,density):
                return dict(id=id,file="one.wav",tags=tags,energy=energy,density=density,duration_seconds=100,
                    source_url="https://example.org/source",rights_evidence_url="https://example.org/license",
                    rights_status="verified_for_project",allowed_platforms=["douyin"],instrumental=True,
                    attribution_placement="description")
            cat={"schema_version":1,"tracks":[track("bright",["proud"],.8,.5),track("sneaky",["guilty"],.2,.1)]}
            p={"schema_version":1,"platform":"douyin","scenes":[
                dict(id="a",start=0,end=10,tags=["proud"],energy=.8,density=.5),
                dict(id="b",start=10,end=20,tags=["guilty"],energy=.2,density=.1),
                dict(id="c",start=20,end=21,silence=True)]}
            r=rank(p,cat,d)
            self.assertEqual([s["selection"] for s in r["scenes"]],["bright","sneaky",None])
            cat["tracks"][0]["rights_status"]="unknown"
            cat["tracks"][1]["attribution_placement"]="on_screen_required"
            r=rank(p,cat,d)
            self.assertEqual(r["scenes"][0]["status"],"no_eligible_track")
            self.assertEqual(len(r["rejected"]),2)
    def test_bad_timeline_rejected(self):
        p={"schema_version":1,"platform":"douyin","scenes":[dict(id="bad",start=4,end=3,silence=True)]}
        with self.assertRaises(ValueError):rank(p,{"schema_version":1,"tracks":[]},".")
    def test_source_path_does_not_escape(self):
        with tempfile.TemporaryDirectory() as d:
            t=dict(id="bad",file="../secret.wav",source_url="https://example.org/s",
                rights_evidence_url="https://example.org/l",rights_status="verified_for_project",
                allowed_platforms=["douyin"],instrumental=True)
            p={"schema_version":1,"platform":"douyin","scenes":[dict(id="a",start=0,end=1,tags=[],energy=.1,density=.1)]}
            r=rank(p,{"schema_version":1,"tracks":[t]},d)
            self.assertEqual(r["rejected"][0]["reason"],"unsafe_or_missing_file")
if __name__=="__main__":unittest.main()
