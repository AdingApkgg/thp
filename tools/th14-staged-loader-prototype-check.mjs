// Private implementation experiment. Never writes production or shared objects.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,copyFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const home=resolve(root,'artifacts/th14/staged-loader-prototype-oct14');mkdirSync(home,{recursive:true});
const enginePath=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'),engineBytes=readFileSync(enginePath),engine=JSON.parse(engineBytes);
assert.equal(Object.keys(engine.sourceHashes).length,265);
const baseline=resolve(home,'baseline/runtimes/th12/th12_web'),prototype=resolve(home,'prototype/runtimes/th12/th12_web'),sourceBindings={};
const put=(path,data)=>{mkdirSync(dirname(path),{recursive:true});if(existsSync(path))assert.equal(sha(readFileSync(path)),sha(Buffer.from(data)),path);else writeFileSync(path,data);};
for(const [name,hash] of Object.entries(engine.sourceHashes)){
 const source=resolve(rt,name),bytes=readFileSync(source);assert.equal(sha(bytes),hash,name);sourceBindings[relative(root,source).replaceAll('\\','/')]=hash;
 put(resolve(baseline,name),bytes);
 if(!['cpp/game/EnemyManager.cpp','cpp/game/EnemyManager.hpp'].includes(name))put(resolve(prototype,name),bytes);
}
const portable=resolve(root,'runtimes/th12/portable');
function copyHeaders(directory){for(const entry of readdirSync(directory,{withFileTypes:true})){const path=resolve(directory,entry.name);if(entry.isDirectory())copyHeaders(path);else if(/\.(hpp|h|inc)$/.test(entry.name)){const bytes=readFileSync(path),name=relative(portable,path);sourceBindings[relative(root,path).replaceAll('\\','/')]=sha(bytes);put(resolve(home,'baseline/runtimes/th12/portable',name),bytes);put(resolve(home,'prototype/runtimes/th12/portable',name),bytes);}}}
copyHeaders(portable);
const ownerHeader=readFileSync(resolve(baseline,'cpp/game/EnemyManager.hpp'),'utf8').replace('    bool reset(EclProgram&);',`    bool reset(EclProgram&);
#if PORT_TITLE == 14
    bool retire();
    bool initialize_empty(EclProgram&);
    bool owner_present()const noexcept{return commands.manager==this;}
    const EclProgram* bound_timeline()const noexcept{return program;}
#endif`);
const ownerCode=readFileSync(resolve(baseline,'cpp/game/EnemyManager.cpp'),'utf8').replace('bool EnemyManager::update(){',`#if PORT_TITLE == 14
bool EnemyManager::retire(){
    while(first)if(!destroy(*first->value))return false;
    first=last=nullptr;count=0;total_created=0;program=nullptr;
    environment.enemy_count=0;environment.boss=nullptr;
    for(auto& boss:commands.bosses)boss=nullptr;
    if(commands.manager==this)commands.manager=nullptr;
    if(environment.th14_enemy_list==&first)environment.th14_enemy_list=nullptr;
    return true;
}
bool EnemyManager::initialize_empty(EclProgram& next){
    if(owner_present()||count||first||last)return false;
    if(!reset(next))return false;
    commands.manager=this;environment.th14_enemy_list=&first;
    return true;
}
#endif
bool EnemyManager::update(){`);
assert(ownerHeader.includes('bool retire();')&&ownerCode.includes('bool EnemyManager::retire()'));
put(resolve(prototype,'cpp/game/EnemyManager.hpp'),ownerHeader);put(resolve(prototype,'cpp/game/EnemyManager.cpp'),ownerCode);
const loaderSource=`#pragma once
#include "Types.hpp"
namespace th11::prototype {
enum class Work:u32{Waiting,Ready,Failed};
enum class LoadPhase:u32{Idle,WaitCapture,WaitMinimum,Hud,Scene,Timeline,Ready,Aborted,Failed};
struct StageActions {
 virtual ~StageActions()=default;
 virtual bool retire_owner()=0;
 virtual bool enter_work_and_initialize()=0;
 virtual Work prepare_hud()=0;
 virtual Work prepare_scene()=0;
 virtual bool publish_empty_owner()=0;
 virtual Work prepare_timeline()=0;
};
struct StagedLoader {
 LoadPhase phase=LoadPhase::Idle;
 u64 deadline=0,last_sample=0;
 bool initial_stage=false,has_sample=false;
 bool request(StageActions& actions,bool initial=false){
  if(phase!=LoadPhase::Idle&&phase!=LoadPhase::Ready)return false;
  if(!actions.retire_owner()){phase=LoadPhase::Failed;return false;}
  initial_stage=initial;has_sample=false;deadline=0;phase=LoadPhase::WaitCapture;return true;
 }
 bool pump(StageActions& actions,u64 now,i32 first_capture_index,u32 supervisor_flags){
  if(phase==LoadPhase::Idle||phase==LoadPhase::Ready)return true;
  if(phase==LoadPhase::Aborted||phase==LoadPhase::Failed)return false;
  if(has_sample&&now<last_sample){phase=LoadPhase::Failed;return false;}
  has_sample=true;last_sample=now;
  for(;;){
   if(phase==LoadPhase::WaitCapture){
    if(first_capture_index>=0){
     if(supervisor_flags&0x180){phase=LoadPhase::Aborted;return false;}
     return true;
    }
    const u64 minimum=initial_stage?0:60000000;
    if(now>~u64(0)-minimum){phase=LoadPhase::Failed;return false;}
    deadline=now+minimum;phase=LoadPhase::WaitMinimum;
   }
   if(phase==LoadPhase::WaitMinimum){
    if(now<deadline)return true;
    if(!actions.enter_work_and_initialize()){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Hud;
   }
   if(phase==LoadPhase::Hud){
    const auto result=actions.prepare_hud();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Scene;
   }
   if(phase==LoadPhase::Scene){
    const auto result=actions.prepare_scene();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    if(!actions.publish_empty_owner()){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Timeline;
   }
   if(phase==LoadPhase::Timeline){
    const auto result=actions.prepare_timeline();
    if(result==Work::Waiting)return true;
    if(result==Work::Failed){phase=LoadPhase::Failed;return false;}
    phase=LoadPhase::Ready;return true;
   }
   phase=LoadPhase::Failed;return false;
  }
 }
};
}
`;
put(resolve(prototype,'cpp/game/StagedLoaderPrototype.hpp'),loaderSource);
const fixtureSource=`#include "StagedLoaderPrototype.hpp"
#include "EnemyManager.hpp"
#include "GameSessionResources.hpp"
#include "Replay.hpp"
#include "GameEconomy.hpp"
#include "SceneCompositor.hpp"
#include <map>
#include <time.h>
using namespace th11;
using namespace th11::prototype;
#define API(n) extern "C" __attribute__((export_name(#n)))
struct Files final:EclResourceProvider {
 std::map<std::string,std::vector<u8>> data;
 u32 animation_requests=0;
 bool read(const std::string& name,std::vector<u8>& out)override{auto it=data.find(name);if(it==data.end())return false;out=it->second;return true;}
 bool animation(u32,const std::string&)override{++animation_requests;return true;}
};
static Files files;
static AnmResource core_ascii,core_text;
static u32 words[16]{};
struct World final:EnemyFrameWorld {
 u32 cleared_targets=0;
 void clear_shot_targets(Enemy*)override{++cleared_targets;}
 bool player_collision(EnemyState&,float,i32& result)override{result=0;return true;}
 bool shot_damage(EnemyState&,i32& result)override{result=0;return true;}
};
struct Fixture final:StageActions {
 GameSessionResources resources;
 std::unique_ptr<StageResources> pending=std::make_unique<StageResources>();
 EnemyEnvironment environment;
 EnemyCommandEnvironment commands;
 AnmManager anm;
 EnemyAnimations animations{anm};
 SceneCompositor compositor{anm};
 World world;
 Rng gameplay,visual;
 GameEconomy economy;
 ReplayStageState header;
 EnemyManager manager{resources.stage->timeline,environment,commands,world};
 StagedLoader loader;
 u32 initialized=0,copy_interrupt_events=0,published=0;
 u32 hud_gate=0,scene_gate=0,timeline_gate=0;
 bool live=false;
 bool graphics_ready=false;
 u16 recorded_seed=0;
 std::vector<u32> order;
 Fixture(bool recording):live(recording){
  gameplay.seed=49408;gameplay.calls=66446;visual.seed=12532;visual.calls=223808;
  environment.shared_random=&gameplay;commands.animations=&animations;header.seed=54321;
  anm.fallback_sprites=&core_ascii;
  graphics_ready=anm.prepare_resource(core_ascii,2)&&anm.prepare_resource(core_text,0)&&compositor.initialize(core_text);
  for(u32 i=0;i<28;++i)header.th14_globals[i]=100+i;
  manager.total_created=299;
 }
 bool retire_owner()override{order.push_back(1);return manager.retire();}
 bool enter_work_and_initialize()override{
  order.push_back(2);
  if(!graphics_ready||!compositor.stage_start())return false;
  ++copy_interrupt_events;
  order.push_back(3);++initialized;
  if(live){recorded_seed=gameplay.seed;visual.seed=recorded_seed;gameplay.calls=0;}
  else header.restore(economy,gameplay,false,&visual);
  return true;
 }
 Work prepare_hud()override{if(!hud_gate)return Work::Waiting;order.push_back(4);return hud_gate==2?Work::Failed:Work::Ready;}
 Work prepare_scene()override{if(!scene_gate)return Work::Waiting;order.push_back(5);return scene_gate==2?Work::Failed:Work::Ready;}
 bool publish_empty_owner()override{order.push_back(6);++published;return manager.initialize_empty(pending->timeline);}
 Work prepare_timeline()override{
  if(!timeline_gate)return Work::Waiting;order.push_back(7);
  if(timeline_gate==2||!pending->timeline.load("st02.ecl",files))return Work::Failed;
  resources.previous_stage=std::move(resources.stage);resources.stage=std::move(pending);
  return Work::Ready;
 }
};
static std::unique_ptr<Fixture> f;
API(allocate) u8* allocate(u32 n){return new u8[n];}
API(load_file) void load_file(const char* name,const u8* p,u32 n){files.data[name]=std::vector<u8>(p,p+n);}
API(load_core) u32 load_core(u32 which,const u8* p,u32 n){return (which?core_text:core_ascii).open(p,n);}
API(reset_case) void reset_case(u32 recording){f=std::make_unique<Fixture>(recording!=0);files.animation_requests=0;}
API(request) u32 request(u32 initial){return f->loader.request(*f,initial!=0);}
API(pump) u32 pump(u64 now,i32 index,u32 flags){return f->loader.pump(*f,now,index,flags);}
API(gates) void gates(u32 hud,u32 scene,u32 timeline){f->hud_gate=hud;f->scene_gate=scene;f->timeline_gate=timeline;}
API(clock_now) u64 clock_now(){timespec t{};if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return u64(t.tv_sec)*1000000000+u64(t.tv_nsec);}
API(observe) const u32* observe(){
 words[0]=u32(f->loader.phase);words[1]=f->manager.owner_present();words[2]=f->manager.total_created;
 words[3]=f->commands.manager==&f->manager;words[4]=f->environment.th14_enemy_list==&f->manager.first;
 words[5]=f->gameplay.seed;words[6]=f->gameplay.calls;words[7]=f->visual.seed;words[8]=f->visual.calls;
 words[9]=f->initialized;words[10]=f->published;words[11]=f->copy_interrupt_events;
 words[12]=f->manager.bound_timeline()==&(f->pending?f->pending:f->resources.stage)->timeline;
 words[13]=f->resources.stage->timeline.definitions.size();words[14]=f->recorded_seed;words[15]=f->manager.count;return words;
}
API(deadline) u64 deadline(){return f->loader.deadline;}
API(order) const u32* order(){return f->order.data();}
API(order_size) u32 order_size(){return f->order.size();}
API(copy_state) const u32* copy_state(){
 const auto& copy=f->compositor.copies[0];
 words[0]=copy.pending_interrupt;words[1]=copy.script_index;words[2]=copy.sprite_index;
 words[3]=copy.timer.previous;words[4]=copy.timer.current;
 std::memcpy(&words[5],&copy.timer.fractional,4);
 words[6]=copy.flags;words[7]=copy.color;
 words[8]=copy.instruction?u32(reinterpret_cast<const u8*>(copy.instruction)-reinterpret_cast<const u8*>(copy.script_begin)):0;
 return words;
}
API(legacy_reset) const u32* legacy_reset(){reset_case(0);EclProgram next;words[0]=f->manager.reset(next);words[1]=f->manager.owner_present();words[2]=f->manager.total_created;words[3]=f->commands.manager==&f->manager;words[4]=f->environment.th14_enemy_list==&f->manager.first;return words;}
API(retire_live_entry) const u32* retire_live_entry(){
 reset_case(0);auto resource=std::make_unique<EclResource>();resource->bytes.resize(32);
 std::memcpy(resource->bytes.data(),"ECLH",4);
 const EclInstruction wait{2147483647,1,16,0,255,0,0};std::memcpy(resource->bytes.data()+16,&wait,16);
 resource->subroutines.push_back({"idle",0,32});auto* raw=resource.get();f->resources.stage->timeline.files.push_back(std::move(resource));f->resources.stage->timeline.definitions.push_back({raw,0});
 auto* enemy=f->manager.spawn("idle",{});if(!enemy){words[0]=0;return words;}
 f->world.target=enemy;f->world.target_locked=true;
 const u32 before=f->manager.count,prior_next=f->manager.total_created;
 const bool retired=f->manager.retire();
 words[0]=retired;words[1]=before;words[2]=prior_next;words[3]=f->manager.count;words[4]=f->manager.total_created;
 words[5]=f->manager.owner_present();words[6]=f->commands.manager==nullptr;words[7]=f->environment.th14_enemy_list==nullptr;
 words[8]=f->world.target==nullptr;words[9]=!f->world.target_locked;words[10]=f->world.cleared_targets;words[11]=f->gameplay.calls;return words;
}
`;
const fixture=resolve(home,'fixture-v4.cpp');put(fixture,fixtureSource);
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),output=resolve(home,'objects');mkdirSync(output,{recursive:true});
const options=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-I',resolve(prototype,'cpp/game')];
const ownObject=resolve(output,'EnemyManager-prototype.o');
execFileSync(compiler,[...options,'-c',resolve(prototype,'cpp/game/EnemyManager.cpp'),'-o',ownObject],{cwd:home,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:output,TMP:output,TMPDIR:output}});
const shared=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),sharedObjects=readdirSync(shared).filter(n=>n.endsWith('.o')&&n!=='cpp_game_EnemyManager.cpp.o').map(n=>resolve(shared,n));
const sharedObjectHashes=Object.fromEntries(sharedObjects.map(p=>[relative(root,p).replaceAll('\\','/'),sha(readFileSync(p))]));
const wasm=resolve(home,'staged-loader-prototype-v4.wasm');
execFileSync(compiler,[...options,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,ownObject,...sharedObjects,'-o',wasm],{cwd:home,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:output,TMP:output,TMPDIR:output}});
const wasmBytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'))),fileBindings=[];
const coreBindings=[];
for(const [which,name] of ['ascii.anm','text.anm'].entries()){
 const bytes=readFileSync(resolve(archive.extraction,name)),row=archive.decoded.find(r=>r.name===name);assert.equal(sha(bytes),row.sha256);
 const p=c.allocate(bytes.length);new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);assert.equal(c.load_core(which,p,bytes.length),1);
 coreBindings.push({name,bytes:bytes.length,sha256:row.sha256});
}
for(const row of archive.decoded.filter(r=>r.name.endsWith('.ecl'))){const bytes=readFileSync(resolve(archive.extraction,row.name));assert.equal(sha(bytes),row.sha256);const data=c.allocate(bytes.length),name=Buffer.from(row.name+'\0'),label=c.allocate(name.length);new Uint8Array(c.memory.buffer,data,bytes.length).set(bytes);new Uint8Array(c.memory.buffer,label,name.length).set(name);c.load_file(label,data,bytes.length);fileBindings.push({name:row.name,bytes:bytes.length,sha256:row.sha256});}
const state=()=>{const p=c.observe();return Array.from(new Uint32Array(c.memory.buffer,p,16));},order=()=>{const p=c.order();return Array.from(new Uint32Array(c.memory.buffer,p,c.order_size()));};
const legacyPointer=c.legacy_reset();assert.deepEqual(Array.from(new Uint32Array(c.memory.buffer,legacyPointer,5)),[1,1,1,1,1]);
const livePointer=c.retire_live_entry(),liveEntry=Array.from(new Uint32Array(c.memory.buffer,livePointer,12));assert.deepEqual(liveEntry,[1,1,300,0,0,0,1,1,1,1,1,66446]);
const nativeBindings={};
function receipt(name,expected){
 const path=resolve(root,'docs/porting',name),bytes=readFileSync(path);assert.equal(sha(bytes),expected,name);
 nativeBindings[relative(root,path).replaceAll('\\','/')]={bytes:bytes.length,sha256:expected};return JSON.parse(bytes);
}
const native=receipt('th14-staged-loader-wait-predicate-verified-oct14.json','ae6fc5db4033a29633d88fc2079b52d7e539a3ee2c75f76dd1d34d6344d7fd31');assert(native.predicateEvidencePassed&&native.caseCount===96);
const nativeOwner=receipt('th14-staged-loader-owner-publication-boundary-observed-oct14.json','d70e257295f26ff206d5451328a6663f94b6f2e0855c8be16bcd756068259f38');
assert(nativeOwner.evidencePassed&&nativeOwner.native.instructionExecutionPassed);
assert.equal(nativeOwner.native.ownerPresentAfter,false);assert.equal(nativeOwner.native.observableNextIdAfter,0);
assert.equal(nativeOwner.native.constructionPrefix.ownerPublishedBeforeEclLoad,true);assert.equal(nativeOwner.native.constructionPrefix.nextIdBeforeEclLoad,1);
const nativeOwnerBytes=readFileSync(nativeOwner.paths.nativeReport);assert.equal(sha(nativeOwnerBytes),nativeOwner.nativeReportSha256);
nativeBindings[relative(root,nativeOwner.paths.nativeReport).replaceAll('\\','/')]={bytes:nativeOwnerBytes.length,sha256:sha(nativeOwnerBytes)};
const nativeQueue=receipt('th14-staged-loader-capture-queue-verified-oct14.json','e8ba853850fb8cd881c4da1a3ce671ea24bde7dcf6accf985809369896f7a845');assert(nativeQueue.captureQueueEvidencePassed&&nativeQueue.guardMeaningProven);
const nativeHost=receipt('th14-staged-loader-host-boundary-verified-oct14.json','5ad13f7c374a5754c092e9b801676078eb9d32194518208d587eb14965a41155');assert(nativeHost.hostBoundaryEvidencePassed);
const originalExe='H:/Games/th/14/th14.exe',originalExeBytes=readFileSync(originalExe);assert.equal(sha(originalExeBytes),native.executableSha256);
nativeBindings[originalExe]={bytes:originalExeBytes.length,sha256:sha(originalExeBytes)};
const predicates=[];
for(const row of native.cases.filter(r=>r.entryKind==='workerEntry')){
 c.reset_case(0);assert.equal(c.request(row.initialStageFlag),1);
 const returned=c.pump(1000000000n,row.declaredSignedGuard,row.supervisorFlags),actual=state();
 const expected=row.branch==='abortBranch'?7:row.branch==='requestSleep1ms'?1:row.branch==='requestSleep60ms'?2:3;
 assert.equal(actual[0],expected);assert.equal(returned,expected===7?0:1);assert.equal(actual[1],0);assert.equal(actual[2],0);
 assert.equal(actual[9],expected===3?1:0);assert.equal(actual[6],expected===3?0:66446);
 predicates.push({nativeBranch:row.branch,guard:row.declaredSignedGuard,flags:row.supervisorFlags,initial:row.initialStageFlag,prototypePhase:actual[0],initialized:actual[9]});
}
c.reset_case(0);assert.equal(c.request(0),1);assert.equal(c.request(0),0);
const copyState=()=>{const p=c.copy_state();return Array.from(new Uint32Array(c.memory.buffer,p,9));},copyBefore=copyState();
assert.equal(c.pump(1000000000n,0,0),1);assert.equal(c.deadline(),0n);
assert.equal(c.pump(2000000000n,-1,0x180),1);assert.equal(c.deadline(),2060000000n);
assert.equal(c.pump(2059999999n,-1,0),1);assert.equal(state()[9],0);assert.equal(state()[6],66446);
assert.deepEqual(copyState(),copyBefore);
assert.equal(c.pump(2060000000n,-1,0),1);assert.deepEqual(state().slice(1,12),[0,0,0,0,54321,0,54321,223808,1,0,1]);
const copyAfter=copyState();assert.notDeepEqual(copyAfter,copyBefore);assert.equal(copyAfter[0],0);
assert.equal(c.pump(3060000000n,-1,0),1);assert.equal(state()[9],1);
assert.deepEqual(copyState(),copyAfter);
c.gates(1,0,0);assert.equal(c.pump(3060000001n,-1,0),1);assert.equal(state()[0],4);assert.equal(state()[1],0);
c.gates(1,1,0);assert.equal(c.pump(3060000002n,-1,0),1);const published=state();assert.equal(published[0],5);assert.equal(published[1],1);assert.equal(published[2],1);assert.equal(published[12],1);assert.equal(published[13],0);
c.gates(1,1,1);assert.equal(c.pump(3060000003n,-1,0),1);const ready=state();assert.equal(ready[0],6);assert.equal(ready[12],1);assert(ready[13]>0);assert.deepEqual(order(),[1,2,3,4,5,6,7]);
assert.equal(c.pump(9999999999n,-1,0),1);assert.equal(state()[9],1);assert.equal(state()[10],1);
const lifecycle={published,ready,order:order(),stableTimelineBeforeAndAfterResourceOwnerMove:true};
c.reset_case(1);assert.equal(c.request(0),1);assert.equal(c.pump(1n,-1,0),1);assert.equal(state()[6],66446);assert.equal(c.pump(60000001n,-1,0),1);const recorded=state();assert.equal(recorded[14],49408);assert.equal(recorded[6],0);assert.equal(recorded[7],49408);assert.equal(recorded[8],223808);
const failures=[];
for(const gates of [[2,1,1],[1,2,1],[1,1,2]]){c.reset_case(0);c.gates(...gates);assert.equal(c.request(1),1);assert.equal(c.pump(1n,-1,0),0);const observed=state();assert.equal(observed[0],8);assert.equal(c.pump(2n,-1,0),0);assert.equal(observed[10],gates[2]===2?1:0);failures.push({gates,observed});}
c.reset_case(0);c.request(0);c.pump(100n,-1,0);assert.equal(c.pump(99n,-1,0),0);assert.equal(state()[0],8);
c.reset_case(0);c.request(0);assert.equal(c.pump(18446744073709551615n,-1,0),0);assert.equal(state()[0],8);
// Actual WASI CLOCK_MONOTONIC drives this separate run; no synthetic Native duration.
c.reset_case(0);c.request(0);const hostStart=c.clock_now();assert(hostStart>0n);c.pump(hostStart,-1,0);assert.equal(state()[9],0);
await new Promise(resolve=>setTimeout(resolve,70));const hostAfter=c.clock_now();assert(hostAfter-hostStart>=60000000n);c.pump(hostAfter,-1,0);assert.equal(state()[9],1);
const actualHostClock={startNs:hostStart.toString(),afterNs:hostAfter.toString(),elapsedNs:(hostAfter-hostStart).toString(),initializedOnce:state()[9]===1};
for(const title of [12,13,16])execFileSync(compiler,[...options.filter(o=>o!=='-DPORT_TITLE=14'),`-DPORT_TITLE=${title}`,'-c',resolve(prototype,'cpp/game/EnemyManager.cpp'),'-o',resolve(output,`EnemyManager-title${title}.o`)],{cwd:home,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:output,TMP:output,TMPDIR:output}});
for(const [p,h] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);
for(const [p,h] of Object.entries(sharedObjectHashes))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
const patchScript=resolve(home,'write-patch.py');put(patchScript,`import difflib\nfrom pathlib import Path\nroot=Path(r'${root.replaceAll('\\','/')}')\nhome=root/'artifacts/th14/staged-loader-prototype-oct14'\nparts=[]\nfor name in ['EnemyManager.hpp','EnemyManager.cpp']:\n rel='runtimes/th12/th12_web/cpp/game/'+name\n before=(home/'baseline'/rel).read_text()\n after=(home/'prototype'/rel).read_text()\n parts.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))\n(home/'owner-lifecycle.patch').write_text(''.join(parts),encoding='utf-8',newline='\\n')\n`);
execFileSync('C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',['-X','utf8',patchScript],{cwd:home,stdio:'inherit',windowsHide:true});
const loaderPatch='--- /dev/null\n+++ b/runtimes/th12/th12_web/cpp/game/StagedLoaderPrototype.hpp\n@@ -0,0 +1,'+loaderSource.trimEnd().split('\n').length+' @@\n'+loaderSource.trimEnd().split('\n').map(l=>'+'+l).join('\n')+'\n';
put(resolve(home,'loader-state.patch'),loaderPatch);
const retainedFailures=['first-detached-buffer-failure.log','second-invalid-ecl-header-failure.log','third-missing-world-dependency-failure.log','fixture.cpp','fixture-v2.cpp','staged-loader-prototype.wasm','staged-loader-prototype-v2.wasm'].map(name=>{const path=resolve(home,name),bytes=readFileSync(path);return {path:relative(root,path).replaceAll('\\','/'),bytes:bytes.length,sha256:sha(bytes)};});
const report={prototypeVerified:true,productionVerified:false,productionChanged:false,completeGame:false,nativeEquivalent:false,
 privateSourceLayout:relative(root,prototype).replaceAll('\\','/'),sourceFilesVerified:265,sourceHashes:engine.sourceHashes,additionalCopiedHeaders:Object.keys(sourceBindings).length-265,
 sharedObjectsReadOnly:true,sharedObjectHashes,sourceBindings,privateOwnerObjectSha256:sha(readFileSync(ownObject)),wasmSha256:sha(wasmBytes),fixtureSha256:sha(readFileSync(fixture)),
 ownerPatch:relative(root,resolve(home,'owner-lifecycle.patch')).replaceAll('\\','/'),ownerPatchSha256:sha(readFileSync(resolve(home,'owner-lifecycle.patch'))),loaderStatePatch:relative(root,resolve(home,'loader-state.patch')).replaceAll('\\','/'),loaderStatePatchSha256:sha(Buffer.from(loaderPatch)),loaderPrototypeSha256:sha(Buffer.from(loaderSource)),
 nativePredicateCasesCompared:predicates.length,predicates,liveOwnerRetirementWords:liveEntry,stableTimelineLifecycle:lifecycle,ordinaryRecordInitializationWords:recorded,failedWorkCases:failures,
 actualHostClock,originalEclFiles:fileBindings,originalCoreFiles:coreBindings,actualCopy0Initialization:{before:copyBefore,after:copyAfter,productionStageStartCalledOnce:true,nativeVmStateEquivalence:false},nativeBindings,originalBoundaryComparison:{retiredOwnerPresent:false,retiredObservableNextId:0,publishedOwnerBeforeEcl:true,publishedNextId:1,originalRetire:'0x422821',originalPublish:'0x4228de/0x4228e4',originalCopy0ThenReplay:'0x435b3a ->0x435f32'},retainedFailedAttempts:retainedFailures,otherTitleObjectsCompiled:[12,13,16],toolSha256:sha(readFileSync(import.meta.filename)),engineManifestSha256:sha(engineBytes),
 scope:'Private unchanged-prefix source clone plus isolated owner lifecycle/clock state prototype. Production265 sources and140 linked shared objects verified unchanged before/after; only private EnemyManager object/output compiled.48 original worker-entry predicate cases match declared loader state. Real EclProgram parses original stage2/include bytes after real empty-owner publication; unique_ptr StageResources move preserves timeline address. Real EnemyManager spawn/destroy/retire removes an isolated future-time ECL entry and shot target using an empty real AnmManager/EnemyAnimations and declared zero collision/damage world; it does not prove Native live enemy deletion. Original ASCII/text ANM bytes are parsed/prepared and actual SceneCompositor::stage_start delivers label2 to copy0 before actual ReplayStageState::restore, both once. This does not compare Native copy0 VM words/GPU effects. HUD/Scene readiness and capture-slot index are declared interface events, not actual graphics/Stage constructors/queue completion. One separate test uses real WASI CLOCK_MONOTONIC elapsed>=60ms; controlled tests inject explicit unit clocks, no Native thread time. No integrated GameSession callbacks, browser, natural replay, ASAN or1:1 production claim.'};
writeFileSync(resolve(root,'docs/porting/th14-staged-loader-private-events-prototype-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({prototypeVerified:true,productionVerified:false,nativePredicateCases:predicates.length,stableTimeline:true,sourceFilesUnchanged:265,actualHostElapsedNs:actualHostClock.elapsedNs,otherTitleCompiles:[12,13,16]}));
