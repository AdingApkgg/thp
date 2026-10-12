import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/gpu-world-profiles');
const bytes=p=>readFileSync(resolve(root,p)),json=p=>JSON.parse(bytes(p).toString('utf8').replace(/^\uFEFF/,'')),sha=b=>createHash('sha256').update(b).digest('hex');
const native=json('artifacts/th14/gpu-world-profiles/native.json'),pixels=bytes('artifacts/th14/gpu-world-profiles/native.bgra');
assert.equal(native.vertexProcessing,'Hardware');assert.equal(native.behaviorFlags,64);assert.equal(native.cases.length,1920);assert.equal(pixels.length,1920*4096);assert.equal(sha(pixels),native.pixelsSha256);
const keys=new Set();for(const [i,c] of native.cases.entries()){
 for(const [k,max] of Object.entries({profile:4,world:2,view:1,projection:1,textureTransform:1,fog:3,range:1,point:1}))assert.ok(Number.isInteger(c[k])&&c[k]>=0&&c[k]<=max);
 const key=[c.profile,c.world,c.view,c.projection,c.textureTransform,c.fog,c.range,c.point].join('/');assert.ok(!keys.has(key));keys.add(key);assert.equal(sha(pixels.subarray(i*4096,(i+1)*4096)),c.pixelsSha256);
}
assert.equal(keys.size,1920);
for(const [file,hash] of Object.entries(native.tools))assert.equal(sha(bytes('tools/'+file)),hash);
const variants=[];
for(const name of ['control','squared','cpu-scale','cpu-exp','cpu-both','euler-base','euler-uniform','euler-reciprocal','reciprocal-uniform','euler-lerp','euler-reverse','euler-separate','euler-color','correct-lerp','correct-reverse','correct-separate','range-rsqrt','range-sqrt','linear-mad']){
 const path='artifacts/th14/gpu-world-profiles/'+name,build=json(path+'/build.json'),report=json(path+'/browser-result.json');
 assert.equal(build.name,name);assert.equal(build.diagnosticOnly,true);assert.equal(report.variant,name);assert.equal(report.completeGame,false);assert.equal(report.nativeEquivalent,false);assert.equal(report.cases,1920);
 assert.equal(build.nativeSha256,sha(bytes('artifacts/th14/gpu-world-profiles/native.json')));assert.equal(report.nativePixelsSha256,native.pixelsSha256);
 assert.equal(build.wasmSha256,sha(bytes(path+'/gpu.wasm')));assert.equal(build.loaderSha256,sha(bytes(path+'/gpu.mjs')));assert.equal(report.wasmSha256,build.wasmSha256);
 for(const [file,hash] of Object.entries(build.sources))assert.equal(sha(bytes(path+'/'+file)),hash);
 assert.equal(build.fixtureSha256,sha(bytes('runtimes/th12/th12_web/tests/cpp/th14-gpu-world-profiles-fixture.cpp')));
 assert.equal(report.groups.length,8);assert.equal(report.groups.reduce((n,g)=>n+g.cases,0),1920);assert.equal(report.groups.reduce((n,g)=>n+g.exactCases,0),report.exactCases);assert.equal(report.groups.reduce((n,g)=>n+g.differentChannels,0),report.differentChannels);assert.equal(Math.max(...report.groups.map(g=>g.maxDelta)),report.maxDelta);
 assert.equal(report.strictPixelsEqual,report.exactCases===1920&&report.differentChannels===0);
 for(const d of report.firstDifferences){const c=native.cases[d.index];for(const k of ['profile','world','view','projection','textureTransform','fog','range','point','pixelsSha256'])assert.equal(d[k],c[k]);assert.equal(pixels[d.index*4096+d.first.y*128+d.first.x*4+d.first.channel],d.first.d3d9);assert.notEqual(d.first.portable,d.first.d3d9);}
 variants.push({name,strictPixelsEqual:report.strictPixelsEqual,exactCases:report.exactCases,differentChannels:report.differentChannels,maxDelta:report.maxDelta,buildSha256:sha(bytes(path+'/build.json')),browserResultSha256:sha(bytes(path+'/browser-result.json'))});
}
const floatDiagnostics=[];
for(const flat of [false,true]){
 const path='artifacts/th14/gpu-fog-profiles'+(flat?'/flat':''),module='artifacts/th14/gpu-world-profiles/'+(flat?'float-flat':'float-fog'),n=json(path+'/native.json'),r=json(path+'/browser-result.json'),b=bytes(path+'/native.rgba32f'),build=json(module+'/build.json');
 assert.equal(n.behaviorFlags,64);assert.equal(n.cases.length,1920);assert.equal(b.length,1920*16384);assert.equal(sha(b),n.pixelsSha256);assert.equal(r.nativePixelsSha256,n.pixelsSha256);assert.equal(r.wasmSha256,sha(bytes(module+'/gpu.wasm')));assert.equal(build.wasmSha256,r.wasmSha256);
 for(const [i,c] of n.cases.entries())assert.equal(sha(b.subarray(i*16384,(i+1)*16384)),c.pixelsSha256);
 for(const [file,hash] of Object.entries(build.sources))assert.equal(sha(bytes(module+'/'+file)),hash);
 for(const [file,hash] of Object.entries(n.tools))assert.equal(sha(bytes('tools/'+file)),hash);
 for(const c of r.critical)assert.equal(b.readFloatLE(c.index*16384+(c.y*32+c.x)*16),c.native);
 floatDiagnostics.push({flatDepth:flat,nativePixelsSha256:n.pixelsSha256,wasmSha256:r.wasmSha256,browserResultSha256:sha(bytes(path+'/browser-result.json')),groups:r.groups});
}
const report={diagnosticEvidenceVerified:true,strictPixelsEqual:variants.every(v=>v.strictPixelsEqual),completeGame:false,nativeEquivalent:false,productionChanged:false,nativePixelsSha256:native.pixelsSha256,variants,floatDiagnostics,limits:'Validates physical native pixels, case coverage, diagnostic source/module bindings and observed browser results. Failing candidates remain failures; this is not a passed rendering or complete-game equivalence report.'};
report.bestCandidate=variants.find(v=>v.name==='linear-mad');
report.productionRendererMatchesBaseline=sha(bytes('runtimes/th12/portable/sdl/Renderer.cpp'))===sha(bytes('artifacts/th14/gpu-world-profiles/control/Renderer.cpp'));
report.productionChanged=!report.productionRendererMatchesBaseline;
writeFileSync(resolve(root,'docs/porting/th14-gpu-world-diagnostic-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({diagnosticEvidenceVerified:true,strictPixelsEqual:report.strictPixelsEqual,variants:variants.map(({name,exactCases,differentChannels})=>({name,exactCases,differentChannels}))},null,2));
