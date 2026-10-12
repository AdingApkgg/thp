import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out='artifacts/th14/gpu-alpha-depth',read=n=>readFileSync(resolve(root,n)),sha=b=>createHash('sha256').update(b).digest('hex');
const native=JSON.parse(read(out+'/native.json')),build=JSON.parse(read(out+'/build.json')),browser=JSON.parse(read(out+'/browser-result.json')),pixels=read(out+'/native.bgra');
assert.equal(native.generated,true);assert.equal(native.cases.length,2560);assert.equal(pixels.length,2560*4096);assert.equal(sha(pixels),native.pixelsSha256);
assert.equal(native.materialOracleSha256,sha(read('artifacts/th14/render-native.json')));assert.equal(native.nativeExecutableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [name,hash] of Object.entries(native.tools))assert.equal(sha(read('tools/'+name)),hash,name);for(const [name,hash] of Object.entries(build.sources))assert.equal(sha(read(name)),hash,name);
assert.equal(sha(read(out+'/gpu.wasm')),build.wasmSha256);assert.equal(sha(read(out+'/gpu.mjs')),build.loaderSha256);assert.equal(sha(read(out+'/native.json')),build.nativeSha256);
const coverage=new Set(),images=new Set(),byKey=new Map();let occluding=0,flat=0;
const float=new Float32Array(1),bits=new Uint32Array(float.buffer);float[0]=.6;const backZ=float[0],middle=bits[0];const zs=[.25,backZ];bits[0]=middle-1;zs.push(float[0]);bits[0]=middle+1;zs.push(float[0]);zs.push(.75);
for(let i=0;i<native.cases.length;i++){const c=native.cases[i],image=pixels.subarray(i*4096,(i+1)*4096);assert.equal(sha(image),c.pixelsSha256);assert.ok(c.format===0||c.format===1);assert.ok(c.low===0||c.low===1);assert.ok(c.point===0||c.point===1);assert.ok(c.write===0||c.write===1);assert.ok(c.compare>=1&&c.compare<=8);assert.ok([0,1,2,128].includes(c.reference));assert.equal(c.z,zs[c.depth]);assert.equal(c.backZ,backZ);
 const key=[c.format,c.compare,c.write,c.depth,c.reference,c.low,c.point].join('/');assert.ok(!coverage.has(key));coverage.add(key);byKey.set(key,{c,image});images.add(c.pixelsSha256);
 let changed=0;for(let p=0;p<image.length;p+=4)if(image.readUInt32LE(p)!==0xffdda336)changed++;if(changed)occluding++;else flat++;
 // An opaque later layer must cover the whole target when the first layer
 // cannot write depth or when its alpha can never pass the threshold.
 if(!c.write||c.compare===1||(c.low&&c.reference===128))assert.equal(changed,0,'No surviving depth writes must leave the later layer visible');
}
assert.equal(coverage.size,2560);assert.ok(images.size>5);assert.ok(occluding>100);assert.ok(flat>1000);
let selectiveDiscardPairs=0;
for(const {c,image} of byKey.values())if(c.write&&c.depth===0&&c.reference===0&&[2,4,6,8].includes(c.compare)){
 const other=byKey.get([c.format,c.compare,c.write,c.depth,128,c.low,c.point].join('/'));assert.ok(other);if(!image.equals(other.image))selectiveDiscardPairs++;
}
assert.ok(selectiveDiscardPairs>=16,'Changing alpha threshold must change actual occlusion');
assert.equal(browser.strictPixelsEqual,true);assert.equal(browser.cases,2560);assert.equal(browser.exactCases,2560);assert.equal(browser.maxDelta,0);assert.equal(browser.differentChannels,0);assert.equal(browser.nativePixelsSha256,native.pixelsSha256);assert.equal(browser.portablePixelsSha256,native.pixelsSha256);assert.equal(browser.wasmSha256,build.wasmSha256);assert.deepEqual(browser.firstDifferences,[]);
assert.equal(browser.groups.length,16);for(let i=0;i<16;i++)assert.deepEqual(browser.groups[i],{format:Math.floor(i/8),compare:i%8+1,cases:160,exactCases:160,differentChannels:0,maxDelta:0});assert.deepEqual(JSON.parse(read(out+'/browser-logs.json')),[]);
const files=['native.json','native.bgra','build.json','gpu.mjs','gpu.wasm','browser-result.json','browser.png','browser-logs.json'].map(n=>out+'/'+n).concat(Object.keys(build.sources),Object.keys(native.tools).map(n=>'tools/'+n),['tools/th14-gpu-alpha-depth-check.mjs','artifacts/th14/render-native.json']);
const evidence=Object.fromEntries([...new Set(files)].map(path=>{const b=read(path);return [path,{bytes:b.length,sha256:sha(b)}];}));
const report={passed:true,completeGame:false,nativeEquivalent:false,cases:2560,exactCases:2560,comparedChannels:pixels.length,differentChannels:0,maxDelta:0,distinctNativeImages:images.size,occludingNativeCases:occluding,flatNativeCases:flat,selectiveDiscardPairs,coverage:{depthFormats:['D16','D24S8'],depthCompareFunctions:8,depthWriteStates:2,frontDepths:zs,backDepth:backZ,alphaReferences:[0,1,2,128],alphaRanges:2,filters:2},nativePixelsSha256:native.pixelsSha256,wasmSha256:build.wasmSha256,evidence,scope:'Actual D3D9 HAL versus production SDL/WebGL: alpha-tested blended foreground with optional depth write, then opaque later layer; checks discarded fragments do not occlude',limits:['Uniform per-quad screen-space depth; no world-space perspective or arbitrary depth gradients','No original-game GPU draw-loop/full-frame capture or cross-device guarantee','TH14 1:1 and all unconverted works remain incomplete']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-alpha-depth-browser-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:2560,comparedChannels:pixels.length,distinctNativeImages:images.size,occludingNativeCases:occluding,selectiveDiscardPairs}));
