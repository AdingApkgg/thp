// Independent current production selector/Dialogue lifecycle versus pinned retail prefixes.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const enginePath=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'),engineBytes=readFileSync(enginePath),engine=JSON.parse(engineBytes);
assert.equal(Object.keys(engine.sourceHashes).length,265);
for(const [p,h] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);
const header='cpp/sdl/PauseCaptureTh14.hpp',application='cpp/sdl/Application.cpp';
const policyBytes=readFileSync(resolve(rt,header)),appBytes=readFileSync(resolve(rt,application)),appSource=appBytes.toString();
assert(appSource.includes('const auto capture=th14_pause_capture_source(session);'));
assert(appSource.includes('source=graphics.texture(session.resources.core.text,3)'));
assert(appSource.includes('graphics.backend.resample(source,from,target,to,nullptr,0,0)'));
assert(appSource.indexOf('const auto capture=th14_pause_capture_source(session);')<appSource.indexOf('if(!session.draw(renderer,&frame_text))'));
const out=resolve(root,'artifacts/th14/pause-dialogue-capture',sha(policyBytes).slice(0,16));mkdirSync(out,{recursive:true});
const fixture=resolve(out,'fixture.cpp'),source=`#include "PauseCaptureTh14.hpp"
using namespace th11;
static GameSession session;
static u32 values[5]{};
static std::vector<u8> message;
extern "C" __attribute__((export_name("allocate"))) u8* allocate(u32 n){return new u8[n];}
extern "C" __attribute__((export_name("load"))) i32 load(u32 which,const u8* p,u32 n){return (which?session.resources.core.text:session.resources.core.ascii).open(p,n);}
extern "C" __attribute__((export_name("initialize"))) i32 initialize(){
 auto& a=session.animations;a.fallback_sprites=&session.resources.core.ascii;
 if(!a.prepare_resource(session.resources.core.ascii,2)||!a.prepare_resource(session.resources.core.text,0))return 0;
 session.battle=std::make_unique<GameBattle>(session.resources,a,session.economy,session.spell_records,session.compositor,session.clear_records);
 session.battle->dialogue=std::make_unique<Dialogue>(a,session.resources.core.text,session.resources.core.players[0],session.resources.core.front,session.resources.stage->enemies,session.resources.stage->logo,*session.battle);
 session.state.phase=GameSessionPhase::paused;return 1;
}
extern "C" __attribute__((export_name("begin_message"))) i32 begin_message(){
 message.resize(16);const u32 table[]={1,12,0};std::memcpy(message.data(),table,12);
 message[12]=2;message[13]=0;message[14]=0;message[15]=0;
 return session.battle->dialogue->begin(message,0);
}
extern "C" __attribute__((export_name("step_message"))) i32 step_message(){return session.battle->dialogue->update(0,0);}
extern "C" __attribute__((export_name("active"))) i32 active(){return session.battle&&session.battle->dialogue&&session.battle->dialogue->active;}
extern "C" __attribute__((export_name("phase"))) void phase(u32 p){session.state.phase=p==0?GameSessionPhase::title:p==1?GameSessionPhase::stage:p==2?GameSessionPhase::paused:GameSessionPhase::game_over;}
extern "C" __attribute__((export_name("observe"))) const u32* observe(float scale){const auto source=th14_pause_capture_source(session,scale);values[0]=source.text_intermediate;for(u32 i=0;i<4;++i)values[i+1]=u32(source.rectangle[i]);return values;}
extern "C" __attribute__((export_name("observe_absent"))) const u32* observe_absent(){auto battle=std::move(session.battle);const auto source=th14_pause_capture_source(session);values[0]=source.text_intermediate;for(u32 i=0;i<4;++i)values[i+1]=u32(source.rectangle[i]);session.battle=std::move(battle);return values;}
`;
if(existsSync(fixture))assert.equal(sha(readFileSync(fixture)),sha(Buffer.from(source)));else writeFileSync(fixture,source);
const wasm=resolve(out,'capture-selector.wasm'),objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-I',resolve(rt,'cpp/game'),'-I',resolve(rt,'cpp/sdl'),fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasmBytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archivePath=resolve(root,'artifacts/archive-differential/th14.json'),archiveBytes=readFileSync(archivePath),archive=JSON.parse(archiveBytes),resourceBindings=[];
for(const [which,name] of [[0,'ascii.anm'],[1,'text.anm']]){const data=readFileSync(resolve(archive.extraction,name)),row=archive.decoded.find(r=>r.name===name);assert.equal(sha(data),row.sha256);const pointer=c.allocate(data.length);new Uint8Array(c.memory.buffer,pointer,data.length).set(data);assert.equal(c.load(which,pointer,data.length),1,name);resourceBindings.push({name,bytes:data.length,sha256:sha(data)});}
assert.equal(c.initialize(),1);assert.equal(c.active(),0);
const boundaryPath=resolve(root,'docs/porting/th14-staged-loader-host-boundary-verified-oct14.json'),boundaryBytes=readFileSync(boundaryPath),boundary=JSON.parse(boundaryBytes);assert(boundary.hostBoundaryEvidencePassed);
assert.equal(boundary.executableSha256,'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353');
const words=p=>Array.from(new Uint32Array(c.memory.buffer,p,5));const cases=[];
for(const active of [false,true]){
 if(active){assert.equal(c.begin_message(),1);assert.equal(c.active(),1);}
 for(const row of boundary.immediatePauseSourceCases.filter(r=>r.dialoguePointerNonzero===active)){
  const observed=words(c.observe(row.declaredScale));assert.deepEqual(observed,[+active,...row.sourceRectangle]);cases.push({dialogueActive:active,scale:row.declaredScale,nativeSurface:row.sourceSurface,nativeRect:row.sourceRectangle,productionWords:observed});
 }
}
const phaseCases=[];
for(const phase of [0,1,3]){c.phase(phase);const observed=words(c.observe(1));assert.deepEqual(observed,[0,32,16,416,464]);phaseCases.push({phase,dialogueObjectActive:true,productionWords:observed});}
c.phase(2);const noBattle=words(c.observe_absent());assert.deepEqual(noBattle,[0,32,16,416,464]);
const lifecycle=[];for(let i=0;i<3;i++){const result=c.step_message(),active=c.active(),observed=words(c.observe(1));assert.equal(result,i===2?1:0);assert.equal(active,i===2?0:1);assert.deepEqual(observed,i===2?[0,32,16,416,464]:[1,128,16,512,464]);lifecycle.push({step:i,result,active,productionWords:observed});}
const nativePath=resolve(out,'native-owner-writers.json'),nativeTool=resolve(root,'tools/th14-pause-dialogue-capture-native.py');
execFileSync(process.env.TH_NATIVE_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',['-X','utf8',nativeTool,'--output',nativePath],{cwd:root,stdio:'inherit',windowsHide:true});
const nativeBytes=readFileSync(nativePath),native=JSON.parse(nativeBytes);assert(native.nativeDialogueOwnerEvidencePassed);assert.equal(native.toolSha256,sha(readFileSync(nativeTool)));
const report={pauseDialogueCaptureEvidencePassed:true,productionChanged:true,completeGame:false,nativeEquivalent:false,
 correction:'TH14 ordinary paused session with active Dialogue now copies text.anm texture3 and logical source RECT128,16,512,464. Its ImmediatePause update-before-draw point remains. No-dialogue capture remains backbuffer32,16,416,464; other phases retain prior source behavior.',
 originalPredicate:native.provenMeaning,native,selectorCases:cases,nonPausePhaseCases:phaseCases,noBattleWords:noBattle,actualDialogueLifecycle:lifecycle,
 sourceFilesVerified:265,sourceHashes:engine.sourceHashes,productionSourceHashes:{[header]:sha(policyBytes),[application]:sha(appBytes)},resourceBindings,
 fixtureSha256:sha(readFileSync(fixture)),wasmSha256:sha(wasmBytes),engineBuildSha256:sha(engineBytes),toolSha256:sha(readFileSync(import.meta.filename)),nativeToolSha256:sha(readFileSync(nativeTool)),nativeReportSha256:sha(nativeBytes),nativeBoundaryReportSha256:sha(boundaryBytes),archiveManifestSha256:sha(archiveBytes),
 paths:{fixture,wasm,nativeReport:nativePath},
 scope:'Current production inline selector independently compiled with unchanged265 engine source objects; real original ASCII/text ANM resources are parsed/prepared and real Dialogue::begin/MSG0 update/clear establish active lifetime, not fixture flag assignment. Six original448c3a prefixes compared in source identity/RECT only, including controlled1/1.5/2 scales; current SDL uses logical640x480/default scale1. Excludes actual application backend resample pixels, Browser/HAL render, successful COM calls, DeferredEnd post-draw timing, main loader, audio and whole-game equality. Existing GPU fixtures/Shader/Renderer and shared objects are not edited or rebuilt.'};
writeFileSync(resolve(root,'docs/porting/th14-pause-dialogue-capture-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({pauseDialogueCaptureEvidencePassed:true,nativeSelectorCases:cases.length,dialogueLifecycleSteps:lifecycle.length,nonPauseCases:phaseCases.length,sourceFilesVerified:265,productionChanged:true}));
