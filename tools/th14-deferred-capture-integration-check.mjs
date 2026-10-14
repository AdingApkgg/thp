// Actual private Pause methods/resources plus explicit controlled backend.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/deferred-capture-integration-oct14'),rt=resolve(root,'runtimes/th12/th12_web');
const sha=b=>createHash('sha256').update(b).digest('hex'),inputs=JSON.parse(readFileSync(resolve(out,'integration-inputs.json'))),bindings={};
const bind=p=>{const b=readFileSync(p);bindings[p]={bytes:b.length,sha256:sha(b)};return b;};
for(const [p,b] of Object.entries(inputs.sourceBindings))assert.equal(sha(bind(resolve(out,inputs.modifiedExistingFiles.includes(p)?'before':'source',p))),b.sha256);
// Only four original files have dedicated before copies; all other game
// sources remain in the immutable source snapshot with their original hash.
const fixture=`#include "PauseMenu.hpp"
#include "ApplicationCaptureTh14.hpp"
#include "GameResources.hpp"
#include "GameSession.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;
static AnmManager animations;static AnmResource text,front;static ScoreFile scores;
static DeferredCaptureQueueTh14 queue;static std::unique_ptr<DeferredCaptureBindingTh14> binding;
static std::unique_ptr<PauseMenu> menu;
static i32 values[128];
struct Backend {int result=1,calls=0; i32 source[4]{},destination[4]{};u32 from=0,to=0;
 bool resample(u32 a,const i32* b,u32 c,const i32* d,const void*,u32,u32){++calls;from=a;to=c;std::copy(b,b+4,source);std::copy(d,d+4,destination);return result!=0;}};
struct Graphics {static constexpr u32 screen=1;Backend backend;bool null_target=false;int texture_calls=0,dirty=0;AnmResource* resolved=nullptr;u32 index=0;
 u32 texture(AnmResource& file,u32 n){++texture_calls;resolved=&file;index=n;return null_target?0:100+n;}void changed(u32){++dirty;}};
struct Render {int flushes=0,invalidations=0;void flush(){++flushes;}void invalidate(){++invalidations;}};
struct FixtureDialogueState {bool active=false;};struct BattleState {FixtureDialogueState* dialogue=nullptr;};
struct Session {struct Resources{struct Core{AnmResource& text;}core;}resources;BattleState* battle=nullptr;struct State{GameSessionPhase phase=GameSessionPhase::stage;}state;};
static FixtureDialogueState dialogue;static BattleState battle;static Session session{{{text}},&battle};
extern "C" unsigned allocate(unsigned n){return unsigned(std::malloc(n));}
extern "C" unsigned output(){return unsigned(values);}
extern "C" int load(unsigned address,unsigned size){GameResources source;if(!source.open_archive(reinterpret_cast<const u8*>(address),size))return 0;
 if(!source.open_anm("text.anm",text)||!source.open_anm("front.anm",front))return 0;
 return animations.prepare_resource(text,0)&&animations.prepare_resource(front,5);}
static void observe(){
 std::memcpy(values,queue.slots.data(),160);values[40]=menu?menu->state:-1;values[41]=menu?menu->capture_requested:0;values[42]=menu?i32(menu->background_animation):0;
 values[43]=queue.first_file_index();values[44]=th14_capture_queue(animations)==&queue;
 if(menu)if(auto* vm=animations.find(menu->background_animation)){values[45]=vm->script_index;values[46]=vm->file_index;values[47]=vm->resource==&text;
  if(vm->sprite){values[48]=i32(vm->sprite->texture);values[49]=i32(vm->sprite->x);values[50]=i32(vm->sprite->y);values[51]=i32(vm->sprite->width);values[52]=i32(vm->sprite->height);}}
}
extern "C" int begin_case(int kind){menu.reset();animations.clear();queue={};binding.reset();binding=std::make_unique<DeferredCaptureBindingTh14>(animations,queue);std::memset(values,0,sizeof(values));
 menu=std::make_unique<PauseMenu>(animations,text,front,scores);menu->selection=0;menu->difficulty=0;menu->stage=kind==4?7:1;
 menu->spell_practice_id=kind==3||kind==6?0:-1;
 bool ok=kind==0?menu->begin(false):menu->begin_end(kind==2||kind==3||kind==5||kind==6,kind>=4);observe();return ok;
}
extern "C" int update_case(int tick){menu->timer.current=tick;bool ok=menu->update(0,0);observe();return ok;}
extern "C" int destroy_menu(){menu.reset();observe();return queue.first_file_index();}
extern "C" int consume_case(int null_target,int result){Graphics graphics;Render renderer;graphics.null_target=null_target;graphics.backend.result=result;
 th11::sdl::th14_consume_deferred_captures(queue,session,graphics,renderer);observe();values[60]=graphics.texture_calls;values[61]=graphics.resolved==&text;values[62]=graphics.index;values[63]=graphics.backend.calls;values[64]=graphics.dirty;values[65]=renderer.invalidations;values[66]=renderer.flushes;values[67]=graphics.backend.from;values[68]=graphics.backend.to;
 std::copy(graphics.backend.source,graphics.backend.source+4,values+69);std::copy(graphics.backend.destination,graphics.backend.destination+4,values+73);return 1;}
extern "C" int phase_value(int index){const GameSessionPhase phases[]={GameSessionPhase::stage,GameSessionPhase::paused,GameSessionPhase::game_over};return i32(phases[index]);}
extern "C" int source_case(int phase,int active){session.state.phase=GameSessionPhase(phase);dialogue.active=active;battle.dialogue=&dialogue;
 auto source=th11::sdl::th14_immediate_capture_source(session);values[80]=source.text_intermediate;std::copy(source.rectangle,source.rectangle+4,values+81);return 1;}
extern "C" int unbind_case(){binding.reset();observe();return th14_capture_queue(animations)==nullptr;}
`;
writeFileSync(resolve(out,'fixture.cpp'),fixture);
const objectsDir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
const objects=readdirSync(objectsDir).filter(n=>n.endsWith('.o')&&!['cpp_game_PauseMenu.cpp.o','cpp_game_PauseEnd.cpp.o'].includes(n)).map(n=>resolve(objectsDir,n));
const objectHashes=Object.fromEntries(objects.map(p=>[p,sha(bind(p))]));
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),wasm=resolve(out,'integration.wasm');
const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',...['allocate','output','load','begin_case','update_case','destroy_menu','consume_case','source_case','phase_value','unbind_case'].map(n=>'-Wl,--export='+n),'-DPORT_TITLE=14','-I',resolve(out,'source/cpp/game'),'-I',resolve(out,'source/cpp/sdl'),'-I',resolve(rt,'cpp/sdl'),'-I',resolve(rt,'cpp/game')];
execFileSync(compiler,[...flags,resolve(out,'fixture.cpp'),resolve(out,'source/cpp/game/PauseMenu.cpp'),resolve(out,'source/cpp/game/PauseEnd.cpp'),...objects,'-o',wasm],{cwd:root,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
for(const [p,digest] of Object.entries(objectHashes))assert.equal(sha(readFileSync(p)),digest,'Concurrent object changed');
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bind(wasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=bind('H:/Games/th/14/th14.dat');assert.equal(sha(archive),'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
const ptr=c.allocate(archive.length);new Uint8Array(c.memory.buffer,ptr,archive.length).set(archive);assert.equal(c.load(ptr,archive.length),1);
const words=()=>[...new Int32Array(c.memory.buffer,c.output(),128)],cases=[];
for(let kind=0;kind<=6;kind++){
 assert.equal(c.begin_case(kind),1,'begin '+kind);const entry=words();
 if(kind<=3){assert.equal(entry[41],1);assert.equal(entry[43],-1);assert.equal(entry[45],52);}
 if(kind===4){assert.equal(entry[41],0);assert.equal(entry[43],0);assert.deepEqual(entry.slice(2,6),[32,16,384,448]);assert.deepEqual(entry.slice(6,10),entry.slice(49,53));assert.equal(entry[1],entry[48]);assert.equal(entry[47],1);}
 if(kind===5||kind===6){assert.equal(entry[41],0);assert.equal(entry[43],-1);assert.equal(entry[42],0);}
 const updates=[];
 if(kind===5){for(const tick of [0,9,10,79]){assert.equal(c.update_case(tick),1);const w=words();assert.equal(w[40],21);assert.equal(w[43],-1);updates.push({tick,state:w[40],first:w[43]});}
  assert.equal(c.update_case(80),1);const w=words();assert.equal(w[40],22);assert.equal(w[43],0);assert.equal(w[41],0);assert.equal(w[45],52);updates.push({tick:80,state:w[40],first:w[43]});}
 if(kind===6){assert.equal(c.update_case(9),1);assert.equal(words()[43],-1);assert.equal(c.update_case(10),1);assert.equal(words()[40],22);assert.equal(words()[43],-1);}
 cases.push({kind,entry:entry.slice(0,53),updates});
}
const retirements=[];
for(const nullTarget of [0,1])for(const result of [0,1,-2147467259]){
 assert.equal(c.begin_case(4),1);const before=words();assert.equal(c.destroy_menu(),0,'queue survives menu destruction');assert.equal(c.consume_case(nullTarget,result),1);const after=words();
 assert.equal(after[43],-1);assert.equal(after[44],1);assert.equal(after[60],1);assert.equal(after[61],1);assert.equal(after[62],before[1]);assert.equal(after[63],nullTarget?0:1);
 if(!nullTarget){assert.deepEqual(after.slice(69,73),[32,16,416,464]);assert.deepEqual(after.slice(73,77),[before[6],before[7],before[6]+before[8],before[7]+before[9]]);assert.equal(after[67],1);assert.equal(after[64],1);}
 retirements.push({nullTarget,controlledCopyResult:result,requestBefore:before.slice(0,40),requestAfter:after.slice(0,40),menuDestroyedBeforeConsumption:true,counters:after.slice(60,77)});
}
const immediate=[];for(const [index,label] of ['stage','paused','game_over'].entries())for(const active of [0,1]){const phase=c.phase_value(index);assert.equal(c.source_case(phase,active),1);const w=words();assert.equal(w[80],active);assert.deepEqual(w.slice(81,85),active?[128,16,512,464]:[32,16,416,464]);immediate.push({declaredPhase:label,actualPhaseEnum:phase,dialogueActive:!!active,textIntermediate:!!w[80],sourceRectangle:w.slice(81,85)});}
assert.equal(c.unbind_case(),1);assert.equal(words()[44],0);
const report={privateIntegrationCodeVerified:true,productionChanged:false,completeGame:false,nativeEquivalent:false,cases,retirements,immediateSourceCases:immediate,
 applicationQueueSurvivesMenuDestruction:true,scopeBindingRemovedAtDestruction:true,resourceIdentity:'Actual decoded th14.dat text.anm resource and actual initialized text52 sprite/texture request; declared controlled backend returns only, no GPU copy.',
 fixtureSha256:sha(Buffer.from(fixture)),wasmSha256:sha(readFileSync(wasm)),flags,objectHashes,bindings,inputsSha256:sha(readFileSync(resolve(out,'integration-inputs.json'))),toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Private actual PauseMenu/PauseEnd calls with original real text/front ANM bytes and existing core objects. Four immediate entry cases, normal Extra completion deferred entry, completed StagePractice80-frame deferred creation, completed SpellPractice10-frame no-copy, six explicit null/return-value retirement variants and six phase-independent Immediate source cases. Backend copy is controlled; graphics/error-service semantics, whole Application execution, loader concurrency/GPU completion, pixels, natural menu/score timelines and production explicit queue ownership remain unverified.'};
writeFileSync(resolve(root,'docs/porting/th14-deferred-capture-integration-code-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({privateIntegrationCodeVerified:true,entryCases:cases.length,retirementCases:retirements.length,immediateSourceCases:immediate.length,productionChanged:false}));
