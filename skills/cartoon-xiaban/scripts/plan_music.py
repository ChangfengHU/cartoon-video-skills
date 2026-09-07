#!/usr/bin/env python3
"""Rank caller-researched music metadata for scene intent; no search or listening."""
import argparse
import json
import math
from pathlib import Path

def number(value, name, low=0, high=1):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Invalid {name}")
    return value

def tags(value):
    if not isinstance(value,list) or not all(isinstance(x,str) and x for x in value):
        raise ValueError("tags must be nonempty strings in a list")
    return set(value)

def rank(plan, catalog, root):
    root = Path(root).resolve()
    if plan.get("schema_version") != 1 or catalog.get("schema_version") != 1:
        raise ValueError("Unsupported schema")
    platform = plan.get("platform")
    if not isinstance(platform,str) or not platform:
        raise ValueError("platform required")
    tracks, rejected, ids = [], [], set()
    for t in catalog.get("tracks",[]):
        ident = t.get("id")
        if not isinstance(ident,str) or not ident or ident in ids:
            raise ValueError("Missing or duplicate track id")
        ids.add(ident)
        reason = None
        rel = Path(t.get("file",""))
        if rel.is_absolute() or ".." in rel.parts or not str(rel) or str(rel) == ".":
            reason = "unsafe_or_missing_file"
        else:
            f = (root/rel).resolve()
            if not f.is_relative_to(root) or not f.is_file():
                reason = "missing_local_file"
        if t.get("rights_status") != "verified_for_project" or platform not in t.get("allowed_platforms",[]):
            reason = "rights_or_platform_unverified"
        if not all(isinstance(t.get(k),str) and t[k].startswith("https://") for k in ("source_url","rights_evidence_url")):
            reason = "missing_source_evidence"
        if plan.get("clean_frame",True) and t.get("attribution_placement") == "on_screen_required":
            reason = "requires_on_screen_credit"
        if t.get("instrumental") is not True:
            reason = "instrumental_not_confirmed"
        if reason:
            rejected.append({"id":ident,"reason":reason}); continue
        tags(t.get("tags",[]))
        number(t.get("energy"),"energy"); number(t.get("density"),"density")
        number(t.get("duration_seconds"),"duration_seconds",.01,86400)
        tracks.append(t)
    scenes=[]; seen=set(); previous_end=0
    for s in plan.get("scenes",[]):
        if not s.get("id") or s["id"] in seen:
            raise ValueError("Missing or duplicate scene id")
        seen.add(s["id"])
        start=number(s.get("start"),"start",0,86400)
        end=number(s.get("end"),"end",0,86400)
        if end <= start or start < previous_end:
            raise ValueError("Scene times must be ordered and nonoverlapping")
        previous_end=end
        if s.get("silence") is True:
            scenes.append({"scene":s["id"],"start":start,"end":end,"selection":None,"status":"intentional_silence","reason":s.get("reason","comic pause")});continue
        wanted=tags(s.get("tags",[])); energy=number(s.get("energy"),"energy")
        density=number(s.get("density"),"density")
        options=[]
        for t in tracks:
            if t["duration_seconds"] < end-start:
                continue
            overlap=len(wanted & tags(t.get("tags",[])))/max(1,len(wanted))
            score=round(60*overlap+25*(1-abs(energy-t["energy"]))+15*(1-abs(density-t["density"])),2)
            options.append({"id":t["id"],"score":score,"matched_tags":sorted(wanted & tags(t.get("tags",[]))),
                "file":t["file"],"attribution":t.get("attribution",""),"audition_status":t.get("audition_status","not_listened")})
        options.sort(key=lambda x:(-x["score"],x["id"]))
        scenes.append({"scene":s["id"],"start":start,"end":end,
            "selection":options[0]["id"] if options else None,
            "status":"metadata_candidate_needs_review" if options else "no_eligible_track",
            "ranked_candidates":options[:4]})
    if not scenes: raise ValueError("At least one scene required")
    return {"schema_version":1,"method":"caller supplied tags, energy and density; NOT audio analysis, search, or legal verification",
        "platform":platform,"scenes":scenes,"rejected":rejected,
        "next":"Agent reviews transitions, source offsets, rights evidence and auditions; then freeze cue sheet and mix."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--asset-root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=rank(json.loads(a.plan.read_text()),json.loads(a.catalog.read_text()),a.asset_root)
    # Exclusive creation preserves prior decisions.
    with a.output.open("x",encoding="utf-8") as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"written":str(a.output),"scenes":len(result["scenes"])}))
if __name__=="__main__": main()
