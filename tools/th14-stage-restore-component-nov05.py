"""Compile the exact GameSession initialization lambda with synthetic owners.

Uses real Rng, restore job, ReplayStageState, GameEconomy and the actual economy
projection body. Battle/graphics fields are declared unit owners, not a full run.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parents[1];G=R/'runtimes/th12/th12_web/cpp/game'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()

def body(text,needle):
 start=text.index(needle);opening=start+len(needle)-1;assert text[opening]=='{'
 depth=1;end=opening+1
 while depth:
  if text[end]=='{':depth+=1
  elif text[end]=='}':depth-=1
  end+=1
 return text[start:end]

def main(out):
 out=out.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists()
 assert shutil.disk_usage(R).free>=100*1024**3;out.mkdir(parents=True)
 session=(G/'GameSession.cpp').read_text(encoding='utf8')
 initializer=body(session,'auto initialize=[this,restore=ReplayRngRestoreJobTh14{}]()mutable->prototype::Work {')
 projection=body((G/'Replay.cpp').read_text(encoding='utf8'),'void ReplayStageState::restore_economy_th14(GameEconomy& e)const{')
 fixture=r'''
#include "GameSessionResources.hpp"
#include "StagedLoaderPrototype.hpp"
#include "Replay.hpp"
#include "GameEconomy.hpp"
#include <cstring>
using namespace th11;
#define API(name) extern "C" __attribute__((export_name(#name)))
extern "C" __attribute__((import_module("delivery"),import_name("ready"))) u32 host_ready(u32);
extern "C" __attribute__((import_module("delivery"),import_name("commit"))) u32 host_commit(u32);
extern "C" __attribute__((import_module("delivery"),import_name("now"))) double host_now();
namespace th11 {
StageResourceEffects::DecodeResult StageResourceEffects::decode_stage_phase(GameResources&,StageResources&,Phase,u32){return DecodeResult::Failed;}
@PROJECTION@
}
namespace {
u32 words[24]{};
struct Context;
struct Effects final:StageResourceEffects {
 Context* c=nullptr;u32 stores=0,snapshots=0,invalid=0,snapshot_waits=0;
 static u32 operation(ReplayRngRestorePointTh14 point){
  using P=ReplayRngRestorePointTh14;
  return point==P::GameplaySeedStored||point==P::StageSeedRecorded?0:point==P::ScriptSeedStored?1:2;
 }
 ReplayRngRestoreResultTh14 stage_rng_store_readiness(ReplayRngRestorePointTh14 point)const override{
  const auto code=host_ready(operation(point));return code==0?ReplayRngRestoreResultTh14::Waiting:
   code==1?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Failed;
 }
 bool stage_rng_store_committed(ReplayRngRestorePointTh14 point)override;
 ReplayRngRestoreResultTh14 stage_replay_snapshot_readiness()const override;
 bool stage_replay_snapshot_committed()override;
};
struct Context {
 struct State {bool replay=true;}state;
 struct Animations {Rng visual_rng{0x1011,0xabcd,19},script_rng{0x5e23,0xbeef,23};}animations;
 struct Resources {StageResourceEffects* effects=nullptr;}resources;
 struct Player {struct {i32 minimum_point_value=-800;}state;}player;
 struct Battle {
  ReplayStageState replay_entry;
  struct {i32 spell_practice_id=-900;}enemy_environment;
  struct {struct {i32 continues=-700;}score;}hud;
  Player* player=nullptr;
 } battle_owner;
 Battle* battle=&battle_owner;
 GameEconomy economy;u32 recording_seed=0;std::string error;
 Context(){
  battle->player=&player;economy.score_units=-1000;
  auto& e=battle->replay_entry;e.seed=0x6d31;e.score=31415;e.power=200;e.points=401;
  e.graze=79;e.rank=11;e.lives=4;e.fragments=2;e.extends=3;e.continues=1;e.th14_practice_mode=17;
  for(u32 i=0;i<28;++i)e.th14_globals[i]=i+100;
  e.th14_globals[24]=0x3f800000;e.th14_globals[25]=0x40000000;e.th14_globals[26]=0x40400000;
 }
 auto initializer(){@INITIALIZER@;return initialize;}
};
bool Effects::stage_rng_store_committed(ReplayRngRestorePointTh14 point){
 const auto index=operation(point);if(index!=stores)++invalid;
 const auto expected=c->state.replay?c->battle->replay_entry.seed:c->recording_seed;
 if(index==0&&c->state.replay&&c->animations.visual_rng.seed!=u16(expected))++invalid;
 if(index==1&&c->animations.script_rng.seed!=u16(expected))++invalid;
 if(index==2&&c->animations.visual_rng.calls!=0)++invalid;
 ++stores;return host_commit(index)!=0;
}
ReplayRngRestoreResultTh14 Effects::stage_replay_snapshot_readiness()const{
 auto& self=*const_cast<Effects*>(this);if(c->economy.score_units!=-1000)++self.invalid;
 const auto code=host_ready(3);if(code==0)++self.snapshot_waits;
 return code==0?ReplayRngRestoreResultTh14::Waiting:code==1?ReplayRngRestoreResultTh14::Ready:ReplayRngRestoreResultTh14::Failed;
}
bool Effects::stage_replay_snapshot_committed(){
 ++snapshots;const auto& e=c->economy;
 if(stores!=3||e.score_units!=31415||e.power!=200||e.point_value!=401||e.graze!=79||
    e.rank!=11||e.difficulty!=103||e.th14_point_items!=108||e.max_point_value!=111||
    e.max_power!=113||e.power_step!=114||e.lives!=4||e.life_fragments!=2||e.th14_life_awards!=3||
    e.th14_bombs!=118||e.th14_bomb_fragments!=119||e.th14_reserved_54!=121||e.th14_special_drop_count!=127||
    e.th14_combo.total!=120||e.th14_combo.count!=122||e.th14_combo.timer!=123||
    e.th14_combo.position.x!=1||e.th14_combo.position.y!=2||e.th14_combo.position.z!=3||
    c->battle->enemy_environment.spell_practice_id!=17||c->battle->hud.score.continues!=1||
    c->player.state.minimum_point_value!=110)++invalid;
 return host_commit(3)!=0;
}
}
API(run) u32 run(u32 playback,u32 maximum_ms){
 Context c;Effects effects;effects.c=&c;c.resources.effects=&effects;c.state.replay=playback!=0;
 auto initialize=c.initializer();const auto start=host_now();u32 iterations=0;
 auto progress=prototype::Work::Waiting;
 while(progress==prototype::Work::Waiting&&host_now()-start<maximum_ms){
  c.animations.script_rng.next32_with_boundary([&](RngBoundary){
   if(progress==prototype::Work::Waiting)progress=initialize();
  });++iterations;
 }
 words[0]=u32(progress);words[1]=effects.stores;words[2]=effects.snapshots;words[3]=effects.invalid;
 words[4]=effects.snapshot_waits;words[5]=iterations;words[6]=u32(c.economy.score_units);
 words[7]=c.animations.visual_rng.calls;words[8]=u32(c.error.empty());words[9]=ReplayRngRestoreScopeTh14::active?1:0;
 words[10]=c.recording_seed;words[11]=c.animations.visual_rng.seed;words[12]=u32((host_now()-start)*1000);
 return u32(progress);
}
API(value) u32 value(u32 index){return index<24?words[index]:~0u;}
'''.replace('@INITIALIZER@',initializer).replace('@PROJECTION@',projection)
 (out/'fixture.cpp').write_text(fixture,encoding='utf8',newline='\n')
 # All game headers are small source inputs; frozen copies make the executed
 # component independent of subsequent worktree edits.
 headers={}
 for path in sorted(G.glob('*.hpp')):
  raw=path.read_bytes();(out/path.name).write_bytes(raw);headers[path.name]=SHA(raw)
 compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
 assert SHA(compiler.read_bytes())=='945cba19ec5c002628bb7d226d21a443198e5da5d9e5430fd2f61b9f143d5309'
 argv=[str(compiler),'--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0',
  '-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',
  str(out/'fixture.cpp'),'-o',str(out/'component.wasm')]
 with(out/'compile.log').open('wb')as log:
  result=subprocess.run(argv,cwd=out,env={**os.environ,'TEMP':str(out),'TMP':str(out)},stdout=log,stderr=subprocess.STDOUT,timeout=90)
 assert result.returncode==0,'Retain compile.log'
 report=dict(compiled=True,headerHashes=headers,fixtureSha256=SHA((out/'fixture.cpp').read_bytes()),
  wasmSha256=SHA((out/'component.wasm').read_bytes()),initializerSha256=SHA(initializer.encode()),
  projectionSha256=SHA(projection.encode()),sourceBindings={str(p.relative_to(R)):SHA(p.read_bytes())for p in [G/'GameSession.cpp',G/'Replay.cpp']},
  exactGameSessionInitializationLambda=True,exactReplayEconomyProjection=True,syntheticInputsOnly=True,
  battleAndGraphicsAreUnitDependencies=True,ordinaryApplicationExecuted=False,completeGame=False,
  toolSha256=SHA(Path(__file__).read_bytes()))
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(compiled=True,wasmSha256=report['wasmSha256'],actualInitializationLambda=True)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
