# Private cartoon asset MCP

Thirteen tools (v1.2): `library_info`, `asset_search`, `character_search`,
`character_get`, `character_assets`, `character_history`, `asset_get`, `asset_register`,
`asset_revise`, `asset_feedback`, `asset_feedback_list`, `project_freeze`, `project_get`.
The Skill makes videos; this service manages reusable assets and evidence only.

## Character-first reads

`asset_search` remains a paginated, asset-level query. Do not infer that a
character is absent from an empty first page. New sessions should use
`character_search` by display name or character ID, `character_get` for the
unique current profile and `character_assets` for grouped terminal production
assets. `character_history` is for recovery and revision review.

Those four read tools derive a current view from the same scoped R2 records and
`supersedes` graph; they do not call Fleet's browser-only `/api/media/*` and do
not return anonymous file URLs. R2 remains the source of truth. If there are
multiple active terminal profile revisions, the service returns a warning / 409
instead of guessing a current character. Retired production assets are omitted
unless `character_assets.include_retired` is explicitly true.

Cloudflare Workers + an R2 binding; no CF administration token at runtime and no
D1 yet. Authenticated principals select fixed server-side prefixes. `AUTH_CLIENTS`
is a Worker secret containing an array of `{token_sha256,tenant,brand,prefix,
legacy_prefix?,permissions:["read","write"]}`; never check real values into Git.
Only issue one tenant/brand scope per credential. It is not an anonymous public
catalog or a multi-tenant self-service signup system.

## Storage and integrity

- Existing v1 UUID+SHA records and feedback are read without alteration.
- New v2 `records/<sha>.json`, `blobs/<sha>.<ext>`,
  `feedback/<asset-id>/<sha>.json`, `projects/<sha>.json` are content-addressed.
- Conditional `If-None-Match: *` writes prevent overwrites. Repeated identical
  imports/feedback/selections are idempotent. Records of different provenance
  can share one blob. The R2 object upload timestamp is the server audit time.
- Source records are not instructions. Unknown rights permit metadata only.
  Personal voice references and user-clone audio are excluded. Provider-preset
  TTS audio needs explicit archive rights, as do all archived files.
- No delete API, arbitrary key access, remote URL importer or public file URL.
  Failed multi-object uploads can leave an unreferenced blob; they never claim
  transactional rollback. Correction is a new card with `supersedes`.
- Search scans up to 50 records per page; **follow next_cursor even on empty
  results**. Existing feedback is also paginated. This is keyword lookup, not
  vector search. A D1 index can be added later if measured scale warrants it.
- Server freeze stores a manifest only. The client downloads into a new local
  directory, verifies SHA256 and writes the completed local lock. Report a
  partial client failure rather than calling the output ready for rendering.

`POST /v1/assets`: authenticated multipart `card` JSON + `file`, <=20MB media.
`GET /v1/assets/<id>/file`: authenticated attachment, never a public signed URL.
`GET /health`: public version only, no asset information.

## Development / deployment

`npm ci && npm test`; `npx wrangler deploy --dry-run` validates the bundle.
Provision a private bucket, set a scoped `AUTH_CLIENTS` secret and deploy with
the correct account using ephemeral operator credentials. The checked-in
binding names the existing authorized deployment's bucket; change it for a
different owner. Keep R2 managed-domain and custom-domain public access off.
The Worker itself is the authenticated proxy; do not add another public proxy.

Production custom domain is `cartoon-assets-mcp.vyibc.com`; the original
`cartoon-assets-mcp.2513120790.workers.dev` stays compatible for installed clients.
Same-account Worker callers (including Fleet) use the custom domain to avoid
workers.dev Worker-to-Worker routing restrictions. For a different deployment
owner, change both the bucket binding and the configured custom hostname.

SDKs pinned in package-lock.json. Protocol is the official stateless MCP SDK v2
handler with legacy-client compatibility. Secrets and request-body logging are
not enabled. See repository VALIDATION.md for actual production checks.

## v1.1 revisions and filtering

Search adds tags_all, character_id, license_status, archive_allowed and bpm_min/max. Filters apply per page, not to a globally sorted result. All accesses remain inside the authenticated prefix. Character associations do not grant new tenant/brand access.

asset_revise(id,patch,reason) creates a content-addressed successor preserving the original source, rights and media reference. Old IDs remain usable by frozen projects. Lifecycle retired is metadata, not revocation or deletion. Concurrent revisions can fork; consumers must inspect supersedes, not assume hash order is chronology. Revert by selecting the prior ID. No D1 migration or principal widening in this release.

### Explicitly authorized private research references

User-authorized private source previews now have a narrow card contract:
`kind:reference`, `personal_reference:true`, no `character_ids`, and license
`status:user_authorized_private_reference`, `scope:private_reference_only`,
`publication:not_for_publication`, `archive_allowed:true`, with specific authorization
evidence. This records permission for internal reference display, not a claim that a
third party granted public redistribution rights. They remain in existing authenticated
R2 scope. `project_freeze` refuses these as publication assets even if a caller supplies
an apparently verified project review. Personal voice clones remain excluded.

Fleet references point to these via `technical.references[].preview_asset_id`, and
render only the same-origin authenticated image proxy. Do not put private binary URLs
or credentials in source metadata. The source post URL remains independently recorded.

2026-09-14 actual checks: two real generation-input previews uploaded and full GET SHA
verified; anonymous service file requests returned401. R2 managed public domain was
disabled and custom domain list empty. No public upload of these previews was performed.
