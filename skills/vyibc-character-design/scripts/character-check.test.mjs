import test from 'node:test';
import assert from 'node:assert/strict';
import {validateCast} from './character-check.mjs';

const evidence = {status:'pass',evidence:'synthetic fixture, not a live result'};
const asset = kind => ({kind,url:'https://example.com/'+kind+'.png',sha256:'a'.repeat(64),provider:'fixture',prompt:'fixture prompt',inputReferences:[],views:['front','side','back'],expressions:['sleepy','happy'],technical:{...evidence},visual:{...evidence}});
const character = (id='hero') => ({id,version:1,name:id,role:'supporting',species:'human',age:20,brief:'fixture',identityLocks:['face'],references:[],requiredAssets:['turnaround','expressions'],assets:[asset('turnaround'),asset('expressions')],approval:{status:'approved',evidence:'fixture user approval'}});
const cast = () => ({schemaVersion:1,projectId:'fixture',style:{id:'3d',description:'soft'},characters:[character()],lineups:[]});
test('single approved character',()=>assert.deepEqual(validateCast(cast(),{approved:true}),[]));
test('missing image is not completion',()=>{const d=cast();d.characters[0].assets.pop();assert.ok(validateCast(d).some(e=>e.includes('missing required')));});
test('duplicate identities and stale lineup versions fail',()=>{const d=cast();d.characters.push(character('roommate'));d.lineups=[{members:[{characterId:'hero',version:1},{characterId:'roommate',version:2}],asset:asset('lineup')}];assert.ok(validateCast(d,{approved:true}).some(e=>e.includes('stale')));d.characters.push(character());assert.ok(validateCast(d).some(e=>e.includes('duplicate character')));});
test('complete actor group is required for approved handoff',()=>{const d=cast();d.characters.push(character('roommate'),character('ghost'));assert.ok(validateCast(d,{approved:true}).length);d.lineups=[{members:d.characters.map(c=>({characterId:c.id,version:c.version})),asset:asset('lineup')}];assert.deepEqual(validateCast(d,{approved:true}),[]);d.lineups[0].members.pop();assert.ok(validateCast(d,{approved:true}).some(e=>e.includes('complete current')));});
test('visual and user acceptance independent of generation',()=>{const d=cast();d.characters[0].approval.status='draft';d.characters[0].assets[0].visual.status='pending';assert.deepEqual(validateCast(d),[]);assert.ok(validateCast(d,{approved:true}).length>=2);});
test('credentials and wrong turns are rejected',()=>{for(const url of ['https://user:pass@example.com/a','https://example.com/a?xsec_token=abc','https://example.com/a?X-Amz-Signature=abc','http://example.com/a']){const d=cast();d.characters[0].assets[0].url=url;assert.ok(validateCast(d).some(e=>e.includes('HTTPS')));}const d=cast();d.characters[0].assets[0].views=['front','three-quarter','back'];assert.ok(validateCast(d).some(e=>e.includes('front/side/back')));});
test('nonhuman and minimal background design are allowed',()=>{const d=cast();const c=d.characters[0];c.species='talking-teacup';delete c.age;c.requiredAssets=['silhouette'];c.assets=[asset('silhouette')];assert.deepEqual(validateCast(d),[]);});
test('bad shapes produce errors, not crashes',()=>{for(const d of [null,[],{}, {...cast(),characters:[null]}, {...cast(),lineups:[null]}])assert.ok(validateCast(d).length);});
test('no invented approval or missing evidence',()=>{const d=cast();d.characters[0].approval.evidence='';d.characters[0].assets[0].technical.evidence='';assert.ok(validateCast(d).length>=2);});
