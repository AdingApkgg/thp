import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out='artifacts/th14/dialogue-application-message-scene-text',evidence={};
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(root,p));
const track=p=>{const b=read(p);evidence[p]={bytes:b.length,sha256:sha(b)};return b;};
const native=JSON.parse(track(out+'/native.json')),prepared=JSON.parse(track(out+'/prepared.json')),scratch=JSON.parse(track(out+'/scratch.json')),build=JSON.parse(track(out+'/build.json')),browser=JSON.parse(track(out+'/browser-diagnostic.json')),pixels=track(out+'/native.bgra');
assert.equal(native.generated,true);assert.equal(native.rows.length,2);assert.equal(native.cases.length,12);assert.equal(sha(pixels),native.pixelsSha256);assert.equal(native.preparedSha256,sha(read(out+'/prepared.json')));assert.equal(prepared.scratchProofSha256,sha(read(out+'/scratch.json')));assert.equal(build.nativeSha256,sha(read(out+'/native.json')));
assert.equal(native.nativeExecutableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
for(const [p,h] of Object.entries(build.sourceHashes))assert.equal(sha(track('runtimes/th12/'+p)),h,p);
for(const [p,h] of Object.entries(build.includedFixtures))assert.equal(sha(track(p.slice(root.length+1).replaceAll('\\','/'))),h,p);
for(const [p,h] of Object.entries(build.objectHashes))assert.equal(sha(read('runtimes/th14/th14_web/artifacts/sdl3-release/objects/'+p.replaceAll('/','_')+'.o')),h,p);
assert.equal(sha(track(out+'/gpu.wasm')),build.wasmSha256);assert.equal(sha(track(out+'/gpu.mjs')),build.loaderSha256);assert.equal(browser.wasmSha256,build.wasmSha256);
for(const [p,h] of [['tools/th14-dialogue-application-message-scene-text-native.py',scratch.toolSha256],['tools/th14-dialogue-application-message-scene-text-gpu-prepare.py',prepared.toolSha256],['tools/th14-dialogue-application-message-scene-text-gpu-native.py',native.toolSha256],['tools/th14-dialogue-application-message-scene-text-gpu-build.mjs',build.toolSha256]])assert.equal(sha(track(p)),h,p);
const fonts=JSON.parse(track('runtimes/th14/th14_web/assets/sdl-native/fonts/manifest.json'));assert.equal(sha(read('runtimes/th14/th14_web/assets/sdl-native/fonts/manifest.json')),build.fontManifestSha256);
for(const f of fonts.files){const b=track('runtimes/th14/th14_web/assets/sdl-native/fonts/'+f.file);assert.equal(b.length,f.bytes);assert.equal(sha(b),f.sha256);}
for(const t of prepared.textures){const b=track(out+'/'+t.file);assert.equal(b.length,t.bytes);assert.equal(sha(b),t.sha256);}
let frames=0,quads=0,requests=0,writingFrames=0;
for(const [row,r] of native.rows.entries()){
 assert.deepEqual(r.input,scratch.rows[row].input);assert.equal(r.program,scratch.rows[row].program);assert.equal(r.frames.length,scratch.rows[row].frames.length);
 for(const [frame,f] of r.frames.entries()){
  ++frames;quads+=f.draws.length;requests+=f.writes.length;
  for(const w of f.writes){const b=track(out+'/'+w.file);assert.equal(b.length,262144);assert.equal(sha(b),w.sha256);}
  if(f.writes.length){const copy=browser.copies[writingFrames++];assert.equal(copy.row,row);assert.equal(copy.frame,frame);assert.equal(copy.nativeSha256,f.writes.at(-1).textureSha256);assert.equal(copy.exact,copy.sha256===copy.nativeSha256);}
 }
}
assert.equal(frames,723);assert.equal(requests,59);assert.equal(browser.animatedFrames,frames);assert.equal(browser.quads,quads);assert.equal(browser.floatComponents,quads*24);assert.equal(browser.nonExactFloatValues,0);assert.equal(browser.actualApplication,true);assert.equal(browser.actualFontWrites,40);assert.equal(browser.textureWrites,writingFrames);assert.equal(browser.copies.length,writingFrames);
assert.equal(browser.stateDifferences.length,browser.stateDifferenceCount);for(const d of browser.stateDifferences){assert.equal(d.field,18);assert.equal(d.actual,1);assert.equal(d.native,0);assert(native.rows[d.row].frames[d.frame].writes.some(w=>w.line===d.vm));}
let different=0,rendered=0,offset=0;
for(const [i,c] of native.cases.entries()){const r=browser.rows[i],b=pixels.subarray(c.offset,c.offset+c.size);assert.equal(c.index,i);assert.equal(c.offset,offset);offset+=c.size;assert.equal(sha(b),c.pixelsSha256);assert.equal(r.index,i);assert.equal(r.row,c.row);assert.equal(r.frame,c.frame);assert.equal(r.drawCount,c.drawCount);if(!r.differentChannels)assert.equal(r.pixelsSha256,c.pixelsSha256);different+=r.differentChannels;if(r.foregroundPixels)++rendered;}
assert.equal(offset,pixels.length);assert.equal(browser.comparedChannels,pixels.length);assert.equal(browser.nativePixelsSha256,native.pixelsSha256);assert.equal(browser.differentChannels,different);assert.equal(browser.renderedCases,rendered);
const logs=JSON.parse(track(out+'/browser-logs.json'));track(out+'/browser.png');for(const p of ['tools/th14-dialogue-application-message-scene-text-gpu.html','tools/th14-dialogue-application-message-scene-text-gpu-serve.mjs','tools/th14-dialogue-application-message-scene-text-gpu-check.mjs'])track(p);
const exactTextures=browser.copies.filter(c=>c.exact).length,renderedOutputPassed=!different&&exactTextures===writingFrames&&!logs.length,selectedStatePassed=browser.stateDifferenceCount===0;
if(!different)assert.equal(browser.portablePixelsSha256,native.pixelsSha256);assert.equal(browser.exactCases,browser.rows.filter(r=>!r.differentChannels).length);assert.equal(browser.exactTextures,exactTextures);assert.equal(browser.passed,renderedOutputPassed&&selectedStatePassed);
const report={passed:renderedOutputPassed&&selectedStatePassed,evidenceVerified:true,renderedOutputPassed,selectedStatePassed,completeGame:false,nativeEquivalent:false,actualApplication:true,routes:2,frames,requests,actualFontWrites:browser.actualFontWrites,writingFrames,exactTextures,quads,floatComponents:quads*24,nonExactFloatValues:browser.nonExactFloatValues,cases:12,exactCases:browser.exactCases,renderedCases:rendered,comparedChannels:pixels.length,differentChannels:different,stateDifferenceCount:browser.stateDifferenceCount,stateDifferences:browser.stateDifferences,browserWarningsOrErrors:logs.length,evidence,limits:['Actual unmodified Application.cpp text_events and actual GameBattle dialogue_text queue; full GameBattle world initialization/update excluded','Owner/interpreter/ANM updates are fixture-driven; world/HUD/input/audio controlled','Original receives 59 synchronous text requests; Application deduplicates to40 uploads; ten writing-frame final atlases compared, not each intermediate native upload','Post-upload flags bit0 differs on hidden text animations19 times; no zero-state-difference claim','Only12 selected current-driver full-screen pixels compared; no complete game or natural-clear equivalence']};
writeFileSync(resolve(root,'docs/porting/th14-dialogue-application-message-scene-text-gpu-observed-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:report.passed,evidenceVerified:true,renderedOutputPassed,selectedStatePassed,frames,requests,actualFontWrites:browser.actualFontWrites,writingFrames,exactTextures,cases:12,exactCases:browser.exactCases,differentChannels:different,stateDifferenceCount:browser.stateDifferenceCount}));
