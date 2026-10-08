# Reusable real-character material bundles

Research was independently source-inspected; neither framework was installed or
used to generate the acceptance media. The existing private R2 library remains
authoritative. No third-party source code was copied.

## Pinned comparisons

- [HKUDS/ViMax](https://github.com/HKUDS/ViMax/tree/fd4b72e7731be6e5f88486206d25ea59849b0285)
  (MIT; inspected revision dated 2026-09-30): `interfaces/character.py` separates
  static face/body features from costume/accessory features. Portrait generation
  and reference selection maintain multi-view references. Adapt that separation,
  not its Python 3.12/LangChain/MoviePy/provider stack. Text locks and a file-exists
  cache do not prove visual consistency or cache validity.
- [aws-samples/sample-storyboardplatform](https://github.com/aws-samples/sample-storyboardplatform/tree/5ed0b0f93068c53996daddb6c040370bf286966c)
  (MIT-0; inspected revision dated 2026-09-12): asset selection/keeping and board
  references inform explicit reusable material selection. Do not adopt mutable
  array positions as identity versions, automatic extraction as user approval, or
  silently truncated references. Its AWS/Cognito/AppSync/DynamoDB/S3/GPU stack is
  unnecessary for this service.

## Implemented boundaries

- Extend the existing library with representation, production role and a pinned
  `profile_asset_id`; do not create a separate editable character database.
- Preserve prior tools, scope, prefix and private download authentication. New
  tools are `character_materials` and `character_register_material`.
- Only the canonical identity reference carries face/body locks and its explicit
  approval evidence. New poses, views, clothing, voices and videos are separately
  reviewed. A material inventory is not a full audiovisual quality receipt.
- Metadata-only review/voice revisions retain compatible attachments when the
  semantic profile version, identity locks and identity file hash remain equal.
  A changed identity does not inherit previous materials or approval.
- Generation provenance, source rights, byte hashes and task/output references
  remain private material facts; portable plugins contain only code and rules.

## Verification scope

Library unit tests cover representation filtering, immutable registration,
scope isolation, material/version conflicts and metadata-only revision recovery.
An isolated Miniflare test exercises the compiled MCP with private fixture R2,
actual tool discovery, registration, readback and anonymous rejection. Production
acceptance additionally verifies imported bytes by authenticated full R2 readback.
These tests do not establish exact pose geometry, voice preference or final-film
quality; those require per-production inspection and user review.
