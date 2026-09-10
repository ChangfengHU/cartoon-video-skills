import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';

const text = v => typeof v === 'string' && v.trim().length > 0;
const stableUrl = v => {
  try {
    const u = new URL(v);
    return u.protocol === 'https:' && !u.username && !u.password && !u.hash &&
      ![...u.searchParams.keys()].some(k => /token|signature|credential|secret|password|api.?key|authorization|x-amz|x-goog/i.test(k));
  } catch { return false; }
};

export function validateCast(cast, {approved = false} = {}) {
  const errors = [];
  const check = (ok, message) => { if (!ok) errors.push(message); };
  if (!cast || typeof cast !== 'object' || Array.isArray(cast)) return ['cast must be an object'];
  check(cast.schemaVersion === 1, 'schemaVersion must be 1');
  check(text(cast.projectId), 'projectId required');
  check(text(cast.style?.id) && text(cast.style?.description), 'shared style required');
  const chars = Array.isArray(cast.characters) ? cast.characters : [];
  check(chars.length > 0, 'characters required');
  const ids = new Map();
  const evidence = (record, label, states) => {
    check(states.includes(record?.status), label + ': invalid status');
    if (record?.status && !['pending', 'draft'].includes(record.status)) check(text(record.evidence), label + ': evidence required');
  };
  const asset = (a, label) => {
    if (!a || typeof a !== 'object') { check(false, label + ': asset object required'); return; }
    check(text(a.kind), label + ': kind required');
    check(stableUrl(a.url), label + ': stable HTTPS URL required (no credentials)');
    check(/^[a-f0-9]{64}$/.test(a.sha256 || ''), label + ': real sha256 required');
    check(text(a.provider) && text(a.prompt), label + ': actual provider/prompt required');
    check(Array.isArray(a.inputReferences) && a.inputReferences.every(stableUrl), label + ': inputReferences must be safe URL array');
    evidence(a.technical, label + ' technical', ['pending', 'pass', 'fail']);
    evidence(a.visual, label + ' visual', ['pending', 'pass', 'fail']);
    if (a.kind === 'turnaround') check(Array.isArray(a.views) && ['front','side','back'].every(v => a.views.includes(v)), label + ': front/side/back required');
    if (a.kind === 'expressions') check(Array.isArray(a.expressions) && a.expressions.length > 0 && a.expressions.every(text), label + ': expression labels required');
    if (approved) check(a.technical?.status === 'pass' && a.visual?.status === 'pass', label + ': not technically/visually accepted');
  };
  for (const [i,c] of chars.entries()) {
    const label = 'character[' + i + ']';
    if (!c || typeof c !== 'object') { check(false, label + ': object required'); continue; }
    check(text(c.id) && /^[a-z0-9][a-z0-9_-]*$/.test(c.id), label + ': safe id required');
    check(!ids.has(c.id), label + ': duplicate character id');
    ids.set(c.id, c.version);
    check(Number.isInteger(c.version) && c.version > 0, label + ': positive version required');
    for (const key of ['name','role','species','brief']) check(text(c[key]), label + ': ' + key + ' required');
    if (c.age !== undefined) check(Number.isFinite(c.age) && c.age >= 0, label + ': invalid age');
    check(Array.isArray(c.identityLocks) && c.identityLocks.length > 0 && c.identityLocks.every(text), label + ': identityLocks required');
    check(Array.isArray(c.references) && c.references.every(r => r && stableUrl(r.url) && text(r.purpose)), label + ': invalid references');
    const required = Array.isArray(c.requiredAssets) ? c.requiredAssets : [];
    check(required.length > 0 && required.every(text) && new Set(required).size === required.length, label + ': unique requiredAssets required');
    const assets = Array.isArray(c.assets) ? c.assets : [];
    const kinds = assets.map(a => a?.kind);
    check(new Set(kinds).size === kinds.length, label + ': duplicate asset kind');
    for (const kind of required) check(kinds.includes(kind), label + ': missing required asset ' + kind);
    for (const a of assets) asset(a, label + '/' + (a?.kind || '?'));
    evidence(c.approval, label + ' approval', ['draft','approved','rejected']);
    if (approved) check(c.approval?.status === 'approved', label + ': user approval missing');
  }
  const lineups = Array.isArray(cast.lineups) ? cast.lineups : [];
  check(Array.isArray(cast.lineups), 'lineups must be an array');
  let wholeCast = false;
  for (const [i,l] of lineups.entries()) {
    const label = 'lineup[' + i + ']';
    const members = Array.isArray(l?.members) ? l.members : [];
    check(members.length >= 2, label + ': at least two members required');
    check(new Set(members.map(m => m?.characterId)).size === members.length, label + ': duplicate member');
    for (const m of members) check(m && ids.has(m.characterId) && ids.get(m.characterId) === m.version, label + ': unknown/stale character version');
    check(l?.asset?.kind === 'lineup', label + ': asset kind must be lineup');
    asset(l?.asset, label);
    if (members.length === chars.length && [...ids].every(([id,version]) => members.some(m => m?.characterId === id && m.version === version))) wholeCast = true;
  }
  if (approved && chars.length > 1) check(wholeCast, 'approved cast requires a complete current-version lineup');
  return errors;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = process.argv.slice(2);
    if (!args[0] || args.slice(1).some(a => a !== '--approved')) throw Error('Usage: node character-check.mjs cast.json [--approved]');
    const errors = validateCast(JSON.parse(readFileSync(args[0], 'utf8')), {approved: args.includes('--approved')});
    console.log(JSON.stringify({ok: errors.length === 0, scope: 'structure-only; supplied evidence is not independently verified', errors}, null, 2));
    if (errors.length) process.exitCode = 1;
  } catch (e) { console.error(e.message); process.exitCode = 1; }
}
