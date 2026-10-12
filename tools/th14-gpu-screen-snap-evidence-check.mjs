import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),read=p=>readFileSync(resolve(root,p)),sha=b=>createHash('sha256').update(b).digest('hex'),json=p=>JSON.parse(read(p)),evidence=new Map();
const track=p=>{const b=read(p);evidence.set(p,{bytes:b.length,sha256:sha(b)});return b;};
function build(path,sourceRoot){
 const b=JSON.parse(track(path+'/build.json'));
 assert.equal(sha(track(path+'/gpu.wasm')),b.wasmSha256);assert.equal(sha(track(path+'/gpu.mjs')),b.loaderSha256);
 for(const [p,h] of Object.entries(b.sources)){const full=p.includes('/')?p:sourceRoot+'/'+p;assert.equal(sha(track(full)),h,full);}
 for(const [p,h] of Object.entries(b.fixtureSources||{}))assert.equal(sha(track(p)),h,p);
 return b;
}
function reference(path,filename='native.bgra'){
 const n=JSON.parse(track(path+'/native.json')),pixels=track(path+'/'+filename);
 assert.equal(sha(pixels),n.pixelsSha256);if(n.nativeExecutableSha256)assert.equal(n.nativeExecutableSha256,sha(track('H:/Games/th/14/th14.exe')));
 assert.equal(n.d3d9Sha256,sha(track('C:/Windows/System32/d3d9.dll')));
 if(n.toolSha256){const name=path==='artifacts/th14/gpu-original-shapes/float'?'tools/th14-gpu-original-shapes-float-native.py':path==='artifacts/th14/gpu-screen-grid'?'tools/th14-gpu-screen-grid-native.py':path==='artifacts/th14/gpu-raster'?'tools/th14-gpu-raster-native.py':'tools/th14-gpu-original-shapes-native.py';assert.equal(sha(track(name)),n.toolSha256);}
 else for(const [p,h] of Object.entries(n.tools))assert.equal(sha(track('tools/'+p)),h,p);
 const size=pixels.length/n.cases.length;
 for(const [i,c] of n.cases.entries()){const start=c.size!==undefined?c.offset:i*size,length=c.size??size;assert.equal(sha(pixels.subarray(start,start+length)),c.pixelsSha256);}
 return {n,pixels};
}
function browser(path,b,n){
 const r=JSON.parse(track(path+'/browser-result.json'));assert.equal(r.wasmSha256,b.wasmSha256);assert.equal(r.nativePixelsSha256,n.pixelsSha256);assert.equal(r.cases,n.cases.length);assert.equal(r.completeGame,false);assert.equal(r.nativeEquivalent,false);
 assert.deepEqual(JSON.parse(track(path+'/browser-logs.json')),[]);track(path+'/browser.png');return r;
}
function rasterRows(r,n,pixels,expectedExact){
 assert.equal(r.rows.length,n.cases.length);assert.equal(r.exactCases,expectedExact);assert.equal(r.strictPixelsEqual,expectedExact===n.cases.length);
 let nonempty=0,different=0,maximum=0;
 for(const [i,c] of n.cases.entries()){
  const row=r.rows[i];assert.equal(row.index,i);assert.deepEqual(row.crop,c.crop);assert.equal(row.status,c.status);assert.equal(row.drawCount,c.drawCount);
  const raw=pixels.subarray(c.offset,c.offset+c.size);let changed=0;for(let j=0;j<raw.length;j+=4)if(raw.readUInt32LE(j)!==0xff42678b)++changed;
  assert.equal(row.foregroundPixels,changed);if(changed)++nonempty;
  for(const k of ['mode','anchor','parent','resolution','baseIndex','axis','place','neighbor','rhw'])if(k in c)assert.equal(row[k],c[k]);
  if(row.differentChannels){++different;assert.ok(row.maxDelta>0);const f=row.first,j=((f.y-c.crop[1])*c.crop[2]+f.x-c.crop[0])*4+f.channel;assert.equal(raw[j],f.d3d9);assert.ok(Math.abs(f.portable-f.d3d9)<=row.maxDelta);}
  else {assert.equal(row.first,null);assert.equal(row.maxDelta,0);assert.equal(row.pixelsSha256,c.pixelsSha256);}
  maximum=Math.max(maximum,row.maxDelta);
 }
 assert.equal(n.cases.length-different,expectedExact);assert.equal(r.renderedCases,nonempty);assert.equal(r.maxDelta,maximum);
 if(!different)assert.equal(r.portablePixelsSha256,n.pixelsSha256);
 return {cases:n.cases.length,exactCases:expectedExact,nonemptyCases:nonempty,maxDelta:maximum,portablePixelsSha256:r.portablePixelsSha256};
}
const shape='artifacts/th14/gpu-original-shapes',{n:shapeNative,pixels:shapePixels}=reference(shape);
const prepared=JSON.parse(track(shape+'/prepared.json'));assert.equal(sha(track('tools/th14-gpu-original-shapes-prepare.py')),prepared.prepareToolSha256);
assert.equal(sha(track(shape+'/prepared.json')),shapeNative.preparedSha256);assert.equal(shapePixels.length,prepared.bytes);
assert.equal(sha(track('artifacts/th14/gpu-original-quads/geometry/native.json')),prepared.renderOracleSha256);
const baseBuild=build(shape),baseBrowser=browser(shape,baseBuild,shapeNative),baseline=rasterRows(baseBrowser,shapeNative,shapePixels,794);
const inputBuild=build(shape+'/native-input'),inputBrowser=browser(shape+'/native-input',inputBuild,shapeNative);rasterRows(inputBrowser,shapeNative,shapePixels,794);assert.equal(inputBrowser.portablePixelsSha256,baseBrowser.portablePixelsSha256);
const inspection=JSON.parse(track(shape+'/geometry-inspection.json'));assert.equal(inspection.cases,810);assert.equal(inspection.exactVertexCases,810);assert.equal(inspection.differentComponents,0);assert.ok(inspection.rows.every(r=>!r.differences.length));
assert.equal(inspection.wasmSha256,sha(track('artifacts/th14/gpu-original-quads/geometry/th14.wasm')));
const variants=[];
for(const [name,exact] of [['clip-linear',794],['clip-mul',794],['color-rcp',794],['clip-color',794],['strip-direct',794],['screen-snap-up',786],['screen-snap',810]]){
 const p=shape+'/'+name,b=build(p,p),r=browser(p,b,shapeNative);assert.equal(b.nativeSha256,sha(read(shape+'/native.json')));variants.push({name,...rasterRows(r,shapeNative,shapePixels,exact)});
}
const grid='artifacts/th14/gpu-screen-grid',{n:gridNative,pixels:gridPixels}=reference(grid);assert.equal(gridNative.cases.length,720);
const coverage=new Set(gridNative.cases.map(c=>[c.baseIndex,c.axis,c.place,c.neighbor,c.rhw].join('/')));assert.equal(coverage.size,720);
const gridVariants=[];for(const [name,exact] of [['before',332],['screen-snap',720]]){const p=grid+'/'+name,b=build(p,p),r=browser(p,b,gridNative);gridVariants.push({name,...rasterRows(r,gridNative,gridPixels,exact)});}
const float=shape+'/float',{n:floatNative,pixels:floatPixels}=reference(float,'native.rgba32f'),floatVariants=[];
for(const [name,path,exact,count] of [['before',float,794,31172],['screen-snap',float+'/screen-snap',810,0]]){
 const b=build(path,path),r=browser(path,b,floatNative);assert.equal(b.nativeSha256,sha(read(float+'/native.json')));assert.equal(r.blendingEnabled,false);assert.equal(r.exactForegroundCases,exact);assert.equal(r.differentFloats,count);assert.equal(r.rows.length,810);
 assert.equal(sha(read(path+'/Shaders.hpp')),name==='before'?baseBuild.sources['runtimes/th12/portable/sdl/Shaders.hpp']:sha(read(shape+'/screen-snap/Shaders.hpp')));
 let total=0;for(const row of r.rows){const c=floatNative.cases[row.index],s=shapeNative.cases[row.index],mask=shapePixels.subarray(s.offset,s.offset+s.size);let foreground=0;for(let j=0;j<mask.length;j+=4)if(mask.readUInt32LE(j)!==0xff42678b)++foreground;assert.equal(row.foregroundPixels,foreground);assert.equal(row.differentFloats,row.differencesByChannel.reduce((a,n)=>a+n,0));total+=row.differentFloats;
  if(row.first){const f=row.first,pos=c.offset+((f.y-c.crop[1])*c.crop[2]+f.x-c.crop[0])*16+f.channel*4;assert.equal(floatPixels.readFloatLE(pos),f.d3d9);}
 }
 assert.equal(total,count);assert.equal(r.rows.filter(x=>!x.differentFloats).length,exact);
 for(const point of r.critical){const c=floatNative.cases[point.index],pos=c.offset+((point.y-c.crop[1])*c.crop[2]+point.x-c.crop[0])*16;assert.deepEqual(point.d3d9,[0,4,8,12].map(d=>floatPixels.readFloatLE(pos+d)));if(name==='screen-snap')assert.deepEqual(point.portable,point.d3d9);}
 if(name==='screen-snap'){assert.equal(r.maxDelta,0);assert.deepEqual(r.differencesByChannel,[0,0,0,0]);}
 floatVariants.push({name,exactForegroundCases:exact,differentFloats:count,maxDelta:r.maxDelta,clearPixelsExcluded:true,allPixelHashesEqual:r.portablePixelsSha256===r.nativePixelsSha256});
}
const regressions=[];let regressionCases=0;
for(const [suite,count] of [['raster',192],['alpha',4096],['alpha-blend',7168],['alpha-depth',2560]]){
 const p='artifacts/th14/gpu-screen-snap-regression/'+suite,b=build(p,'artifacts/th14/gpu-screen-snap-regression/renderer'),nativePath='artifacts/th14/gpu-'+suite,{n,pixels}=reference(nativePath);
 assert.equal(n.cases.length,count);assert.equal(b.nativeSha256,sha(read(nativePath+'/native.json')));const r=browser(p,b,n);assert.equal(r.exactCases,count);assert.equal(r.strictPixelsEqual,true);assert.equal(r.maxDelta,0);assert.equal(r.portablePixelsSha256,n.pixelsSha256);
 if(r.groups)for(const g of r.groups){assert.equal(g.exactCases,g.cases);assert.equal(g.differentChannels,0);assert.equal(g.maxDelta,0);}
 if(suite==='alpha'){const lowPath='artifacts/th14/gpu-alpha-low',{n:low}=reference(lowPath),lowBrowser=JSON.parse(track(p+'/browser-low-result.json'));assert.equal(b.nativeLowSha256,sha(read(lowPath+'/native.json')));assert.equal(lowBrowser.wasmSha256,b.wasmSha256);assert.equal(lowBrowser.nativePixelsSha256,low.pixelsSha256);assert.equal(lowBrowser.portablePixelsSha256,low.pixelsSha256);assert.equal(lowBrowser.exactCases,4096);assert.equal(lowBrowser.strictPixelsEqual,true);regressionCases+=4096;track(p+'/browser-low.png');}
 regressions.push({suite,cases:count,strictPixelsEqual:true,comparedChannels:pixels.length});regressionCases+=count;
}
assert.equal(regressionCases,18112);
const report={diagnosticEvidenceVerified:true,completeGame:false,nativeEquivalent:false,scope:'TH14 screen-space geometry-to-raster subpixel precision diagnosis and candidate verification',baseline,variants,gridVariants,floatVariants,regressions,regressionCases,productionRendererAtEvidenceSha256:sha(read('runtimes/th12/portable/sdl/Renderer.cpp')),productionShaderAtEvidenceSha256:sha(read('runtimes/th12/portable/sdl/Shaders.hpp')),evidence:Object.fromEntries(evidence),limits:['Original-recorded geometry uses controlled non-fog/depth GPU states; full retail batch loop and complete frames are not captured','Boundary variants are controlled translations and reciprocal-W variations, not claimed retail dispatcher executions','Float interpolation comparison excludes native RGBA8 foreground-mask clear pixels; complete RGBA32F output hashes remain different and are not mislabeled as globally equal','Candidate is isolated; actual production integration and its compiled GPU fixtures must be verified separately','Exact observed subpixel grid behavior is measured on this RTX 2080 Ti driver; no cross-device guarantee']};
writeFileSync(resolve(root,'docs/porting/th14-gpu-screen-snap-diagnostic-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({diagnosticEvidenceVerified:true,shapeCandidateExact:810,gridCandidateExact:720,foregroundFloatCandidateExact:810,regressionCases}));
