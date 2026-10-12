import test from 'node:test';
import assert from 'node:assert/strict';
import {openTfpk,openCg,decryptCg,tfpkPathHash} from './archives.mjs';

test('Readers reject corrupt headers, short reads and entry ranges',async()=>{
 const truncated=new Uint8Array([84,70,80,75,0]);
 await assert.rejects(openTfpk((o,n)=>truncated.slice(o,o+n),5),/truncated RSA/);
 await assert.rejects(openTfpk(()=>new Uint8Array(4),100),/short archive read/);
 await assert.rejects(openTfpk(()=>new Uint8Array([84,70,80,75,9]),100),/unsupported TFPK/);
 await assert.rejects(openCg(()=>new Uint8Array(),16),/truncated CG/);
 const footer=new Uint8Array(32),v=new DataView(footer.buffer);
 v.setUint32(20,24,true);v.setUint32(24,10,true);v.setUint32(28,32,true);
 const encrypted=decryptCg(footer,0);
 await assert.rejects(openCg((o,n)=>encrypted.subarray(o,o+n),32),/archive range outside/);
});

test('Path hashes normalize ASCII case and separators without guessing Japanese encoding',()=>{
 for(const version of [0,1]){
  assert.equal(tfpkPathHash('DATA/Script/Boot.nut',version),tfpkPathHash('data\\script\\boot.nut',version));
  assert.throws(()=>tfpkPathHash('日本語.nut',version),/Shift-JIS/);
 }
 assert.notEqual(tfpkPathHash('data/script/boot.nut',0),tfpkPathHash('data/script/boot.nut',1));
});
