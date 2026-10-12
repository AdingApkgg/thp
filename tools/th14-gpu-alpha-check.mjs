import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),dir='artifacts/th14/gpu-alpha/',read=n=>readFileSync(resolve(root,n)),sha=b=>createHash('sha256').update(b).digest('hex');
const build=JSON.parse(read(dir+'build.json')),before=JSON.parse(read(dir+'browser-result-before.json')),beforeBuild=JSON.parse(read(dir+'before/build.json'));
assert.equal(build.built,true);assert.equal(sha(read(dir+'gpu.wasm')),build.wasmSha256);assert.equal(sha(read(dir+'gpu.mjs')),build.loaderSha256);
for(const [path,hash] of Object.entries(build.sources))assert.equal(sha(read(path)),hash,path);
assert.equal(before.cases,4096);assert.equal(before.exactCases,2750);assert.equal(before.strictPixelsEqual,false);assert.equal(before.wasmSha256,beforeBuild.wasmSha256);
assert.equal(sha(read(dir+'before/gpu.wasm')),beforeBuild.wasmSha256);assert.equal(sha(read(dir+'before/gpu.mjs')),beforeBuild.loaderSha256);
assert.equal(sha(read(dir+'before/Renderer.cpp')),beforeBuild.sources['runtimes/th12/portable/sdl/Renderer.cpp']);
assert.equal(sha(read(dir+'before/native.json')),beforeBuild.nativeSha256);
const oldNative=JSON.parse(read(dir+'before/native.json'));assert.equal(sha(read(dir+'before/native.bgra')),oldNative.pixelsSha256);
assert.equal(sha(read(dir+'before/th14-gpu-alpha-native.py')),oldNative.tools['th14-gpu-alpha-native.py']);
assert.deepEqual(JSON.parse(read(dir+'browser-logs.json')),[]);
const suites=[];
for(const low of [false,true]){
 const path=low?'artifacts/th14/gpu-alpha-low/':dir,native=JSON.parse(read(path+'native.json')),browser=JSON.parse(read(path+'browser-result.json')),pixels=read(path+'native.bgra');
 assert.equal(native.generated,true);assert.equal(native.lowAlpha,low);assert.equal(native.cases.length,4096);assert.equal(pixels.length,4096*4096);
 assert.equal(sha(read(path+'native.json')),low?build.nativeLowSha256:build.nativeSha256);assert.equal(sha(pixels),native.pixelsSha256);
 for(const [name,hash] of Object.entries(native.tools))assert.equal(sha(read('tools/'+name)),hash,name);
 assert.equal(browser.lowAlpha,low);assert.equal(browser.completeGame,false);assert.equal(browser.nativeEquivalent,false);
 assert.equal(browser.strictPixelsEqual,true);assert.equal(browser.cases,4096);assert.equal(browser.exactCases,4096);assert.equal(browser.maxDelta,0);assert.equal(browser.differentChannels,0);
 assert.equal(browser.nativePixelsSha256,sha(pixels));assert.equal(browser.portablePixelsSha256,sha(pixels));assert.equal(browser.wasmSha256,build.wasmSha256);assert.deepEqual(browser.firstDifferences,[]);
 assert.equal(browser.groups.length,16);for(const g of browser.groups){assert.equal(g.cases,256);assert.equal(g.exactCases,256);assert.equal(g.differentChannels,0);assert.equal(g.maxDelta,0);}
 assert.equal(browser.boundaries.length,256);assert.equal(browser.boundaries[0],0);
 for(let i=1;i<256;i++)assert.ok(browser.boundaries[i]>browser.boundaries[i-1]&&browser.boundaries[i]<=1);
 let checks=0,rendered=0;
 for(let i=0;i<4096;i++){
  const c=native.cases[i],image=pixels.subarray(i*4096,(i+1)*4096),always=pixels.subarray((c.operation*2048+1792)*4096,(c.operation*2048+1793)*4096);
  assert.equal(c.operation,Math.floor(i/2048));assert.equal(c.compare,Math.floor((i%2048)/256)+1);assert.equal(c.reference,i%256);assert.equal(sha(image),c.pixelsSha256);
  // Independently verify that original alpha-test results follow byte alpha
  // from the actual original Always output, including exact-equality cases.
  for(let j=0;j<4096;j+=4){const a=always[j+3],r=c.reference,pass=[false,a<r,a===r,a<=r,a>r,a!==r,a>=r,true][c.compare-1];assert.equal(image.readUInt32LE(j),pass?always.readUInt32LE(j):0xff42678b);checks++;}
  if(c.compare===8&&c.reference===0){for(let j=0;j<4096;j+=4)if(always.readUInt32LE(j)!==0xff42678b)rendered++;}
 }
 assert.equal(rendered,968);if(!low)assert.equal(native.pixelsSha256,oldNative.pixelsSha256,'unchanged original reference');
 if(low){assert.deepEqual([...new Set(native.texture.map(n=>n>>>24))],[0,1,2,3]);}
 suites.push({lowAlpha:low,cases:4096,pixels:4096*1024,channels:4096*4096,nativeByteCompareChecks:checks,rendererInitMs:browser.rendererInitMs,pixelsSha256:native.pixelsSha256});
}
const names=[dir+'native.json',dir+'native.bgra',dir+'build.json',dir+'gpu.wasm',dir+'gpu.mjs',dir+'browser-result.json',dir+'browser.png',dir+'browser-logs.json',dir+'browser-result-before.json',dir+'browser-before.png',dir+'before/build.json',dir+'before/gpu.wasm',dir+'before/gpu.mjs',dir+'before/Renderer.cpp',dir+'before/native.json',dir+'before/native.bgra',dir+'before/th14-gpu-alpha-native.py',dir+'browser-result-alpha-conversion.json',...['native.json','native.bgra','browser-result.json','browser.png'].map(n=>'artifacts/th14/gpu-alpha-low/'+n)];
const report={passed:true,completeGame:false,nativeEquivalent:false,strictPixelsEqual:true,cases:8192,pixels:8192*1024,channels:8192*4096,maxDelta:0,suites,before:{exactCases:2750,differentCases:1346,differentChannels:before.differentChannels,maxDelta:before.maxDelta,wasmSha256:before.wasmSha256},sources:build.sources,evidence:Object.fromEntries(names.map(n=>[n,{bytes:read(n).length,sha256:sha(read(n))}])),scope:'Actual production SDL/WebGL Renderer compared byte-for-byte against actual offscreen D3D9 HAL alpha-test images:8 compares x256 references x2 combiner operations x normal/0..3 texture alpha. Measured RGBA8 conversion boundaries are used by both generic and warmed production shaders. Original reference for the failing suite is unchanged.',limits:['Separate D3D9 fixture, not an original-game draw-loop or complete-frame capture','Current local D3D9 and WebGL devices only; other drivers, target formats, world/depth/fog/text/resampling and full TH14 1:1 remain unproved','Full game release integration is checked separately; this module is a raster diagnostic with no game simulation']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-alpha-browser-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:8192,channels:report.channels,beforeDifferentCases:1346,maxDelta:0}));
