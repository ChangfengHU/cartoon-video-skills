// Immutable R2 facts. No Cloudflare administration, URL fetching, deletion or model calls.
export const MAX_FILE = 20_000_000;
export const KINDS = ['image', 'sfx', 'voice', 'bgm', 'reference'];
export class Rejected extends Error {
  constructor(message, status = 400) { super(message); this.status = status; }
}
export function assert(ok, message, status) { if (!ok) throw new Rejected(message, status); }
export const canonical = value => JSON.stringify(value, (_, v) => v && !Array.isArray(v) && typeof v === 'object' ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b))) : v);
export async function sha(value) {
  const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), x => x.toString(16).padStart(2, '0')).join('');
}
export function clean(value, depth = 0) {
  assert(depth < 20, 'Metadata too deeply nested');
  if (Array.isArray(value)) { assert(value.length <= 200, 'Metadata array too large'); value.forEach(v => clean(v, depth + 1)); }
  else if (value && typeof value === 'object') {
    for (const [k, v] of Object.entries(value)) {
      assert(!['apikey','apitoken','authorization','accesstoken','cookie','password','secret','globalkey','privatekey','token','tenant','owner','prefix'].includes(k.toLowerCase().replace(/[^a-z]/g, '')), 'Credential/ownership fields are forbidden');
      clean(v, depth + 1);
    }
  } else if (typeof value === 'string') {
    assert(value.length <= 16000, 'Metadata text too long');
    if (/^https?:\/\//i.test(value)) {
      const u = new URL(value);
      assert(!u.username && !u.password && ![...u.searchParams.keys()].some(k => /token|secret|key|signature|credential/i.test(k)), 'Credential-bearing source URLs forbidden');
    }
  }
}
function requireText(v, key) { assert(typeof v?.[key] === 'string' && v[key].trim().length > 0, `Missing ${key}`); }
function stringArray(value) { return Array.isArray(value) && value.length > 0 && value.every(x => typeof x === 'string' && x.trim().length > 0); }
function validDate(value) { return typeof value === 'string' && /^\d{4}-\d\d-\d\d/.test(value) && Number.isFinite(Date.parse(value)); }
export function validateCard(card, binary = false) {
  clean(card);
  assert(new TextEncoder().encode(canonical(card)).length <= 60000, 'Card too large');
  assert(card?.schema_version === 1 && KINDS.includes(card.kind), 'Invalid card schema/kind');
  for (const k of ['title','source_type','source_url','review_status']) requireText(card, k);
  assert(Array.isArray(card.use_cases) && card.use_cases.length > 0 && card.use_cases.every(x => typeof x === 'string'), 'use_cases required');
  assert(Array.isArray(card.tags ?? []) && (card.tags ?? []).every(x => typeof x === 'string'), 'Invalid tags');
  for (const k of ['status','scope','evidence']) requireText(card.license, k);
  assert(!card.personal_reference && card.voice_identity !== 'user_clone', 'Personal references and cloned personal voices excluded');
  for (const key of ['id','object','created_at']) assert(!(key in card), 'Server-owned card field');
  if (binary) {
    assert(card.license.archive_allowed === true && ['verified_for_archive','user_authorized_generated'].includes(card.license.status), 'Binary archive requires documented archive rights');
    assert(card.kind !== 'voice' || card.voice_identity === 'provider_preset', 'Only provider-preset voice output may be archived');
  }
}
function idParts(id) {
  assert(typeof id === 'string' && /^([a-f0-9]{64}|[a-f0-9]{32}-[a-f0-9]{64})$/.test(id), 'Invalid asset/record ID');
  return {legacy: id.length === 97, hash: id.slice(-64)};
}
export async function authenticate(request, env, permission = 'read') {
  const auth = request.headers.get('Authorization') || '';
  assert(auth.startsWith('Bearer ') && auth.length < 1024, 'Authentication required', 401);
  const hash = await sha(auth.slice(7));
  let clients; try { clients = JSON.parse(env.AUTH_CLIENTS); } catch { throw new Rejected('Service authentication unavailable', 503); }
  const p = clients.find(x => x.token_sha256 === hash);
  assert(p, 'Invalid service credential', 401);
  assert(p.permissions?.includes(permission), 'Insufficient scope', 403);
  assert(/^[a-z0-9-]+\/v2$/.test(p.prefix) && (!p.legacy_prefix || /^[a-z0-9-]+\/v1$/.test(p.legacy_prefix)), 'Invalid server scope', 503);
  return p;
}
export class Library {
  constructor(bucket, principal, origin) { this.bucket = bucket; this.p = principal; this.origin = origin; }
  writeAllowed() { assert(this.p.permissions.includes('write'), 'Write scope required', 403); }
  async immutable(key, bytes) {
    const hash = await sha(bytes);
    const put = await this.bucket.put(key, bytes, {onlyIf: new Headers({'If-None-Match':'*'}), sha256: hash, httpMetadata:{contentType:'application/octet-stream'}});
    if (!put) {
      const previous = await this.bucket.get(key);
      assert(previous && await sha(await previous.arrayBuffer()) === hash, 'Immutable object conflict', 409);
    }
    return {deduplicated: !put};
  }
  async append(group, data) {
    const bytes = canonical(data), id = await sha(bytes);
    const result = await this.immutable(`${this.p.prefix}/${group}/${id}.json`, bytes);
    return {id, ...result};
  }
  async load(group, id) {
    const part = idParts(id), prefix = part.legacy ? this.p.legacy_prefix : this.p.prefix;
    assert(prefix, 'Record unavailable in this library', 404);
    const obj = await this.bucket.get(`${prefix}/${group}/${id}.json`);
    assert(obj, 'Record not found', 404);
    const raw = await obj.text();
    assert(await sha(raw) === part.hash, 'Record integrity failure', 409);
    const value = JSON.parse(raw);
    clean(value);
    return {id, ...value};
  }
  async page(group, cursor, limit = 40) {
    limit = Math.max(1, Math.min(50, limit));
    let state = {phase: this.p.legacy_prefix ? 0 : 1, cursor: undefined};
    if (cursor) {
      try { state = JSON.parse(atob(cursor)); } catch { throw new Rejected('Invalid cursor'); }
      assert([0,1].includes(state.phase) && (!state.cursor || typeof state.cursor === 'string'), 'Invalid cursor');
    }
    const prefix = state.phase === 0 ? this.p.legacy_prefix : this.p.prefix;
    assert(prefix, 'Invalid cursor scope');
    const page = await this.bucket.list({prefix:`${prefix}/${group}/`, limit, cursor:state.cursor});
    let next = page.truncated ? {phase:state.phase, cursor:page.cursor} : state.phase === 0 ? {phase:1} : null;
    const rows = await Promise.all(page.objects.map(async obj => {
      const id = obj.key.split('/').pop().replace(/\.json$/, '');
      return this.load(group, id);
    }));
    return {rows, next_cursor: next ? btoa(JSON.stringify(next)) : null};
  }
  async search({query = '', kind, cursor, limit = 40} = {}) {
    const {rows, next_cursor} = await this.page('records', cursor, limit);
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    return {assets: rows.filter(r => (!kind || kind === r.kind) && words.every(w => JSON.stringify([r.title,r.tags,r.use_cases]).toLowerCase().includes(w))), next_cursor, scanned: rows.length, note:'Page-scoped keyword search; follow next_cursor even if this page has no matches. Registration is not individual approval.'};
  }
  async get(id) {
    const asset = await this.load('records', id);
    const feedback = [];
    // Bounded, paginated feedback is also independently available through asset_feedback_list.
    const prefix = `${this.p.prefix}/feedback/${id}/`;
    const notes = await this.bucket.list({prefix, limit:50});
    for (const obj of notes.objects) {
      const raw = await (await this.bucket.get(obj.key)).text();
      assert(await sha(raw) === obj.key.split('/').pop().replace('.json',''), 'Feedback integrity failure', 409);
      feedback.push(JSON.parse(raw));
    }
    return {asset, feedback, feedback_truncated:notes.truncated, download:asset.object ? {url:`${this.origin}/v1/assets/${id}/file`, authentication:'same service Bearer token, never put it in URL', sha256:asset.object.sha256, size:asset.object.size} : null};
  }
  async register(card, file) {
    this.writeAllowed(); validateCard(card, !!file);
    if (card.supersedes) await this.load('records', card.supersedes);
    let object = null;
    if (file) {
      assert(file.bytes.byteLength > 0 && file.bytes.byteLength <= MAX_FILE, 'File limit is 20 MB');
      assert(/^\.(png|jpg|jpeg|webp|wav|mp3|m4a|ogg|mp4|webm|flac)$/.test(file.extension), 'Unsupported media extension');
      const checksum = await sha(file.bytes), key = `${this.p.prefix}/blobs/${checksum}${file.extension}`;
      await this.immutable(key, file.bytes);
      object = {key, sha256:checksum, size:file.bytes.byteLength, extension:file.extension};
    }
    // Content-derived ID makes retry/concurrent identical registration idempotent.
    // R2 object upload time supplies audit time without perturbing identity.
    const record = {...card, object};
    return {...await this.append('records', record), record};
  }
  async feedback(value) {
    this.writeAllowed(); clean(value);
    for (const k of ['asset_id','project','outcome','reason','reviewer','observed_at']) requireText(value, k);
    assert(['used','rejected','user_approved','user_disliked','technical_failure'].includes(value.outcome), 'Invalid feedback outcome');
    assert(validDate(value.observed_at), 'observed_at must be a date');
    await this.load('records', value.asset_id);
    return this.append(`feedback/${value.asset_id}`, value);
  }
  async feedbackList(id, cursor) {
    await this.load('records', id);
    // v1 feedback remains immutable and queryable, not silently discarded.
    let part;
    try { part = cursor ? JSON.parse(atob(cursor)) : {phase:this.p.legacy_prefix ? 0 : 1}; }
    catch { throw new Rejected('Invalid feedback cursor'); }
    assert(part && [0,1].includes(part.phase) && (part.phase !== 0 || this.p.legacy_prefix) && (!part.cursor || typeof part.cursor === 'string'), 'Invalid feedback cursor');
    const prefix = part.phase === 0 ? `${this.p.legacy_prefix}/feedback/` : `${this.p.prefix}/feedback/${id}/`;
    const page = await this.bucket.list({prefix, cursor:part.cursor, limit:50});
    const rows = [];
    for (const obj of page.objects) {
      const raw = await (await this.bucket.get(obj.key)).text();
      assert(await sha(raw) === obj.key.split('/').pop().replace('.json','').slice(-64), 'Feedback integrity failure', 409);
      const v = JSON.parse(raw); if(v.asset_id === id) rows.push(v);
    }
    const next = page.truncated ? {phase:part.phase,cursor:page.cursor} : part.phase === 0 ? {phase:1} : null;
    return {feedback:rows,next_cursor:next ? btoa(JSON.stringify(next)) : null};
  }
  async freeze(selection) {
    this.writeAllowed(); clean(selection);
    for (const k of ['project','story_intent','platform']) requireText(selection, k);
    assert(Array.isArray(selection.selected) && selection.selected.length > 0 && selection.selected.length <= 30, 'Select 1–30 assets');
    const ids = new Set(), records = [];
    for (const item of selection.selected) {
      assert(!ids.has(item.asset_id), 'Duplicate selection'); ids.add(item.asset_id);
      const record = await this.load('records', item.asset_id), review = item.project_review;
      requireText(item,'reason');
      assert(review?.status === 'verified_for_project' && stringArray(review.allowed_platforms) && review.allowed_platforms.includes(selection.platform) && validDate(review.checked_at), 'Fresh project-specific rights review required');
      requireText(review,'evidence');
      records.push({...record, selection:item});
    }
    if (records.some(r => r.kind === 'bgm')) {
      const r = selection.new_music_research;
      assert(r?.performed === true && validDate(r.checked_at) && stringArray(r.queries) && stringArray(r.source_urls) && r.source_urls.every(u => { try { return ['https:','http:'].includes(new URL(u).protocol); } catch { return false; } }) && Array.isArray(r.new_candidates), 'BGM requires recorded NEW music research, even when reusing');
      if (!r.new_candidates.length) requireText(r,'no_new_candidate_reason');
    }
    const snapshot = {schema_version:2, selection, records, note:'Immutable selection; download and verify files before rendering. Not a legal or listening judgment.'};
    return {...await this.append('projects', snapshot), snapshot};
  }
  async file(id) {
    const {object} = await this.load('records', id);
    assert(object, 'Metadata-only record has no file', 404);
    assert(/^[a-f0-9]{64}$/.test(object.sha256) && [this.p.prefix,this.p.legacy_prefix].filter(Boolean).some(p => object.key.startsWith(p + '/blobs/')) && !object.key.includes('..'), 'Invalid file reference', 409);
    const data = await this.bucket.get(object.key);
    assert(data && data.size === object.size, 'File missing or size mismatch', 409);
    return new Response(data.body, {headers:{'Content-Type':'application/octet-stream','Content-Disposition':`attachment; filename="${id}${object.extension}"`,'Content-Length':String(data.size),'X-Content-SHA256':object.sha256,'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
  }
}
