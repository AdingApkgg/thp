// Full-entry differential comparison for mainline and fractional ZUN targets.
// Uses a fresh thtk extraction, so a partial/stale directory cannot make this pass.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {resolve,dirname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../../../..');
const corePath=resolve(repo,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
const coreBytes=readFileSync(corePath);
const thdat=resolve(repo,'tools/thtk/extracted/thtk-bin-12/thdat.exe');
const output=resolve(repo,'artifacts/archive-differential');
mkdirSync(output,{recursive:true});
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');

// Current user scope: verify the seven THA1 mainline targets by default.
// Other title codecs can still be checked explicitly with TH_ARCHIVE_TITLES.
const titles=process.env.TH_ARCHIVE_TITLES?.split(',').map(Number)??[12,13,14,16,17,18,19];
for(const title of titles)test(`TH${title}: every archive entry matches a fresh thtk extraction`,async()=>{
 const targetPath=resolve(repo,`runtimes/th${title}/${title===12?'th12_web/':''}target.json`);
 const target=JSON.parse(readFileSync(targetPath,'utf8'));
 const record=target.dataArchives[`th${title}.dat`];
 const bytes=readFileSync(record.path);
 assert.equal(bytes.length,record.bytes);
 if(record.sha256)assert.equal(sha(bytes),record.sha256);
 // thtk 12 predates TH18/19. Its TH17 archive codec is the independent
 // reference for these archives; all entries must match, not just the header.
 const thtkVersion=(title===18||title===19)?17:title;
 const listing=execFileSync(thdat,['-l',String(thtkVersion),record.path],{encoding:'utf8',windowsHide:true});
 const rows=[...listing.matchAll(/^(\S+)\s+(\d+)\s+(\d+)\s*$/gm)]
  .map(m=>({name:m[1],size:Number(m[2]),packed:Number(m[3])}));
 assert.equal(rows.length,record.entries,'thtk entry count vs surveyed archive header');
 const extraction=mkdtempSync(resolve(output,`th${title}-`));
 for(const row of rows)assert.ok(resolve(extraction,row.name).startsWith(extraction+sep),'entry must stay inside extraction');
 execFileSync(thdat,['-x',String(thtkVersion),record.path],{cwd:extraction,stdio:'pipe',windowsHide:true});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
 const {instance}=await WebAssembly.instantiate(coreBytes,{wasi_snapshot_preview1:wasi.wasiImport});
 wasi.initialize(instance);
 const c=instance.exports,p=c.allocate(bytes.length),archive=c.archive_create();
 assert.notEqual(p,0);
 new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);
 const decoded=[];
 try{
  assert.equal(c.archive_open(archive,p,bytes.length,record.pbgVersion),1);
  assert.equal(c.archive_count(archive),rows.length);
  for(let n=0;n<rows.length;n++){
   const row=rows[n],pointer=c.archive_name(archive,n);
   const nameBytes=new Uint8Array(c.memory.buffer,pointer,1025),end=nameBytes.indexOf(0);
   assert.ok(end>=0,'entry name is terminated');
   assert.equal(new TextDecoder().decode(nameBytes.subarray(0,end)),row.name);
   assert.equal(c.archive_field(archive,n,1),row.size);
   assert.equal(c.archive_field(archive,n,2),row.packed);
   const out=c.allocate(Math.max(row.size,1));
   assert.notEqual(out,0);
   try{
    assert.equal(c.archive_read(archive,n,out,row.size),row.size,`${row.name}: decoded size`);
    const actual=Buffer.from(new Uint8Array(c.memory.buffer,out,row.size));
    const expected=readFileSync(resolve(extraction,row.name));
    assert.equal(expected.length,row.size,`${row.name}: reference size`);
    assert.ok(actual.equals(expected),`${row.name}: decoded bytes differ`);
    decoded.push({name:row.name,bytes:row.size,sha256:sha(actual)});
   }finally{c.release(out);}
  }
 }finally{c.archive_delete(archive);c.release(p);}
 assert.equal(decoded.length,record.entries);
 writeFileSync(resolve(output,`th${title}.json`),JSON.stringify({game:`th${title}`,passed:true,
  coreSha256:sha(coreBytes),archiveSha256:sha(bytes),thtkVersion,entries:decoded.length,
  comparedAgainstThtk:decoded.length,extraction,decoded},null,2)+'\n');
});
