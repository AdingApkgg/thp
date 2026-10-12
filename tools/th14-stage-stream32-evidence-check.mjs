import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),evidence={},sha=b=>createHash('sha256').update(b).digest('hex'),track=p=>{const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;},json=p=>JSON.parse(track(p));
const observed=json('docs/porting/th14-stage-stream32-observed-oct12.json'),base='artifacts/th14/stage-stream32/',native=json('artifacts/th14/stage-gpu-stream-replay/native.json'),prepared=track('artifacts/th14/stage-gpu-stream-replay/prepared.json'),pixels=track('artifacts/th14/stage-gpu-stream-replay/native.bgra');
assert(observed.passed);assert.equal(observed.frames,42);assert.equal(observed.pixelBytes,51609600);assert.equal(observed.preparedSha256,sha(prepared));assert.equal(observed.nativeProofSha256,evidence['artifacts/th14/stage-gpu-stream-replay/native.json'].sha256);assert.equal(observed.nativePixelsSha256,sha(pixels));assert.equal(native.pixelsSha256,sha(pixels));
assert.equal(observed.requestsSha256,sha(track(base+'requests.bin')));assert.equal(observed.requestsBytes,evidence[base+'requests.bin'].bytes);assert.equal(observed.helperSourceSha256,sha(track('tools/th14-stage-stream32-helper.cpp')));assert.equal(observed.toolSha256,sha(track('tools/th14-native-stage-stream32.py')));assert.equal(observed.helperSha256,sha(track(base+'stream32.exe')));assert.equal(observed.d3d9Sha256,sha(readFileSync('C:/Windows/SysWOW64/d3d9.dll')));
const exe=readFileSync(resolve(root,base+'stream32.exe')),pe=exe.readUInt32LE(0x3c);assert.equal(exe.readUInt16LE(pe+4),0x14c);
for(const row of observed.outputs){
 const b=track(base+'readback-'+row.precision+'.bin');assert.equal(sha(b),row.sha256);assert.equal(b.length,row.bytes);assert.equal(b.readUInt32LE(0),21);assert.equal(b.readUInt32LE(4),0x7f);assert.equal(b.readUInt32LE(8),row.precision===24?0x7f:0x37f);let offset=20;
 for(let i=0;i<21;i++){
  const n=native.frames[i],r=row.frames[i];assert.equal(b.readUInt32LE(offset),n.stage);assert.equal(b.readUInt32LE(offset+4),n.frame);assert.equal(b.readUInt32LE(offset+8),r.fpcw);offset+=12;
  const actual=b.subarray(offset,offset+n.bytes),expected=pixels.subarray(n.offset,n.offset+n.bytes);assert(actual.equals(expected));assert.equal(sha(actual),r.sha256);assert.equal(r.nativeSha256,n.sha256);assert.equal(r.differentBytes,0);offset+=n.bytes;
 }assert.equal(offset,b.length);assert.equal(row.differentBytes,0);
}
const report={passed:true,completeGame:false,nativeEquivalent:false,frames:42,pixelBytes:51609600,differentBytes:0,evidence,toolSha256:sha(readFileSync(import.meta.filename)),scope:observed.scope};
writeFileSync(resolve(root,'docs/porting/th14-stage-stream32-evidence-verified-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,frames:42,pixelBytes:51609600,differentBytes:0}));
