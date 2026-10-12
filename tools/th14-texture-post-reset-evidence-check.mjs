import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),evidence={};
const sha=b=>createHash('sha256').update(b).digest('hex');
function track(p){const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;}
const source=JSON.parse(track('artifacts/th14/dialogue-text-check/objects.json'));
for(const [p,h] of Object.entries(source.sourceHashes))assert.equal(h,sha(track('runtimes/th12/th12_web/'+p)));
const summaries=[];
for(const precision of [53,64]){
 const prefix=`artifacts/th14/physical-texture32-post-reset/${precision}/`;
 const nBytes=track(prefix+'native.json'),n=JSON.parse(nBytes);
 const r=JSON.parse(track(`docs/porting/th14-physical-texture32-post-reset-image-${precision}-observed-oct12.json`));
 assert.equal(r.passed,false);assert.equal(r.differences.length,238);assert.equal(r.comparedBytes,130010432);
 assert.equal(r.cases,437);assert.equal(r.resources,57);assert.deepEqual(r.sourceHashes,source.sourceHashes);
 assert.equal(n.postDevicePrecision,precision);assert.equal(n.forcedPostDevicePrecision,true);
 assert.equal(n.postDeviceControl&0x30000,precision===64?0:0x10000);
 assert.equal(n.toolSha256,sha(track('tools/th14-native-physical-texture32-post-reset.py')));
 assert.equal(n.helperSourceSha256,sha(track('tools/th14-physical-texture32-post-reset-helper.cpp')));
 assert.equal(n.helperSha256,sha(track('artifacts/th14/physical-texture32-post-reset/texture32.exe')));
 assert.equal(n.requestInputSha256,sha(track('artifacts/th14/physical-texture32-post-reset/requests.bin')));
 assert.equal(n.requestProofSha256,sha(track('artifacts/th14/anm-physical-resource-loader/native.json')));
 for(const [field,path] of [['d3dxSha256','C:/Windows/SysWOW64/d3dx9_43.dll'],['d3d9Sha256','C:/Windows/SysWOW64/d3d9.dll']])assert.equal(n[field],sha(readFileSync(path)));
 const pixels=track(prefix+'textures.bin');assert.equal(pixels.length,n.bytes);assert.equal(n.binarySha256,sha(pixels));
 assert.equal(r.nativeProofSha256,sha(nBytes));assert.equal(r.nativeBinarySha256,n.binarySha256);
 assert.equal(r.wasmSha256,sha(track(prefix+'textures.wasm')));
 assert.equal(r.toolSha256,sha(track('tools/th14-physical-texture32-post-reset-image-check.mjs')));
 assert.equal(r.fixtureSha256,sha(track('runtimes/th12/th12_web/tests/cpp/th14-physical-texture-image-fixture.cpp')));
 summaries.push({precision,textureDifferences:r.differences.length,differentBytes:r.differences.reduce((sum,d)=>sum+d.errors.reduce((v,e)=>v+(e.differentBytes??0),0),0),binarySha256:n.binarySha256,scope:n.scope});
}
assert.equal(summaries[0].binarySha256,summaries[1].binarySha256);
track('tools/th14-texture-post-reset-evidence-check.mjs');
const report={diagnosticEvidenceVerified:true,strictPixelsEqual:false,completeGame:false,nativeEquivalent:false,productionChanged:false,summaries,evidence,
 limits:'Forced post-device53/64 precision is a controlled hypothesis, including actual x87 FNINIT for64. The observed production24-bit pixel matches remain separate; 238 differing textures remain failures. Requires real retail upload control capture to select runtime behavior; no full-game or HAL-frame claim.'};
writeFileSync(resolve(root,'docs/porting/th14-texture-post-reset-diagnostic-oct12.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({diagnosticEvidenceVerified:true,strictPixelsEqual:false,summaries:summaries.map(({precision,textureDifferences,differentBytes})=>({precision,textureDifferences,differentBytes}))}));
