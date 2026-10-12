import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),base='artifacts/th14/stage-gpu-stream-replay/',evidence={},sha=b=>createHash('sha256').update(b).digest('hex'),track=p=>{const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;},json=p=>JSON.parse(track(p));
const original=json(base+'native.json'),before=json(base+'build.json'),variants=[];
for(const name of ['sequential-eye','cpu-float-eye','cpu-double-eye','no-fog','no-depth']){
 const prefix=base+'variants/'+name+'/',build=json(prefix+'build.json'),report=json(prefix+'browser-result.json');assert.equal(build.name,name);assert.equal(report.variant,name);assert.equal(report.backendVersion,10);assert.equal(report.frames,21);assert.equal(report.strictPixelsEqual,false);
 assert.equal(build.baseBuildSha256,evidence[base+'build.json'].sha256);assert.equal(build.toolSha256,sha(track('tools/th14-stage-gpu-stream-transform-build.mjs')));for(const [p,h] of Object.entries(build.sources))assert.equal(sha(track(prefix+p)),h);assert.equal(build.wasmSha256,sha(track(prefix+'gpu.wasm')));assert.equal(build.loaderSha256,sha(track(prefix+'gpu.mjs')));assert.equal(report.wasmSha256,build.wasmSha256);
 let native=original,nativePixels;
 if(['no-fog','no-depth'].includes(name)){
  native=json(prefix+'native.json');nativePixels=track(prefix+'native.bgra');assert.equal(native.variant,name);assert.equal(native.pixelsSha256,sha(nativePixels));assert.equal(native.toolSha256,sha(track('tools/th14-stage-gpu-stream-'+name+'-hal.py')));assert.equal(native.generatorSha256,sha(track('tools/th14-stage-gpu-stream-isolate-native.py')));assert.equal(native.baseSourceSha256,sha(track('tools/th14-stage-gpu-stream-hal.py')));
 }else nativePixels=track(base+'native.bgra');
 assert.equal(report.nativePixelsSha256,native.pixelsSha256);assert.equal(native.frames.length,21);
 let exact=0,different=0,maxDelta=0;
 for(let i=0;i<21;i++){
  const r=report.reports[i],n=native.frames[i];assert.deepEqual([r.stage,r.frame],[n.stage,n.frame]);assert.equal(r.nativeSha256,n.sha256);assert.equal(r.directDraws,n.directDraws);assert.equal(r.controlledScreenQuadsExcluded,0);
  const bytes=nativePixels.subarray(n.offset,n.offset+n.bytes);assert.equal(sha(bytes),n.sha256);for(const d of r.first){const j=(d.y*640+d.x)*4+d.channel;assert.equal(bytes[j],d.d3d9);assert.notEqual(d.portable,d.d3d9);}if(!r.differentChannels){exact++;assert.equal(r.portableSha256,r.nativeSha256);}different+=r.differentChannels;maxDelta=Math.max(maxDelta,r.maxDelta);
 }
 assert.equal(exact,report.exactFrames);assert.equal(different,report.differentChannels);assert.equal(maxDelta,report.maxDelta);
 variants.push({name,exactFrames:exact,differentChannels:different,maxDelta,strictPixelsEqual:false});
}
assert.deepEqual(variants.map(v=>v.differentChannels),[12314,2612,6129,10436,3158]);
const release=json('runtimes/th14/th14_web/artifacts/sdl3-release/build.json');assert.equal(sha(track('runtimes/th12/portable/sdl/Renderer.cpp')),release.sources['portable/sdl/Renderer.cpp']);assert.equal(sha(track('runtimes/th12/portable/sdl/Shaders.hpp')),before.sources['runtimes/th12/portable/sdl/Shaders.hpp']);
const report={diagnosticEvidenceVerified:true,strictPixelsEqual:false,productionChanged:false,completeGame:false,nativeEquivalent:false,variants,evidence,toolSha256:sha(readFileSync(import.meta.filename)),limits:'Five separate physical browser executions; each candidate remains a failure. The two state overrides have separately generated hidden HAL pixel references and are not game behavior. Candidate browser per-frame summaries, hashes and first32 differing channels are preserved; full candidate WebGL buffers have not been independently archived. Native reference bytes and all saved first differences are independently checked. Original production buffer has a separate byte-for-byte evidence checker. No successful matrix repair, entire game, or native process framebuffer claim.'};
writeFileSync(resolve(root,'docs/porting/th14-stage-gpu-stream-variants-observed-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({diagnosticEvidenceVerified:true,strictPixelsEqual:false,variants}));
