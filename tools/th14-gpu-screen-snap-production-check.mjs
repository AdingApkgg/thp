import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(resolve(root,p)),sha=b=>createHash('sha256').update(b).digest('hex'),json=p=>JSON.parse(read(p));
const out='artifacts/th14/gpu-screen-snap-production',archive='artifacts/th14/screen-snap-baseline',manifest=json(archive+'/manifest.json');
for(const [p,r] of Object.entries(manifest.files)){const b=read(archive+'/'+p);assert.equal(b.length,r.bytes);assert.equal(sha(b),r.sha256);}
const diagnosticPath='docs/porting/th14-gpu-screen-snap-diagnostic-observed-oct11.json',diagnostic=json(diagnosticPath);assert.equal(diagnostic.diagnosticEvidenceVerified,true);
for(const [p,r] of Object.entries(diagnostic.evidence)){const b=read(manifest.files[p]?archive+'/'+p:p);assert.equal(b.length,r.bytes);assert.equal(sha(b),r.sha256,'historical diagnostic '+p);}
assert.equal(diagnostic.productionRendererAtEvidenceSha256,manifest.files['runtimes/th12/portable/sdl/Renderer.cpp'].sha256);
const renderer=read('runtimes/th12/portable/sdl/Renderer.cpp').toString('utf8');assert.match(renderer,/#if defined\(PORT_TITLE\) && PORT_TITLE == 14/);assert.match(renderer,/roundEven\(\(position.xy-viewport.xy\)\*256.0\)/);
assert.equal(sha(read('runtimes/th12/portable/sdl/Shaders.hpp')),manifest.files['runtimes/th12/portable/sdl/Shaders.hpp'].sha256);
const suiteSpecs={shapes:['gpu-original-shapes',810],quads:['gpu-original-quads',640],grid:['gpu-screen-grid',720],raster:['gpu-raster',192],alpha:['gpu-alpha',4096],'alpha-blend':['gpu-alpha-blend',7168],'alpha-depth':['gpu-alpha-depth',2560]};
const suites=[],evidence={};const track=p=>{const b=read(p);evidence[p]={bytes:b.length,sha256:sha(b)};return b;};let cases=0,channels=0;
for(const [suite,[ref,count]] of Object.entries(suiteSpecs)){
 const p=out+'/'+suite,reference='artifacts/th14/'+ref,build=JSON.parse(track(p+'/build.json')),native=JSON.parse(track(reference+'/native.json')),pixels=track(reference+'/native.bgra'),browser=JSON.parse(track(p+'/browser-result.json'));
 assert.equal(build.built,true);assert.equal(build.title,14);assert.equal(build.usesCurrentProductionRenderer,true);assert.ok(build.flags.includes('-DPORT_TITLE=14'));
 assert.equal(sha(track(p+'/gpu.wasm')),build.wasmSha256);assert.equal(sha(track(p+'/gpu.mjs')),build.loaderSha256);assert.equal(sha(read(reference+'/native.json')),build.nativeSha256);
 for(const [f,h] of Object.entries(build.sources))assert.equal(sha(track(f)),h,f);
 assert.equal(native.cases.length,count);assert.equal(sha(pixels),native.pixelsSha256);assert.equal(browser.cases,count);assert.equal(browser.exactCases,count);assert.equal(browser.strictPixelsEqual,true);assert.equal(browser.maxDelta,0);assert.equal(browser.completeGame,false);assert.equal(browser.nativeEquivalent,false);
 assert.equal(browser.nativePixelsSha256,native.pixelsSha256);assert.equal(browser.portablePixelsSha256,native.pixelsSha256);assert.equal(browser.wasmSha256,build.wasmSha256);assert.deepEqual(JSON.parse(track(p+'/browser-logs.json')),[]);track(p+'/browser.png');
 const fixed=pixels.length/count;let drawn=0;
 for(const [i,c] of native.cases.entries()){
  const raw=pixels.subarray(c.size!==undefined?c.offset:i*fixed,c.size!==undefined?c.offset+c.size:(i+1)*fixed);assert.equal(sha(raw),c.pixelsSha256);
  let foreground=0;for(let j=0;j<raw.length;j+=4)if(raw.readUInt32LE(j)!==0xff42678b)++foreground;if(foreground)++drawn;
  if(browser.rows){const r=browser.rows[i];assert.equal(r.index,i);assert.equal(r.differentChannels,0);assert.equal(r.maxDelta,0);assert.equal(r.first,null);if(c.crop){assert.deepEqual(r.crop,c.crop);assert.equal(r.status,c.status);assert.equal(r.drawCount,c.drawCount);assert.equal(r.foregroundPixels,foreground);assert.equal(r.pixelsSha256,c.pixelsSha256);}}
 }
 assert.ok(drawn>0);if(browser.groups)for(const g of browser.groups){assert.equal(g.exactCases,g.cases);assert.equal(g.differentChannels,0);assert.equal(g.maxDelta,0);}
 cases+=count;channels+=pixels.length;suites.push({suite,cases:count,comparedChannels:pixels.length,nonemptyNativeCases:drawn,strictPixelsEqual:true,wasmSha256:build.wasmSha256});
 if(suite==='alpha'){
  const lref='artifacts/th14/gpu-alpha-low',low=JSON.parse(track(lref+'/native.json')),lp=track(lref+'/native.bgra'),lb=JSON.parse(track(p+'/browser-low-result.json'));
  assert.equal(build.nativeLowSha256,sha(read(lref+'/native.json')));assert.equal(sha(lp),low.pixelsSha256);assert.equal(lb.lowAlpha,true);assert.equal(lb.cases,4096);assert.equal(lb.exactCases,4096);assert.equal(lb.strictPixelsEqual,true);assert.equal(lb.maxDelta,0);assert.equal(lb.wasmSha256,build.wasmSha256);assert.equal(lb.nativePixelsSha256,low.pixelsSha256);assert.equal(lb.portablePixelsSha256,low.pixelsSha256);track(p+'/browser-low.png');cases+=4096;channels+=lp.length;suites.push({suite:'alpha-low',cases:4096,comparedChannels:lp.length,strictPixelsEqual:true,wasmSha256:build.wasmSha256});
 }
}
assert.equal(cases,20282);
track('tools/th14-gpu-screen-snap-production-build.mjs');track('tools/th14-gpu-screen-snap-production-serve.mjs');track('tools/th14-gpu-screen-snap-production-check.mjs');track(diagnosticPath);track(archive+'/manifest.json');
const report={passed:true,completeGame:false,nativeEquivalent:false,title:14,productionChange:'Snap transformed screen coordinates to the measured 8-bit subpixel grid using round-to-even before clip-space conversion; compile-time limited to PORT_TITLE=14',strictPixelsEqual:true,cases,comparedChannels:channels,suites,historicalBaselineManifest:archive+'/manifest.json',diagnosticProof:diagnosticPath,evidence,limits:['Actual current production renderer and production geometry fixtures are compiled with PORT_TITLE=14 and drawn in the real browser; these remain independent controlled GPU fixtures','810 native-recorded shapes and640 quads,720 derived subpixel/reciprocal-W cases and18112 alpha/blend/depth/sampler cases; some original recorded quads are intentionally culled or outside the viewport','Native full batch loop, full game frames, text, combined scene/fog/texture ordering and other GPU/driver equivalence remain unproved','Separate unblended float candidate comparison establishes foreground interpolation only; its full clear-pixel RGBA32F hashes remain different','Other titles retain the previous vertex shader; this is not a completed TH14 or multi-game port']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-screen-snap-production-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,title:14,cases,comparedChannels:channels,suites:suites.length}));
