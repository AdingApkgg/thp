import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,openSync,readSync,closeSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {openPkgl,archiveSeed,pkglDecrypt} from './pkgl.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const sha=b=>createHash('sha256').update(b).digest('hex');

test('Every TH06nc PKGL entry agrees with native-checked Python and libzstd',async()=>{
 const target=JSON.parse(readFileSync(resolve(root,'runtimes/th06nc/target.json'),'utf8'));
 assert.equal(sha(readFileSync(target.executable)),target.sha256);
 const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th06nc/pkgl-python.json'),'utf8'));
 assert.equal(proof.executableSha256,target.sha256);
 assert.equal(proof.readerSha256,sha(readFileSync(resolve(root,'tools/th06nc-pkgl.py'))));
 const archives=[];
 for(const reference of proof.archives){
  assert.equal(reference.decoded.length,reference.entries.length,'run Python --verify-all first');
  const fd=openSync(resolve(dirname(target.executable),'data',reference.file),'r');
  try{
   const readAt=(offset,length)=>{const b=Buffer.alloc(length);let done=0;
    while(done<length){const n=readSync(fd,b,done,length-done,offset+done);assert.ok(n>0);done+=n;}return b;};
   const archive=await openPkgl(readAt,reference.bytes,reference.file);
   assert.deepEqual(archive.entries.map(({index,...e})=>e),reference.entries);
   let decodedBytes=0;
   for(const entry of archive.entries){
    const bytes=await archive.readEntry(entry.index);
    assert.equal(sha(bytes),reference.decoded[entry.index].sha256,reference.file+'/'+entry.name);
    decodedBytes+=bytes.length;
   }
   archives.push({file:reference.file,entries:archive.entries.length,decodedBytes});
   console.log(`${reference.file}: ${archive.entries.length} complete entries agree`);
  }finally{closeSync(fd);}
 }
 writeFileSync(resolve(root,'artifacts/th06nc/pkgl-comparison.json'),JSON.stringify({passed:true,game:'th06nc',
  executableSha256:target.sha256,readerSha256:sha(readFileSync(resolve(root,'shared/th06nc/pkgl.mjs'))),
  zstdSha256:sha(readFileSync(resolve(root,'shared/vendor/fzstd/index.mjs'))),archives},null,2)+'\n');
});

function fixture(){
 const name=new TextEncoder().encode('file.txt'),plain=new Uint8Array([1,2,3]),table=new Uint8Array(32+name.length),v=new DataView(table.buffer);
 v.setUint32(2,12345,true);v.setBigUint64(6,3n,true);v.setBigUint64(14,3n,true);
 v.setBigUint64(22,BigInt(8+table.length),true);v.setUint16(30,name.length,true);table.set(name,32);
 const bytes=new Uint8Array(8+table.length+plain.length),header=new DataView(bytes.buffer);
 header.setUint32(0,0x4c474b50,true);header.setUint32(4,table.length,true);
 bytes.set(pkglDecrypt(table,archiveSeed('test.dat')),8);bytes.set(pkglDecrypt(plain,12345),8+table.length);
 return bytes;
}

test('PKGL refuses malformed directories and preserves input bytes',async()=>{
 const bytes=fixture(),copy=bytes.slice(),read=(o,n)=>bytes.subarray(o,o+n);
 const archive=await openPkgl(read,bytes.length,'test.dat');
 assert.deepEqual(await archive.readEntry(0),new Uint8Array([1,2,3]));assert.deepEqual(bytes,copy);
 await assert.rejects(openPkgl(()=>new Uint8Array(4),100,'test.dat'),/short PKGL/);
 await assert.rejects(openPkgl(read,bytes.length,'WRONG.dat'));
 await assert.rejects(openPkgl(read,bytes.length-1,'test.dat'),/entry extent/);
 await assert.rejects(openPkgl(read,bytes.length,'test.dat',{maxEntryBytes:2}),/entry extent/);
 await assert.rejects(archive.readEntry(100),/unknown PKGL/);
});
