// Compile exact frozen Application ownership methods with recording devices.
// Device callbacks are declared unit dependencies; this is not GPU execution.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/staged-loader-integration-oct14/cancel-v3'),rt=resolve(home,'source/runtimes/th12/th12_web'),out=resolve(home,'adapter-owner');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),appBytes=readFileSync(resolve(rt,'cpp/sdl/Application.cpp')),app=appBytes.toString(),frozenBytes=readFileSync(resolve(home,'frozen-source.json')),frozen=JSON.parse(frozenBytes);
for(const row of frozen.files)assert.equal(sha(readFileSync(resolve(home,'source/runtimes',row.path))),row.sha256,row.path);
function block(needle){const start=app.indexOf(needle);assert(start>=0,needle);const opening=app.indexOf('{',start);let depth=1,end=opening+1;for(;depth&&end<app.length;end++){if(app[end]==='{')++depth;else if(app[end]==='}')--depth;}assert.equal(depth,0);return app.slice(start,end);}
const methods=['bool prepare(StageResources& stage)override','bool prepare_stage_phase(StageResources& stage,StageResourceEffects::Phase phase)override','bool stage_phase_ready(StageResourceEffects::Phase phase)const override','void finish_stage_phases(StageResources& stage,u32)override','void cancel_stage_phases(StageResources& stage,u32)override','void release(StageResources& stage)override'].map(block);
const tick=block('if(stage_uploads.pending())');assert(!tick.includes('animations.update'));assert(!tick.includes('return true;'));
const fixtureSource=`#include "StageUploadsTh14.hpp"
#include <functional>
#include <vector>
#include <memory>
using namespace th11;using namespace th11::sdl;
struct Graphics {
 std::string error;bool allow=true;u32 calls=0,unloads=0;
 std::function<void(AnmResource&)> before_unload;
 bool preload(AnmResource&){++calls;return allow;}
 void unload(AnmResource& resource){if(before_unload)before_unload(resource);++unloads;}
};
struct Renderer {void flush(){}void invalidate(){}};
struct Loading {bool allow=true;u32 finished=0;bool begin(int&,AnmResource&){return allow;}void finish(int&){++finished;}};
struct Session {int animations=0;struct Resources {struct Core {AnmResource ascii;} core;} resources;};
struct Adapter final:StageResourceEffects {
 Graphics graphics;Renderer renderer;Loading boot_loading;Session session;
 struct ResourceUpload {AnmResource* resource;u16 file;};
 std::vector<ResourceUpload> boot_uploads;u32 boot_upload_index=0;StageResources* boot_stage_owner=nullptr;
 StageUploadsTh14 stage_uploads;std::string error;u32 continuation=0;
 ${methods.join('\n')}
 bool upload_tick(){${tick}\n++continuation;return true;}
 bool references(const AnmResource& resource)const {for(const auto& job:boot_uploads)if(job.resource==&resource)return true;return false;}
};
static u32 checks=0,failed=0,first_failure=0,words[4]{};
static void check(bool value,u32 code){++checks;if(!value){++failed;if(!first_failure)first_failure=code;}}
extern "C" __attribute__((export_name("run"))) const u32* run(){
 Adapter a;auto owner=std::make_unique<StageResources>();StageResources other;owner->stage_number=2;
 owner->ecl_animation_names[0]="one";owner->ecl_animation_names[2]="three";
 a.graphics.before_unload=[&](AnmResource& resource){
  check(!a.references(resource),900);
  bool belongs=&resource==&owner->background||&resource==&owner->logo||&resource==&owner->enemies;
  for(const auto& file:owner->ecl_animations)belongs=belongs||&resource==&file;
  if(belongs&&a.stage_uploads.owner()==owner.get())check(a.stage_uploads.pending_count()==0,901);
 };
 check(a.prepare_stage_phase(*owner,StageResourceEffects::Phase::Hud),1);
 check(!a.stage_phase_ready(StageResourceEffects::Phase::Hud),2);check(a.upload_tick(),3);check(a.continuation==1,4);
 check(a.stage_phase_ready(StageResourceEffects::Phase::Hud),5);a.finish_stage_phases(*owner,1);check(a.stage_uploads.owner()==nullptr,6);check(a.graphics.unloads==0,7);
 check(a.prepare_stage_phase(*owner,StageResourceEffects::Phase::Timeline),10);check(a.stage_uploads.pending_count()==3,11);
 check(a.upload_tick(),12);a.graphics.allow=false;check(!a.upload_tick(),13);check(a.stage_uploads.failed(),14);check(a.stage_uploads.pending_count()==2,15);check(a.continuation==2,16);
 a.cancel_stage_phases(other,7);check(a.stage_uploads.owner()==owner.get(),17);check(a.stage_uploads.pending_count()==2,18);
 a.cancel_stage_phases(*owner,7);check(a.stage_uploads.owner()==nullptr,19);check(a.stage_uploads.pending_count()==0,20);
 a.graphics.allow=true;check(a.prepare(*owner),30);check(a.boot_stage_owner==owner.get(),31);check(a.boot_uploads.size()==5,32);
 check(a.prepare_stage_phase(*owner,StageResourceEffects::Phase::Scene),33);check(a.stage_uploads.pending_count()==1,34);
 a.release(other);check(a.boot_stage_owner==owner.get(),35);check(a.stage_uploads.owner()==owner.get(),36);
 a.release(*owner);check(a.boot_uploads.empty(),37);check(!a.boot_stage_owner,38);check(!a.stage_uploads.owner(),39);check(a.boot_loading.finished==1,40);
 a.boot_loading.allow=false;check(!a.prepare(*owner),50);check(a.boot_stage_owner==owner.get()&&!a.boot_uploads.empty(),51);
 a.release(*owner);check(a.boot_uploads.empty()&&!a.boot_stage_owner,52);check(a.boot_loading.finished==2,53);
 owner.reset();check(a.stage_uploads.owner()==nullptr&&a.boot_uploads.empty(),54);
 words[0]=failed;words[1]=checks;words[2]=first_failure;words[3]=a.continuation;return words;
}
`;
const fixture=resolve(out,'fixture.cpp');writeFileSync(fixture,fixtureSource);const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),wasm=resolve(out,'adapter-owner.wasm');
execFileSync(compiler,['--target=wasm32-wasip1','-DPORT_TITLE=14','-O2','-std=c++17','-fno-exceptions','-fno-rtti','-I',resolve(rt,'cpp/sdl'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',fixture,'-o',wasm],{cwd:out,windowsHide:true,stdio:'inherit',env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(readFileSync(wasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const p=instance.exports.run(),result=Array.from(new Uint32Array(instance.exports.memory.buffer,p,4));assert.equal(result[0],0,JSON.stringify(result));assert(result[1]>40);
const report={privateActualAdapterOwnershipVerified:true,productionChanged:false,productionVerified:false,nativeEquivalent:false,completeGame:false,gpuExecuted:false,resultWords:result,exactApplicationMethods:methods.map(text=>({sha256:sha(Buffer.from(text)),source:text})),exactTickBlock:{sha256:sha(Buffer.from(tick)),source:tick},applicationSha256:sha(appBytes),frozenSourceSha256:sha(frozenBytes),helperSha256:sha(readFileSync(resolve(rt,'cpp/sdl/StageUploadsTh14.hpp'))),fixtureSha256:sha(readFileSync(fixture)),wasmSha256:sha(readFileSync(wasm)),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Exact frozen Application stage/boot prepare-ready, finish, cancel and release methods plus actual stage upload tick block are extracted unchanged and independently compiled with the real StageUploads helper. Recording graphics/renderer/loading callbacks are declared unit dependencies. Tests verify true job progression, no successful stage-frame early return/extra ANM update, partial failure references retained, wrong owner harmless, both boot/stage raw resource pointers removed before unload and owner destruction. No graphics pixels, actual GL/browser execution, Native resource timing or1:1 claim.'};
writeFileSync(resolve(root,'docs/porting/th14-staged-loader-sdl-adapter-owner-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({privateActualAdapterOwnershipVerified:true,checks:result[1],failures:result[0],continuation:result[3]}));
