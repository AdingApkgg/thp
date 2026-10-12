import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),dir='artifacts/th14/gpu-original-quads/',rt='runtimes/th12/th12_web/';
const read=p=>readFileSync(resolve(root,p)),sha=b=>createHash('sha256').update(b).digest('hex'),json=p=>JSON.parse(read(p));
const prepared=json(dir+'prepared.json'),native=json(dir+'native.json'),build=json(dir+'build.json'),browser=json(dir+'browser-result.json'),pixels=read(dir+'native.bgra');
const geometryPath='docs/porting/th14-gpu-original-quads-geometry-verified-oct11.json',geometry=json(geometryPath),oracle=json(dir+'geometry/native.json');
assert.equal(geometry.passed,true);assert.equal(geometry.nativeQuadCases,640);
for(const [p,h] of Object.entries(geometry.sourceHashes))assert.equal(sha(read(rt+p)),h,p);
for(const [p,h] of Object.entries(geometry.toolHashes))assert.equal(sha(read(p)),h,p);
assert.equal(sha(read(dir+'geometry/th14.wasm')),geometry.wasmSha256);
assert.equal(sha(read(dir+'geometry/native.json')),prepared.renderOracleSha256);
assert.equal(sha(read(geometryPath)),prepared.renderProofSha256);assert.equal(build.geometryProofSha256,prepared.renderProofSha256);
assert.equal(sha(read('tools/th14-gpu-original-quads-prepare.py')),prepared.prepareToolSha256);
assert.equal(native.generated,true);assert.equal(native.behaviorFlags,64);assert.equal(native.vertexProcessing,'Hardware');
assert.equal(native.width,640);assert.equal(native.height,480);assert.equal(prepared.cases.length,640);assert.equal(native.cases.length,640);
assert.equal(sha(read(dir+'prepared.json')),native.preparedSha256);assert.equal(native.materialOracleSha256,prepared.renderOracleSha256);
assert.equal(native.nativeExecutableSha256,sha(read('H:/Games/th/14/th14.exe')));assert.equal(native.nativeExecutableSha256,geometry.nativeExecutableSha256);
assert.equal(native.d3d9Sha256,sha(read('C:/Windows/System32/d3d9.dll')));
assert.equal(native.sdkHeaderSha256,sha(read('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h')));
assert.equal(native.toolSha256,sha(read('tools/th14-gpu-original-quads-native.py')));
assert.equal(pixels.length,prepared.bytes);assert.equal(sha(pixels),native.pixelsSha256);
assert.equal(build.built,true);assert.equal(sha(read(dir+'native.json')),build.nativeSha256);
assert.equal(sha(read(dir+'gpu.wasm')),build.wasmSha256);assert.equal(sha(read(dir+'gpu.mjs')),build.loaderSha256);
for(const [p,h] of Object.entries(build.sources))assert.equal(sha(read(p)),h,p);
assert.equal(browser.completeGame,false);assert.equal(browser.nativeEquivalent,false);assert.equal(browser.cases,640);assert.equal(browser.rows.length,640);
assert.equal(browser.strictPixelsEqual,true);assert.equal(browser.exactCases,640);assert.equal(browser.maxDelta,0);
assert.equal(browser.nativePixelsSha256,sha(pixels));assert.equal(browser.portablePixelsSha256,sha(pixels));assert.equal(browser.wasmSha256,build.wasmSha256);
assert.deepEqual(json(dir+'browser-logs.json'),[]);
let offset=0,submitted=0,rendered=0,foreground=0;
for(let i=0;i<640;++i){
 const p=prepared.cases[i],n=native.cases[i],b=browser.rows[i],o=oracle.quads[i];
 assert.equal(p.index,i);assert.equal(p.offset,offset);assert.equal(p.size,p.crop[2]*p.crop[3]*4);
 assert.ok(p.crop[0]>=0&&p.crop[1]>=0&&p.crop[0]+p.crop[2]<=640&&p.crop[1]+p.crop[3]<=480);
 for(const [k,v] of Object.entries(p))assert.deepEqual(n[k],v,`native ${i}/${k}`);
 for(const k of ['index','mode','colorMode','relation','tinted','visibility','sample','crop','status','drawCount'])assert.deepEqual(b[k],p[k],`browser ${i}/${k}`);
 assert.equal(p.drawCount,o.draws.length);assert.equal(p.status,o.status);
 for(const draw of o.draws)for(const v of draw){
  // Every on-screen native vertex must lie inside the unscaled crop.
  if(v[0]>=0&&v[0]<640&&v[1]>=0&&v[1]<480)assert.ok(v[0]>=p.crop[0]&&v[0]<p.crop[0]+p.crop[2]&&v[1]>=p.crop[1]&&v[1]<p.crop[1]+p.crop[3]);
 }
 const raw=pixels.subarray(offset,offset+p.size);assert.equal(sha(raw),n.pixelsSha256);assert.equal(b.pixelsSha256,n.pixelsSha256);
 assert.equal(b.differentChannels,0);assert.equal(b.maxDelta,0);assert.equal(b.first,null);
 let changed=0;for(let j=0;j<raw.length;j+=4)if(raw.readUInt32LE(j)!==0xff42678b)++changed;
 assert.equal(b.foregroundPixels,changed);if(!p.drawCount)assert.equal(changed,0);submitted+=p.drawCount;if(changed)++rendered;foreground+=changed;offset+=p.size;
}
assert.equal(offset,pixels.length);assert.equal(submitted,256);assert.equal(rendered,224);assert.equal(browser.renderedCases,rendered);assert.ok(foreground>100000);
const names=['prepared.json','native.json','native.bgra','build.json','gpu.mjs','gpu.wasm','browser-result.json','browser.png','browser-logs.json','geometry/native.json','geometry/th14.wasm'];
const report={passed:true,completeGame:false,nativeEquivalent:false,strictPixelsEqual:true,cases:640,submittedCases:submitted,renderedCases:rendered,foregroundPixels:foreground,channels:pixels.length,maxDelta:0,width:640,height:480,url:'http://127.0.0.1:8150/',debugRenderer:browser.debugRenderer,wasmSha256:build.wasmSha256,files:Object.fromEntries(names.map(n=>[dir+n,{bytes:read(dir+n).length,sha256:sha(read(dir+n))}])),sources:build.sources,limits:['Original retail draw dispatcher is executed with its batch boundary recorded; actual native batch implementation and full game draw loop are not captured','Recorded original four-corner geometry is rasterized as a D3D9 HAL hardware-vertex-processing strip; current production independently calculates six triangle vertices from the same ANM inputs and uses the unchanged production SDL/WebGL renderer','640 cases cover drawing modes 0..3, visibility, color modes, inherited transforms, tint, rotation, anchors and UV; 256 submit geometry and 224 produce on-screen foreground','Both devices use a synthetic 4x4 texture and controlled non-fog pipeline at the original 640x480 grid; crops include native bounding-box margins, without scaling','No complete original game frame, original texture/scene/text/depth/fog combination, original batch order or cross-device guarantee is asserted']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-original-quads-browser-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:640,submittedCases:submitted,renderedCases:rendered,foregroundPixels:foreground,channels:pixels.length,maxDelta:0}));
