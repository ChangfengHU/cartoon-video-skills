// Immutable R2 facts. No Cloudflare administration, URL fetching, deletion or model calls.
export const MAX_FILE = 20_000_000;
export const KINDS = ['image', 'sfx', 'voice', 'bgm', 'reference', 'video'];
export const MATERIAL_CATEGORIES = ['identity_reference','turnaround','expressions','actions','wardrobe','scenes','voices','sfx','bgm','videos','other'];
export function representationOf(record) {
  const t = record?.technical || {}, p = t.character_profile || {};
  const value = t.representation || p.representation;
  if (['photorealistic_virtual','photorealistic','live_action','realistic'].includes(value)) return 'realistic';
  if (value === 'cartoon') return 'cartoon';
  const style = String(p.style || t.style || '');
  if (/卡通|动漫|动画|手绘|水彩|黏土|cartoon|illustration|anime|clay|watercolor/i.test(style)) return 'cartoon';
  if (/写实|真人|photoreal|live.action/i.test(style)) return 'realistic';
  return 'unclassified';
}
function materialCategory(record) {
  const role = record.technical?.asset_kind || '';
  if (record.kind === 'video') return 'videos';
  if (/turnaround|三视图/.test(role)) return 'turnaround';
  if (/wardrobe|costume|服装/.test(role)) return 'wardrobe';
  return assetCategory(record);
}
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
const CHARACTER_CATEGORIES = ['identity_reference','expressions','actions','scenes','voices','sfx','bgm','other'];
function lifecycle(record) { return record.lifecycle === 'retired' ? 'retired' : 'active'; }
function assetCategory(record) {
  const role = String(record.technical?.asset_kind || record.technical?.asset_type || record.technical?.role || '').toLowerCase();
  if (role.includes('expression')) return 'expressions';
  if (role.includes('action') || role.includes('pose') || role.includes('motion')) return 'actions';
  if (role.includes('scene') || role.includes('background')) return 'scenes';
  if (role.includes('identity') || role.includes('reference')) return 'identity_reference';
  // Early cards predate asset_kind. A profile card without a more specific
  // production role is the character identity reference; copied profile
  // metadata on action/expression revisions is not.
  if (record.technical?.character_profile && !role) return 'identity_reference';
  if (record.kind === 'voice') return 'voices';
  if (record.kind === 'sfx') return 'sfx';
  if (record.kind === 'bgm') return 'bgm';
  return 'other';
}
function assetSummary(record) {
  const technical = record.technical || {};
  // character_get is the one authoritative, full profile payload.  A grouped
  // asset list must stay small enough for an agent to choose assets rather than
  // repeat every persona and script prompt once per image.
  const detail = Object.fromEntries(Object.entries({
    asset_kind:technical.asset_kind,
    asset_type:technical.asset_type,
    role:technical.role,
    revision:technical.revision,
    scene:technical.scene,
    duration_seconds:technical.duration_seconds,
    voice_id:technical.voice_id,
    provider:technical.provider,
    model:technical.model
  }).filter(([, value]) => value !== undefined));
  return {id:record.id,title:record.title,kind:record.kind,category:assetCategory(record),lifecycle:lifecycle(record),supersedes:record.supersedes || null,tags:record.tags || [],use_cases:record.use_cases || [],review_status:record.review_status,technical:detail};
}
export function validateCard(card, binary = false) {
  clean(card);
  assert(new TextEncoder().encode(canonical(card)).length <= 60000, 'Card too large');
  assert(card?.schema_version === 1 && KINDS.includes(card.kind), 'Invalid card schema/kind');
  for (const k of ['title','source_type','source_url','review_status']) requireText(card, k);
  assert(Array.isArray(card.use_cases) && card.use_cases.length > 0 && card.use_cases.every(x => typeof x === 'string'), 'use_cases required');
  assert(Array.isArray(card.tags ?? []) && (card.tags ?? []).every(x => typeof x === 'string'), 'Invalid tags');
  for (const k of ['status','scope','evidence']) requireText(card.license, k);
  const privateReference = card.license.status === 'user_authorized_private_reference';
  if(privateReference)assert(card.kind === 'reference' && card.personal_reference === true && card.license.scope === 'private_reference_only' && card.license.publication === 'not_for_publication' && card.license.archive_allowed === true && !(card.character_ids?.length), 'Private references require explicit restricted scope and no character card identity');
  assert((!card.personal_reference || privateReference) && card.voice_identity !== 'user_clone', 'Personal references require restricted authorization; cloned personal voices excluded');
  for (const key of ['id','object','created_at']) assert(!(key in card), 'Server-owned card field');
  if (binary) {
    assert(card.license.archive_allowed === true && ['verified_for_archive','user_authorized_generated','user_authorized_private_reference'].includes(card.license.status), 'Binary archive requires documented archive rights');
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
  async allRecords() {
    // Character views deliberately do the pagination inside the service.  The
    // append-only R2 facts stay authoritative; this is a bounded, rebuildable
    // projection rather than a second editable character database.
    const rows = [];
    let cursor;
    for (let pages = 0; pages < 100; pages += 1) {
      const page = await this.page('records', cursor, 50);
      rows.push(...page.rows);
      if (!page.next_cursor) return rows;
      cursor = page.next_cursor;
    }
    throw new Rejected('Character catalog exceeds bounded rebuild capacity', 503);
  }
  async characterCatalog() {
    const records = await this.allRecords();
    const successorIds = new Set(records.map(record => record.supersedes).filter(Boolean));
    const groups = new Map();
    for (const record of records) {
      const profile = record.technical?.character_profile;
      if (!profile || typeof profile.id !== 'string' || !profile.id.trim() || assetCategory(record) !== 'identity_reference') continue;
      const id = profile.id.trim();
      const group = groups.get(id) || [];
      group.push(record);
      groups.set(id, group);
    }
    const characters = [];
    for (const [character_id, profiles] of groups) {
      const leaves = profiles.filter(record => !successorIds.has(record.id));
      const activeLeaves = leaves.filter(record => lifecycle(record) === 'active');
      const current = activeLeaves.length === 1 ? activeLeaves[0] : null;
      const warnings = [];
      if (activeLeaves.length > 1) warnings.push('Multiple active profile revisions have no successor; choose a revision explicitly before production.');
      if (activeLeaves.length === 0 && leaves.length) warnings.push('No active current profile revision. Use character_history for retired revisions.');
      if (!leaves.length) warnings.push('No terminal profile revision could be resolved.');
      characters.push({character_id,profiles,leaves,current,warnings});
    }
    return {records,characters};
  }
  async characterSearch({query = '', limit = 20, representation} = {}) {
    assert(typeof query === 'string' && query.length <= 300, 'Invalid character query');
    assert(Number.isInteger(limit) && limit >= 1 && limit <= 50, 'Invalid character limit');
    assert(representation === undefined || ['realistic','cartoon','unclassified'].includes(representation), 'Invalid representation');
    const {characters} = await this.characterCatalog();
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const results = characters.map(entry => {
      const profile = entry.current?.technical?.character_profile || entry.leaves[0]?.technical?.character_profile || {};
      const version = profile.version ?? profile.profile_version ?? null;
      return {character_id:entry.character_id,name:profile.name || entry.current?.title || entry.leaves[0]?.title || entry.character_id,profile_asset_id:entry.current?.id || null,profile_version:version,representation:representationOf(entry.current || entry.leaves[0]),studio_id:entry.current?.technical?.studio_id || null,lifecycle:entry.current ? 'active' : 'unresolved',status:entry.current?.technical?.preproduction?.status_label || null,warnings:entry.warnings};
    }).filter(result => (!representation || result.representation === representation) && words.every(word => JSON.stringify([result.character_id,result.name,result.status]).toLowerCase().includes(word)));
    return {characters:results.slice(0,limit),total:results.length,note:'Character views resolve current profiles across the private R2 catalog. Use character_get by character_id; asset_search remains paginated discovery for individual assets.'};
  }
  async characterGet(characterId) {
    assert(typeof characterId === 'string' && characterId.trim().length > 0 && characterId.length <= 200, 'Invalid character ID');
    const {characters,records} = await this.characterCatalog();
    const entry = characters.find(character => character.character_id === characterId);
    assert(entry, 'Character not found', 404);
    assert(entry.current, entry.warnings[0] || 'Current character profile cannot be resolved', 409);
    const profile = entry.current.technical?.character_profile || {};
    const linkedSceneIds = Object.values(entry.current.technical?.scene_assets || {}).filter(value => typeof value === 'string');
    const selectedVoiceId = entry.current.technical?.voice_recommendation?.voice_id || null;
    const selectedVoice = selectedVoiceId ? records.find(record => record.kind === 'voice' && record.technical?.voice_id === selectedVoiceId && lifecycle(record) === 'active') : null;
    return {character_id:entry.character_id,profile_asset_id:entry.current.id,profile_version:profile.version ?? profile.profile_version ?? null,lifecycle:lifecycle(entry.current),profile,voice_recommendation:entry.current.technical?.voice_recommendation || null,selected_voice_asset_id:selectedVoice?.id || null,scene_asset_ids:linkedSceneIds,preproduction:entry.current.technical?.preproduction || null,warnings:entry.warnings,note:'This is the current private character configuration. Retrieve grouped production media with character_assets and authenticated file access through asset_get.'};
  }
  async characterAssets({character_id, categories, include_retired = false} = {}) {
    assert(typeof character_id === 'string' && character_id.trim().length > 0 && character_id.length <= 200, 'Invalid character ID');
    assert(categories === undefined || (Array.isArray(categories) && categories.length <= CHARACTER_CATEGORIES.length && categories.every(category => CHARACTER_CATEGORIES.includes(category))), 'Invalid character asset categories');
    assert(typeof include_retired === 'boolean', 'Invalid include_retired');
    const {characters,records} = await this.characterCatalog();
    const entry = characters.find(character => character.character_id === character_id);
    assert(entry, 'Character not found', 404);
    assert(entry.current, entry.warnings[0] || 'Current character profile cannot be resolved', 409);
    const successors = new Set(records.map(record => record.supersedes).filter(Boolean));
    const matching = records.filter(record => (record.character_ids || []).includes(character_id));
    const terminal = matching.filter(record => !successors.has(record.id));
    const selected = terminal.filter(record => (include_retired || lifecycle(record) !== 'retired') && (!categories || categories.includes(assetCategory(record))));
    const grouped = Object.fromEntries(CHARACTER_CATEGORIES.map(category => [category, []]));
    for (const record of selected) grouped[assetCategory(record)].push(assetSummary(record));
    return {character_id,profile_asset_id:entry.current.id,include_retired,categories:categories || CHARACTER_CATEGORIES,assets:grouped,warnings:entry.warnings,note:'Only terminal revisions are returned. Retired assets are omitted unless include_retired is true; use character_history to inspect profile revisions.'};
  }
  async characterHistory(characterId) {
    assert(typeof characterId === 'string' && characterId.trim().length > 0 && characterId.length <= 200, 'Invalid character ID');
    const {characters} = await this.characterCatalog();
    const entry = characters.find(character => character.character_id === characterId);
    assert(entry, 'Character not found', 404);
    return {character_id:characterId,current_profile_asset_id:entry.current?.id || null,warnings:entry.warnings,revisions:entry.profiles.map(record => ({id:record.id,title:record.title,lifecycle:lifecycle(record),supersedes:record.supersedes || null,profile_version:record.technical?.character_profile?.version ?? record.technical?.character_profile?.profile_version ?? null,revision_reason:record.revision_reason || null})),note:'History is immutable and may include retired revisions. Do not select a historical profile for a new production without an explicit reason.'};
  }
  async characterMaterials({character_id, profile_asset_id} = {}) {
    assert(typeof character_id === 'string' && /^[A-Za-z0-9_-]{1,100}$/.test(character_id), 'Invalid character ID');
    const {characters,records} = await this.characterCatalog();
    const entry = characters.find(x => x.character_id === character_id);
    assert(entry, 'Character not found', 404);
    const identity = profile_asset_id ? entry.profiles.find(x => x.id === profile_asset_id) : entry.current;
    assert(identity, 'Character profile is missing or ambiguous; supply an owned profile_asset_id', 409);
    assert(lifecycle(identity) !== 'retired', 'Selected identity is retired', 409);
    const identityKey = record => canonical({version:record.technical?.character_profile?.version,lock:record.technical?.identity_lock,sha256:record.object?.sha256 || record.technical?.sha256 || null});
    const compatibleProfiles = new Set(entry.profiles.filter(x => identityKey(x) === identityKey(identity)).map(x => x.id));
    const successors = new Set(records.map(x => x.supersedes).filter(Boolean));
    const selected = records.filter(x => !successors.has(x.id) && lifecycle(x) !== 'retired' && (x.character_ids || []).includes(character_id) && (!x.technical?.character_profile_asset_id || compatibleProfiles.has(x.technical.character_profile_asset_id)));
    const assets = Object.fromEntries(MATERIAL_CATEGORIES.map(x => [x,[]]));
    for (const record of selected) {
      if (materialCategory(record) === 'identity_reference' && record.id !== identity.id) continue;
      assets[materialCategory(record)].push({...assetSummary(record),source_url:record.source_url,license:record.license,view:record.technical?.view || null,costume:record.technical?.costume || null,profile_asset_id:record.technical?.character_profile_asset_id || null,sha256:record.object?.sha256 || record.technical?.sha256 || null,download:record.object ? {url:`${this.origin}/v1/assets/${record.id}/file`,authentication:'service Bearer required'} : null});
    }
    if (!assets.identity_reference.some(x => x.id === identity.id)) assets.identity_reference.push({...assetSummary(identity),source_url:identity.source_url,license:identity.license,profile_asset_id:identity.id,sha256:identity.object?.sha256 || identity.technical?.sha256 || null,download:identity.object ? {url:`${this.origin}/v1/assets/${identity.id}/file`,authentication:'service Bearer required'} : null});
    const required = ['identity_reference','turnaround','expressions','actions','wardrobe','scenes','voices','videos'];
    return {schema:'character-materials/v1',character_id,profile_asset_id:identity.id,profile_version:identity.technical?.character_profile?.version ?? null,representation:representationOf(identity),studio_id:identity.technical?.studio_id || null,profile:identity.technical?.character_profile || {},identity_lock:identity.technical?.identity_lock || null,voice_recommendation:identity.technical?.voice_recommendation || null,assets,coverage:Object.fromEntries(required.map(category => [category,{count:assets[category].length,approved:assets[category].filter(x => x.review_status === 'user_approved').length}])),missing:required.filter(x => !assets[x].length),warnings:entry.warnings,note:'Candidates are not approved. A bundle is not a generation, rights, lip-sync or visual-quality certification. Pin profile_asset_id in the project.'};
  }
  async registerCharacterMaterial({id,character_id,category,representation,studio_id,profile,identity_lock,expected_profile_asset_id,reason} = {}) {
    this.writeAllowed();
    assert(typeof character_id === 'string' && /^[A-Za-z0-9_-]{1,100}$/.test(character_id), 'Invalid character ID');
    assert(MATERIAL_CATEGORIES.includes(category) && category !== 'other', 'Invalid material category');
    assert(['photorealistic_virtual','live_action','cartoon'].includes(representation), 'Explicit representation required');
    assert(typeof studio_id === 'string' && /^[a-z0-9-]{1,100}$/.test(studio_id), 'Explicit studio ID required');
    const {asset} = await this.get(id);
    assert(lifecycle(asset) !== 'retired', 'Retired material cannot be linked', 409);
    const kind = {voices:'voice',sfx:'sfx',bgm:'bgm',videos:'video'}[category] || 'image';
    assert(asset.kind === kind, 'Material category does not match asset kind');
    let current, existing;
    if (category === 'identity_reference') {
      assert(profile && profile.id === character_id && typeof profile.name === 'string' && profile.name.trim() && ((typeof profile.version === 'string' && profile.version.trim()) || Number.isInteger(profile.version)), 'Identity profile requires matching ID, name and version');
      assert(identity_lock && typeof identity_lock === 'object' && !Array.isArray(identity_lock) && typeof identity_lock.face === 'string' && identity_lock.face.trim() && typeof identity_lock.body_proportions === 'string' && identity_lock.body_proportions.trim(), 'Identity requires face and body-proportion locks');
      if (profile.approval === 'user_approved_visual_design') assert(typeof profile.approval_evidence === 'string' && profile.approval_evidence.trim(), 'Do not invent user approval');
      const catalog = await this.characterCatalog();
      existing = catalog.characters.find(x => x.character_id === character_id);
    } else {
      assert(profile === undefined && identity_lock === undefined, 'Only the identity material owns the profile and locks');
      current = await this.characterGet(character_id);
      assert(expected_profile_asset_id === current.profile_asset_id, 'Character profile changed or not pinned; refresh before linking', 409);
      const root = await this.load('records',current.profile_asset_id);
      assert(representationOf(root) === (representation === 'cartoon' ? 'cartoon' : 'realistic'), 'Representation differs from the selected identity');
      assert(!root.technical?.studio_id || root.technical.studio_id === studio_id, 'Studio differs from the selected identity');
    }
    const technical = {...asset.technical,asset_kind:category,representation,studio_id,character_material_schema:'character-material/v1'};
    if (profile) technical.character_profile = profile;
    if (identity_lock) technical.identity_lock = identity_lock;
    if (current) technical.character_profile_asset_id = current.profile_asset_id;
    const patch = {character_ids:[...new Set([...(asset.character_ids || []),character_id])],technical};
    if (existing && existing.current?.id !== id) {
      // Retrying an identical link must resolve its original immutable revision,
      // while a changed request must not create a second identity root.
      const {id:ignored,created_at,...previous} = asset;
      const expected = await sha(canonical({...previous,...patch,supersedes:id,revision_reason:reason}));
      assert(existing.current?.id === expected, 'Revise the existing identity instead of creating a second root', 409);
    }
    return this.revise(id,patch,reason);
  }
  async search({query = '', kind, cursor, limit = 40, tags_all = [], character_id, license_status, archive_allowed, bpm_min, bpm_max} = {}) {
    assert(Array.isArray(tags_all) && tags_all.length <= 20 && tags_all.every(t => typeof t === 'string'), 'Invalid tags filter');
    assert(bpm_min === undefined || Number.isFinite(bpm_min), 'Invalid BPM'); assert(bpm_max === undefined || Number.isFinite(bpm_max), 'Invalid BPM');
    assert(bpm_min === undefined || bpm_max === undefined || bpm_min <= bpm_max, 'Invalid BPM range');
    const {rows, next_cursor} = await this.page('records', cursor, limit);
    const words = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
    return {assets: rows.filter(r => (!kind || kind === r.kind) && tags_all.every(t => (r.tags || []).includes(t)) && (!character_id || (r.character_ids || []).includes(character_id)) && (!license_status || r.license?.status === license_status) && (archive_allowed === undefined || r.license?.archive_allowed === archive_allowed) && (bpm_min === undefined || (Number.isFinite(r.technical?.bpm) && r.technical.bpm >= bpm_min)) && (bpm_max === undefined || (Number.isFinite(r.technical?.bpm) && r.technical.bpm <= bpm_max)) && words.every(w => JSON.stringify([r.title,r.tags,r.use_cases]).toLowerCase().includes(w))), next_cursor, scanned: rows.length, note:'Page-scoped keyword search; follow next_cursor even if this page has no matches. Registration is not individual approval.'};
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
  async revise(id, patch, reason) {
    this.writeAllowed(); clean(patch);
    assert(typeof reason === 'string' && reason.trim(), 'Revision reason required');
    const allowed = ['title','tags','use_cases','avoid_use_cases','character_ids','technical','audition','review_status','lifecycle'];
    assert(patch && Object.keys(patch).length && Object.keys(patch).every(k => allowed.includes(k)), 'Revision cannot change identity, file, source or rights');
    if (patch.lifecycle) assert(['active','retired'].includes(patch.lifecycle), 'Invalid lifecycle');
    if (patch.character_ids) assert(stringArray(patch.character_ids), 'Invalid character ids');
    const previous = await this.load('records',id);
    const {id: ignored, object, created_at, ...card} = previous;
    const next = {...card,...patch,supersedes:id,revision_reason:reason};
    validateCard(next);
    return {...await this.append('records',{...next,object}),record:{...next,object},note:'Append-only revision; old ID and frozen projects remain valid. Branches are possible; no automatic latest-version approval.'};
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
      assert(record.license?.status !== 'user_authorized_private_reference' && record.license?.publication !== 'not_for_publication', 'Private research references cannot be selected as publication assets');
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
