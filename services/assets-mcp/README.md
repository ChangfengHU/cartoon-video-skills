# Private cartoon asset MCP

Eight tools: `library_info`, `asset_search`, `asset_get`, `asset_register`,
`asset_feedback`, `asset_feedback_list`, `project_freeze`, `project_get`.
The Skill makes videos; this service manages reusable assets and evidence only.

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

SDKs pinned in package-lock.json. Protocol is the official stateless MCP SDK v2
handler with legacy-client compatibility. Secrets and request-body logging are
not enabled. See repository VALIDATION.md for actual production checks.
