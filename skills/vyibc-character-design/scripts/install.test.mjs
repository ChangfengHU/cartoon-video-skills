import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,symlinkSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {install} from './install.mjs';

test('idempotent install and link-only uninstall retain source and neighbors',()=>{
 const dir=mkdtempSync(join(tmpdir(),'character-install-test-'));
 try {const other=join(dir,'other.txt');writeFileSync(other,'keep');assert.equal(install(dir).changed,true);assert.equal(install(dir).changed,false);assert.ok(existsSync(join(dir,'vyibc-character-design','SKILL.md')));assert.equal(install(dir,{uninstall:true}).changed,true);assert.equal(install(dir,{uninstall:true}).changed,false);assert.equal(readFileSync(other,'utf8'),'keep');assert.equal(install(dir).changed,true);assert.ok(existsSync(join(dir,'vyibc-character-design','SKILL.md')));}finally{rmSync(dir,{recursive:true,force:true});}
});
test('different file, directory and dangling symlink preserved',()=>{
 for(const kind of ['file','directory','symlink']) {const dir=mkdtempSync(join(tmpdir(),'character-collision-test-'));const target=join(dir,'vyibc-character-design');try {if(kind==='file')writeFileSync(target,'keep');if(kind==='directory')mkdirSync(target);if(kind==='symlink')symlinkSync(join(dir,'absent'),target);assert.throws(()=>install(dir),/ownership/);assert.throws(()=>install(dir,{uninstall:true}),/ownership/);if(kind==='file')assert.equal(readFileSync(target,'utf8'),'keep');}finally{rmSync(dir,{recursive:true,force:true});}}
});
