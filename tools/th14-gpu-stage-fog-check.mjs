import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),base='artifacts/th14/gpu-stage-fog/';
const bytes=p=>readFileSync(resolve(root,p)),json=p=>JSON.parse(bytes(p).toString('utf8').replace(/^\uFEFF/,'')),sha=b=>createHash('sha256').update(b).digest('hex');
const profiles=json(base+'profiles.json'),native=json(base+'native.json'),pixels=bytes(base+'native.bgra');
assert.equal(profiles.profiles.length,37);assert.equal(profiles.commands.length,170);assert.equal(Object.keys(profiles.sources).length,7);
for(const [path,hash] of Object.entries(profiles.sources))assert.equal(sha(bytes(path)),hash);
for(const c of profiles.commands){assert.ok(c.stage>=1&&c.stage<=7);assert.ok([8,9].includes(c.opcode));const path=Object.keys(profiles.sources).find(p=>p.endsWith(`st0${c.stage}.std`)),b=bytes(path),offset=c.offset+8+(c.opcode===9?8:0),p=profiles.profiles[c.profile];assert.equal(b.readInt32LE(c.offset),c.time);assert.equal(b.readInt16LE(c.offset+4),c.opcode);assert.equal(b.readUInt32LE(offset),p.color);assert.equal(b.readFloatLE(offset+4),p.near);assert.equal(b.readFloatLE(offset+8),p.far);}
assert.equal(native.vertexProcessing,'Hardware');assert.equal(native.behaviorFlags,64);assert.equal(native.cases.length,7104);assert.equal(pixels.length,7104*4096);assert.equal(sha(pixels),native.pixelsSha256);assert.equal(native.profilesSha256,sha(bytes(base+'profiles.json')));
for(const [file,hash] of Object.entries(native.tools))assert.equal(sha(bytes('tools/'+file)),hash);
const keys=new Set();
for(const [i,c] of native.cases.entries()){
 for(const [k,max] of Object.entries({profile:36,world:2,view:1,projection:1,textureTransform:1,range:1,point:1}))assert.ok(Number.isInteger(c[k])&&c[k]>=0&&c[k]<=max);
 assert.ok([0,3].includes(c.fog));const key=[c.profile,c.world,c.view,c.projection,c.textureTransform,c.fog,c.range,c.point].join('/');assert.ok(!keys.has(key));keys.add(key);
 assert.equal(sha(pixels.subarray(i*4096,(i+1)*4096)),c.pixelsSha256);const p=profiles.profiles[c.profile];for(const k of ['near','far','density','color','scale'])assert.equal(c[k],p[k]);
}
assert.equal(keys.size,7104);
const variants=[];
for(const name of ['before','candidate','rsqrt','negative','cpu','rcp-uniform','rcp-barrier']){
 const path=base+name+'/',b=json(path+'build.json'),r=json(path+'browser-result.json');
 assert.equal(b.name,name);assert.equal(b.diagnosticOnly,true);assert.equal(r.variant,name);assert.equal(r.diagnosticOnly,true);assert.equal(r.completeGame,false);assert.equal(r.nativeEquivalent,false);assert.equal(r.cases,7104);assert.equal(b.nativeSha256,sha(bytes(base+'native.json')));assert.equal(b.profilesSha256,sha(bytes(base+'profiles.json')));assert.equal(r.nativePixelsSha256,native.pixelsSha256);
 for(const [file,hash] of Object.entries(b.sources))assert.equal(sha(bytes(path+file)),hash);
 assert.equal(b.fixtureSha256,sha(bytes('runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-fog-fixture.cpp')));assert.equal(b.wasmSha256,sha(bytes(path+'gpu.wasm')));assert.equal(b.loaderSha256,sha(bytes(path+'gpu.mjs')));assert.equal(r.wasmSha256,b.wasmSha256);
 assert.equal(r.groups.length,4);for(const g of r.groups)assert.equal(g.cases,1776);assert.equal(r.groups.reduce((sum,g)=>sum+g.exactCases,0),r.exactCases);assert.equal(r.groups.reduce((sum,g)=>sum+g.differentChannels,0),r.differentChannels);assert.equal(Math.max(...r.groups.map(g=>g.maxDelta)),r.maxDelta);assert.equal(r.strictPixelsEqual,r.exactCases===7104&&r.differentChannels===0);
 assert.equal(r.firstDifferences.length,7104-r.exactCases);for(const d of r.firstDifferences){const c=native.cases[d.index];for(const k of Object.keys(c))assert.equal(d[k],c[k]);assert.equal(pixels[d.index*4096+d.first.y*128+d.first.x*4+d.first.channel],d.first.d3d9);assert.notEqual(d.first.portable,d.first.d3d9);}
 variants.push({name,exactCases:r.exactCases,differentChannels:r.differentChannels,maxDelta:r.maxDelta,strictPixelsEqual:r.strictPixelsEqual,buildSha256:sha(bytes(path+'build.json')),browserResultSha256:sha(bytes(path+'browser-result.json')),remainingCases:r.firstDifferences.map(d=>d.index)});
}
const report={diagnosticEvidenceVerified:true,completeGame:false,nativeEquivalent:false,strictPixelsEqual:variants.every(v=>v.strictPixelsEqual),productionChanged:false,originalStageFiles:7,originalFogCommands:170,uniqueFogEndpoints:37,cases:7104,nativePixelsSha256:native.pixelsSha256,variants,limits:'Checks independent scaled geometry using original STD endpoints, physical D3D9 pixels, complete case coverage and browser module/source bindings. This does not capture the native game draw loop or every fog interpolation frame. Failed candidates remain failed.'};
assert.equal(sha(bytes('runtimes/th12/portable/sdl/Renderer.cpp')),sha(bytes(base+'before/Renderer.cpp')));
writeFileSync(resolve(root,'docs/porting/th14-gpu-stage-fog-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
