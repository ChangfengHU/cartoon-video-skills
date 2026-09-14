# Studio 0.7.0: continuity evidence

Characters can now preserve an explicit reference scope, describe action intent/contact/end state, preview difficult sequences and invalidate stale evidence after changed assets, action timing or final encodes. The workflow reuses production packs and state tracking; it does not create another character registry.

`studio-quality/scripts/sample_motion.py` samples actual MP4 frames. `continuity_check.py` verifies file hashes, plan hashes, sample provenance and recorded observations. An evidence-complete result is not an aesthetic pass or publishing authorization. Visual, emotional and listening judgments remain separately recorded, including pending checks.

Validation: 92 repository tests pass; independent actual-MP4 forward test covered 10 scenarios and found three gaps, which were repaired and retested. Research and limits are under docs/research/2026-09-14-continuity-*.md. No third-party implementation was copied, new engine installed, new MCP added or automatic hook enabled.

Package: 29 skills, 8 MCP declarations, version 0.7.0. Public package contains generic workflow and fixtures; private character assets, voices and user feedback remain in projects. Client installation, Git publication and Fleet catalog deployment are separate operations.
