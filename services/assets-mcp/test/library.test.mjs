import test from 'node:test';
import assert from 'node:assert/strict';
import {Library,sha,validateCard,authenticate} from '../src/library.mjs';
class MemoryR2 {
  data = new Map();
  async get(key) { const bytes = this.data.get(key); if(!bytes) return null; return {size:bytes.byteLength, text:async()=>new TextDecoder().decode(bytes),arrayBuffer:async()=>bytes,body:new Blob([bytes]).stream()}; }
  async put(key,value,options) {
    if(options?.onlyIf?.get('If-None-Match') === '*' && this.data.has(key)) return null;
    const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : new Uint8Array(value);
    assert.equal(await sha(bytes),options.sha256); this.data.set(key,bytes); return {key};
  }
  async list({prefix,limit=50,cursor}) {
    const keys = [...this.data.keys()].filter(x=>x.startsWith(prefix)).sort();
    const start = Number(cursor || 0), rows=keys.slice(start,start+limit);
    return {objects:rows.map(key=>({key})),truncated:start+limit<keys.length,cursor:String(start+limit)};
  }
}
const card = {schema_version:1,kind:'sfx',title:'test ding',source_type:'original_algorithm',source_url:'project://test/ding',review_status:'candidate_not_individually_approved',tags:['通知'],use_cases:['弹出消息'],license:{status:'user_authorized_generated',scope:'private archive',evidence:'original algorithm in this test',archive_allowed:true}};
const principal = {tenant:'vyibc',brand:'cartoon-xiaban',prefix:'xiaban/v2',legacy_prefix:'xiaban/v1',permissions:['read','write']};
function setup(p=principal,b=new MemoryR2()) { return new Library(b,p,'https://example.test'); }
test('registration, cross-instance lookup and identical concurrent dedup', async()=>{
  const l=setup(); const [a,b] = await Promise.all([l.register(card),l.register(card)]);
  assert.equal(a.id,b.id); assert.equal(l.bucket.data.size,1);
  assert.equal((await setup(principal,l.bucket).get(a.id)).asset.title,card.title);
});
test('binary dedup, authenticated download and checksum',async()=>{
  const l=setup(),file={bytes:new TextEncoder().encode('test WAV bytes'),extension:'.wav'};
  const a=await l.register(card,file); const b=await l.register({...card,title:'different context'},file);
  assert.notEqual(a.id,b.id); assert.equal(l.bucket.data.size,3);
  const response=await l.file(a.id); assert.equal(await sha(await response.arrayBuffer()),a.record.object.sha256);
});
test('rights, personal voice, secrets, ownership and file type gate',async()=>{
  const l=setup(),file={bytes:new Uint8Array([1]),extension:'.wav'};
  for(const c of [{...card,personal_reference:true},{...card,voice_identity:'user_clone'},{...card,token:'hidden'},{...card,owner:'another'},{...card,source_url:'https://source.test/file?token=bad'},{...card,license:{...card.license,archive_allowed:false}}]) await assert.rejects(()=>l.register(c,file));
  await assert.rejects(()=>l.register({...card,kind:'voice'},file));
  await assert.rejects(()=>l.register(card,{...file,extension:'.html'}));
  assert.equal(l.bucket.data.size,0);
});
test('unknown rights allow metadata but not binary',async()=>{
  const c={...card,kind:'bgm',license:{status:'unknown',scope:'unknown',evidence:'source only',archive_allowed:false}};
  validateCard(c); assert.throws(()=>validateCard(c,true));
});
test('tenant prefix and read-only principal isolation',async()=>{
  const l=setup(),a=await l.register(card);
  const other=setup({...principal,prefix:'other/v2',legacy_prefix:undefined},l.bucket);
  await assert.rejects(()=>other.get(a.id),{status:404});
  const ro=setup({...principal,permissions:['read']},l.bucket);
  await assert.rejects(()=>ro.register(card),{status:403}); assert.equal((await ro.get(a.id)).asset.title,card.title);
});
test('authentication fails closed and supports read-only token',async()=>{
  const env={AUTH_CLIENTS:JSON.stringify([{...principal,token_sha256:await sha('test-token'),permissions:['read']}])};
  await assert.rejects(()=>authenticate(new Request('https://a/'),env),{status:401});
  await assert.rejects(()=>authenticate(new Request('https://a/',{headers:{Authorization:'Bearer bad'}}),env),{status:401});
  await assert.rejects(()=>authenticate(new Request('https://a/',{headers:{Authorization:'Bearer test-token'}}),env,'write'),{status:403});
});
test('feedback persists without promoting card review status',async()=>{
  const l=setup(),a=await l.register(card),f={asset_id:a.id,project:'test',outcome:'used',reason:'test scene',reviewer:'editor',observed_at:'2026-09-07T00:00:00Z'};
  assert.equal((await l.feedback(f)).id,(await l.feedback(f)).id);
  assert.equal((await l.get(a.id)).asset.review_status,card.review_status);
  let result=await l.feedbackList(a.id); result=await l.feedbackList(a.id,result.next_cursor);
  assert.equal(result.feedback.length,1);
});
test('legacy integrity checked; legacy media and feedback discoverable',async()=>{
  const l=setup(),legacy={...card,created_at:'2026-09-07',object:null},raw=JSON.stringify(legacy,null,2)+'\n';
  const id='a'.repeat(32)+'-'+await sha(raw);
  await l.immutable('xiaban/v1/records/'+id+'.json',raw);
  assert.equal((await l.search()).assets[0].id,id);
  l.bucket.data.set('xiaban/v1/records/'+id+'.json',new TextEncoder().encode('{}'));
  await assert.rejects(()=>l.get(id),{status:409});
});
test('search cursor must be followed including an empty legacy page',async()=>{
  const l=setup(); await l.register(card); await l.register({...card,title:'second'});
  const first=await l.search({limit:1}); assert.equal(first.assets.length,0); assert(first.next_cursor);
  const second=await l.search({limit:1,cursor:first.next_cursor}); assert.equal(second.assets.length,1); assert(second.next_cursor);
  assert.equal((await l.search({limit:1,cursor:second.next_cursor})).assets.length,1);
});
test('BGM freeze requires new research, persists immutable project',async()=>{
  const l=setup(),a=await l.register({...card,kind:'bgm'});
  const selection={project:'episode-test',story_intent:'comedy',platform:'douyin',selected:[{asset_id:a.id,reason:'setup',project_review:{status:'verified_for_project',allowed_platforms:['douyin'],evidence:'test evidence',checked_at:'2026-09-07'}}]};
  await assert.rejects(()=>l.freeze(selection));
  selection.new_music_research={performed:true,checked_at:'2026-09-07',queries:['new'],source_urls:['https://example.com/music'],new_candidates:[],no_new_candidate_reason:'test only, no new audio selected'};
  const frozen=await l.freeze(selection); assert.equal((await setup(principal,l.bucket).load('projects',frozen.id)).selection.project,'episode-test');
});
test('no traversal or absent immutable version accepted',async()=>{
  const l=setup(); await assert.rejects(()=>l.get('../other')); await assert.rejects(()=>l.get('f'.repeat(64)),{status:404});
});
test('freeze rejects truthy objects and string-as-platform/research arrays',async()=>{
  const l=setup(),a=await l.register({...card,kind:'bgm'});
  const base={project:'test',story_intent:'test',platform:'douyin',selected:[{asset_id:a.id,reason:'test',project_review:{status:'verified_for_project',allowed_platforms:['douyin'],evidence:'test',checked_at:'2026-09-07'}}],new_music_research:{performed:true,checked_at:'2026-09-07',queries:['new'],source_urls:['https://example.com'],new_candidates:[],no_new_candidate_reason:'test'}};
  for(const patch of [{allowed_platforms:'not-douyin'},{evidence:{}},{checked_at:{}}]) {
    const input=structuredClone(base); Object.assign(input.selected[0].project_review,patch); await assert.rejects(()=>l.freeze(input));
  }
  for(const patch of [{queries:'x'},{source_urls:'x'},{source_urls:['not-a-url']},{checked_at:{}},{no_new_candidate_reason:{}}]) {
    const input=structuredClone(base); Object.assign(input.new_music_research,patch); await assert.rejects(()=>l.freeze(input));
  }
});
test('structured filters require all tags and keep unknown BPM out of ranges',async()=>{
 const l=setup({...principal,legacy_prefix:undefined});
 await l.register({...card,tags:['喜剧','反转'],character_ids:['hongyi'],technical:{bpm:94}});
 await l.register({...card,title:'unknown',tags:['喜剧'],character_ids:['xiaban']});
 assert.equal((await l.search({tags_all:['喜剧','反转'],character_id:'hongyi',bpm_min:90,bpm_max:100,archive_allowed:true})).assets.length,1);
 assert.equal((await l.search({tags_all:['反转'],character_id:'xiaban'})).assets.length,0);
 assert.equal((await l.search({bpm_min:1})).assets.length,1);
 await assert.rejects(()=>l.search({bpm_min:100,bpm_max:90}));
});
test('revision preserves original media and rights; identical retry deduplicates',async()=>{
 const l=setup(); const a=await l.register(card,{bytes:new Uint8Array([1,2,3]),extension:'.wav'});
 const b=await l.revise(a.id,{tags:['收尾'],lifecycle:'retired'},'no longer default');
 assert.equal((await l.revise(a.id,{tags:['收尾'],lifecycle:'retired'},'no longer default')).id,b.id);
 assert.deepEqual((await l.get(a.id)).asset.tags,['通知']);assert.deepEqual(b.record.object,a.record.object);
 assert.equal(await sha(await (await l.file(b.id)).arrayBuffer()),a.record.object.sha256);
 await assert.rejects(()=>l.revise(a.id,{license:{status:'approved'}},'invalid'));
 const other=setup({...principal,prefix:'other/v2',legacy_prefix:undefined},l.bucket);
 await assert.rejects(()=>other.revise(a.id,{tags:['leak']},'invalid'),{status:404});
});
