import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),bytes=p=>readFileSync(resolve(root,p)),json=p=>JSON.parse(bytes(p).toString('utf8').replace(/^\uFEFF/,'')),sha=b=>createHash('sha256').update(b).digest('hex');
const diagnostics=[];
for(const [folder,names,count,unmodified] of [
 ['gpu-stage-float',['direct-float-before','direct-float-candidate'],7104,true],
 ['gpu-stage-coefficient',['coefficient-before','coefficient-candidate'],7104,false],
 ['gpu-stage-flat-probe',['flat-probe-before','flat-probe-candidate'],576,false],
 ['gpu-native-shader-probe/rsq-output',['flat-probe-rsq'],576,false]
]){
 const reference='artifacts/th14/'+folder+'/',n=json(reference+'native.json'),pixels=bytes(reference+'native.rgba32f');assert.equal(n.cases.length,count);assert.equal(n.behaviorFlags,64);assert.equal(n.vertexProcessing,'Hardware');assert.equal(n.outputFormat,'A32B32G32R32F');assert.equal(pixels.length,count*16384);assert.equal(sha(pixels),n.pixelsSha256);
 for(const [file,hash] of Object.entries(n.tools))assert.equal(sha(bytes('tools/'+file)),hash);
 for(const [i,c] of n.cases.entries())assert.equal(sha(pixels.subarray(i*16384,(i+1)*16384)),c.pixelsSha256);
 let foreground=0;for(let p=12;p<pixels.length;p+=16)if(pixels.readFloatLE(p)!==1)foreground++;
 for(const name of names){
  const path='artifacts/th14/gpu-stage-fog/'+name+'/',b=json(path+'build.json'),r=json(path+'browser-result.json');assert.equal(b.name,name);assert.equal(r.variant,name);assert.equal(r.cases,count);assert.equal(r.completeGame,false);assert.equal(r.nativeEquivalent,false);assert.equal(b.shaderUnmodifiedFromBase,unmodified);assert.equal(r.shaderUnmodifiedFromBase,unmodified);assert.equal(b.nativeSha256,sha(bytes(reference+'native.json')));assert.equal(r.nativePixelsSha256,n.pixelsSha256);
  for(const [file,hash] of Object.entries(b.sources))assert.equal(sha(bytes(path+file)),hash);
  assert.equal(b.shaderSha256,sha(bytes(path+'Shaders.hpp')));assert.equal(r.shaderSha256,b.shaderSha256);assert.equal(b.loaderSha256,sha(bytes(path+'gpu.mjs')));assert.equal(b.wasmSha256,sha(bytes(path+'gpu.wasm')));assert.equal(r.wasmSha256,b.wasmSha256);
  const fixture=name==='flat-probe-rsq'||name.startsWith('flat-probe-')?'th14-gpu-stage-flat-float-fixture.cpp':'th14-gpu-stage-direct-float-fixture.cpp';assert.equal(b.fixtureSha256,sha(bytes('runtimes/th12/th12_web/tests/cpp/'+fixture)));
  const vertexFixture=fixture.includes('flat')?'th14-gpu-stage-flat-probe-fixture.cpp':'th14-gpu-stage-fog-fixture.cpp';assert.equal(b.profileFixtureSha256,sha(bytes('runtimes/th12/th12_web/tests/cpp/'+vertexFixture)));
  if(unmodified)assert.equal(b.shaderSha256,sha(bytes('artifacts/th14/gpu-stage-fog/'+b.base+'/Shaders.hpp')));
  for(const g of r.groups){assert.equal(g.compared,foreground);assert.ok(g.differentFloats>=0&&g.differentFloats<=foreground);assert.ok(Number.isFinite(g.maxDelta));}
  for(const p of r.critical)for(let ch=0;ch<4;ch++)assert.equal(p.native[ch],pixels.readFloatLE(p.index*16384+(p.y*32+p.x)*16+ch*4));
  diagnostics.push({name,cases:count,comparedForegroundPixels:foreground,shaderUnmodifiedFromBase:unmodified,groups:r.groups,critical:r.critical,webglRenderer:r.webglRenderer,buildSha256:sha(bytes(path+'build.json')),browserResultSha256:sha(bytes(path+'browser-result.json'))});
 }
}
const flat=json('artifacts/th14/gpu-stage-flat-probe/native.json'),fixed=bytes('artifacts/th14/gpu-stage-flat-probe/native.rgba32f'),instructionModels=[];
for(const mode of ['rsq-rcp-mad','rsq-mul-mad','rsq-rcp-sub','rsq-rcp-divide-end','rsq-output','rcp-output']){
 const path='artifacts/th14/gpu-native-shader-probe/'+mode+'/',n=json(path+'native.json'),pixels=bytes(path+'native.rgba32f');assert.equal(n.diagnosticMode,mode);assert.equal(n.cases.length,576);assert.equal(sha(pixels),n.pixelsSha256);assert.equal(n.shaderSha256,sha(bytes(path+'probe.vso')));assert.equal(n.shaderAssemblySha256,sha(bytes(path+'probe.asm')));
 for(const [file,hash] of Object.entries(n.tools))assert.equal(sha(bytes('tools/'+file)),hash);
 for(const [i,c] of n.cases.entries())assert.equal(sha(pixels.subarray(i*16384,(i+1)*16384)),c.pixelsSha256);
 if(mode.endsWith('output'))continue;
 let compared=0,differentFloats=0,maxDelta=0,exactCases=0,cases=0;
 for(const [i,c] of flat.cases.entries()){
  if(c.fog!==3||c.range!==1)continue;cases++;let diff=0;
  for(let j=0;j<1024;j++){const p=i*16384+j*16;if(fixed.readFloatLE(p+12)===1)continue;compared++;const delta=Math.abs(fixed.readFloatLE(p)-pixels.readFloatLE(p));if(delta){diff++;maxDelta=Math.max(maxDelta,delta);}}
  differentFloats+=diff;if(!diff)exactCases++;
 }
 instructionModels.push({mode,cases,exactCases,compared,differentFloats,maxDelta,nativePixelsSha256:n.pixelsSha256});
}
const scalarPath='artifacts/th14/gpu-native-shader-probe/rcp-scalar/',s=json(scalarPath+'native.json'),scalar=bytes(scalarPath+'native.rgba32f');assert.equal(s.cases.length,1025);assert.equal(sha(scalar),s.pixelsSha256);assert.equal(s.shaderSha256,sha(bytes(scalarPath+'probe.vso')));assert.equal(s.shaderAssemblySha256,sha(bytes(scalarPath+'probe.asm')));
for(const [file,hash] of Object.entries(s.tools))assert.equal(sha(bytes('tools/'+file)),hash);
const floatBits=n=>{const b=Buffer.alloc(4);b.writeFloatLE(n);return b.readUInt32LE();},ulpCounts={};
for(const [i,c] of s.cases.entries()){
 assert.equal(c.scalarIndex,i);assert.equal(floatBits(c.scalar),0x3f800000+i*8192);assert.equal(sha(scalar.subarray(i*16384,(i+1)*16384)),c.pixelsSha256);
 const offset=i*16384+(16*32+16)*16,delta=scalar.readUInt32LE(offset)-floatBits(1/c.scalar);ulpCounts[delta]=(ulpCounts[delta]||0)+1;
 // Every drawn pixel is a constant scalar probe, not an interpolated reciprocal.
 for(let j=0;j<1024;j++){const p=i*16384+j*16;if(scalar.readFloatLE(p+12)!==1)assert.equal(scalar.readUInt32LE(p),scalar.readUInt32LE(offset));}
}
assert.deepEqual(ulpCounts,{'0':895,'1':90,'-1':40});
const q=bytes('artifacts/th14/gpu-native-shader-probe/rsq-output/native.rgba32f'),rcp=bytes('artifacts/th14/gpu-native-shader-probe/rcp-output/native.rgba32f'),offset=15*16384+(10*32+25)*16,constantRcp={index:15,profile:11,x:25,y:10,rsq:q.readFloatLE(offset),nativeRcp:rcp.readFloatLE(offset)*1024,ieeeFloat32Rcp:Math.fround(1/q.readFloatLE(offset)),limits:'Constant-distance geometry only; reciprocal of an interpolated RSQ is not the interpolation of reciprocal vertex values.'};
assert.equal(constantRcp.nativeRcp,226.38461303710938);assert.equal(constantRcp.ieeeFloat32Rcp,226.38462829589844);
const report={diagnosticEvidenceVerified:true,completeGame:false,nativeEquivalent:false,productionChanged:false,diagnostics,instructionModels,scalarReciprocal:{cases:1025,inputInterval:[1,2],ulpCounts,nativePixelsSha256:s.pixelsSha256},constantRcp,limits:'Pins native float pixels, shader assemblies, modules, source and visible browser observations. Independently authored arithmetic shaders are diagnostic hypotheses, not the native fixed-function shader capture. Native reciprocal errors have both signs; a fixed ULP bias or bit mask is unsupported. Does not prove complete native rendering or all-game equivalence.'};
assert.equal(sha(bytes('runtimes/th12/portable/sdl/Renderer.cpp')),sha(bytes('artifacts/th14/gpu-stage-fog/before/Renderer.cpp')));
writeFileSync(resolve(root,'docs/porting/th14-gpu-stage-float-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({diagnosticEvidenceVerified:true,diagnostics:diagnostics.length,instructionModels,scalarUlpCounts:ulpCounts,constantRcp},null,2));
