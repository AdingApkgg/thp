import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),dir='artifacts/th14/gpu-raster/';
const read=n=>readFileSync(resolve(root,n)),sha=b=>createHash('sha256').update(b).digest('hex');
const native=JSON.parse(read(dir+'native.json')),build=JSON.parse(read(dir+'build.json')),browser=JSON.parse(read(dir+'browser-result.json')),pixels=read(dir+'native.bgra');
assert.equal(native.generated,true);assert.equal(build.built,true);
assert.equal(native.nativeExecutableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
assert.equal(native.cases.length,192);assert.equal(pixels.length,192*32*32*4);
assert.equal(sha(pixels),native.pixelsSha256);assert.equal(sha(read(dir+'native.json')),build.nativeSha256);
assert.equal(sha(read(dir+'gpu.wasm')),build.wasmSha256);assert.equal(sha(read(dir+'gpu.mjs')),build.loaderSha256);
for(const [path,hash] of Object.entries(build.sources))assert.equal(sha(read(path)),hash,path);
assert.equal(sha(read('tools/th14-gpu-raster-native.py')),native.toolSha256);
assert.equal(sha(read('artifacts/th14/render-native.json')),native.materialOracleSha256);
assert.equal(browser.completeGame,false);assert.equal(browser.nativeEquivalent,false);
assert.equal(browser.cases,192);assert.equal(browser.exactCases,192);assert.equal(browser.maxDelta,0);assert.equal(browser.strictPixelsEqual,true);
assert.equal(browser.nativePixelsSha256,sha(pixels));assert.equal(browser.portablePixelsSha256,sha(pixels));assert.equal(browser.wasmSha256,build.wasmSha256);
assert.equal(browser.rows.length,192);assert.deepEqual(JSON.parse(read(dir+'browser-logs.json')),[]);
// Reject an apparently successful test which only compared untouched clear pixels.
const changed=[];
for(let i=0;i<192;i++){
 const c=native.cases[i],b=browser.rows[i],p=pixels.subarray(i*4096,(i+1)*4096);
 assert.equal(sha(p),c.pixelsSha256);assert.equal(b.index,i);
 for(const k of ['blend','point','address','offset'])assert.equal(b[k],c[k]);
 assert.equal(b.differentChannels,0);assert.equal(b.maxDelta,0);assert.equal(b.first,null);
 let count=0;for(let j=0;j<p.length;j+=4)if(p.readUInt32LE(j)!==0xff42678b)++count;
 assert.ok(count>100,`case ${i} must actually render the quad`);changed.push(count);
 assert.equal(p.readUInt32LE(0),0xff42678b);
}
const unique=new Set(native.cases.map(c=>c.pixelsSha256)).size;assert.ok(unique>=50,`distinct rendered cases: ${unique}`);
const names=['native.json','native.bgra','build.json','gpu.mjs','gpu.wasm','browser-result.json','browser.png','browser-logs.json'];
const report={passed:true,completeGame:false,nativeEquivalent:false,strictPixelsEqual:true,cases:192,pixels:192*1024,channels:192*4096,maxDelta:0,distinctImages:unique,renderedPixelsRange:[Math.min(...changed),Math.max(...changed)],url:'http://127.0.0.1:8136/',wasmSha256:build.wasmSha256,files:Object.fromEntries(names.map(n=>[dir+n,{bytes:read(dir+n).length,sha256:sha(read(dir+n))}])),sources:build.sources,limits:['Actual original-game D3D9 material values are drawn by a separate offscreen D3D9 HAL fixture; the original game draw loop is not captured','Portable pixels come from the actual unchanged production SDL/WebGL Renderer and shaders, not a CPU rasterizer','Coverage: sixteen blend selectors, point/linear filters, repeat/clamp/mirror addresses, two subpixel positions, four corner colors and a 4x4 texture','No alpha-test, depth, world transform, fog, text, resampling, complete game frame or other GPU/driver guarantee','Browser result is saved from the visible diagnostic page; all source, native reference and module hashes are checked']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-raster-browser-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:192,channels:report.channels,distinctImages:unique,renderedPixelsRange:report.renderedPixelsRange,maxDelta:0}));
