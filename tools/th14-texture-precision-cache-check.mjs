import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(root,p));
const proofBytes=read('docs/porting/th14-physical-texture32-high-precision-image-64-observed-oct12.json'),proof=JSON.parse(proofBytes);assert(proof.passed);
for(const [p,h] of Object.entries(proof.sourceHashes))assert.equal(sha(read('runtimes/th12/th12_web/'+p)),h,p);
const wasmBytes=read('artifacts/th14/physical-texture32-post-reset/high-precision-check/64/textures.wasm');assert.equal(sha(wasmBytes),proof.wasmSha256);
const high=JSON.parse(read('artifacts/th14/physical-texture32-post-reset/64/native.json')),low=JSON.parse(read('artifacts/th14/physical-texture32-pixels/64/native.json'));
const highPixels=read('artifacts/th14/physical-texture32-post-reset/64/textures.bin'),lowPixels=read('artifacts/th14/physical-texture32-pixels/64/textures.bin');assert.equal(sha(highPixels),high.binarySha256);assert.equal(sha(lowPixels),low.binarySha256);assert.equal(high.cases.length,437);assert.equal(low.cases.length,437);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,archive=JSON.parse(read('artifacts/archive-differential/th14.json'));let name='',loads=0,comparedBytes=0;
for(let i=0;i<high.cases.length;i++){
 const h=high.cases[i],l=low.cases[i];for(const field of ['name','chunk','width','height','pitch','format','bytes','offset'])assert.equal(h[field],l[field]);
 if(name!==h.name){name=h.name;const raw=readFileSync(resolve(archive.extraction,name));assert.equal(sha(raw),proof.resourceHashes[name]);const p=c.allocate(raw.length);new Uint8Array(c.memory.buffer,p,raw.length).set(raw);assert.equal(c.open(p,raw.length),1);c.release(p);}
 for(const mode of [true,false,true,false]){assert.equal(mode?c.load_high(h.chunk):c.load(h.chunk),1);const expected=(mode?highPixels:lowPixels).subarray(h.offset,h.offset+h.bytes),actual=Buffer.from(new Uint8Array(c.memory.buffer,c.data(),c.size()));assert(actual.equals(expected),`${name} chunk${h.chunk} mode${mode}`);loads++;comparedBytes+=h.bytes;}
}
const report={passed:true,completeGame:false,nativeEquivalent:false,resources:57,cases:437,loads,comparedBytes,sourceHashes:proof.sourceHashes,pixelProofSha256:sha(proofBytes),wasmSha256:sha(wasmBytes),highNativePixelsSha256:sha(highPixels),lowNativePixelsSha256:sha(lowPixels),toolSha256:sha(readFileSync(import.meta.filename)),scope:'One production TextureImage/ImageResample instance alternates PC64,PC24,PC64,PC24 for every437 shipped texture case. Exact native32 D3DX bytes test mode-keyed weight cache and prevent precision cross-contamination; no live GPU or whole game claim.'};
writeFileSync(resolve(root,'docs/porting/th14-texture-precision-cache-verified-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,loads,comparedBytes}));
