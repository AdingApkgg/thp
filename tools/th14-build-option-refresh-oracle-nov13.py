"""Link actual Player/ANM option lifecycles to the current normal providers."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/option-refresh-oracle-nov13';O=H/'component';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
P=R/'artifacts/th14/player-initialization-oracle-nov13';provider_path=P/'candidate-providers/build.json';provider=load(provider_path)
assert provider['normalEngineAccessControl']
for name,digest in provider['sourceBindings'].items():assert sha(R/name)==digest,name
for row in provider['currentProviders']:assert sha(R/row['object'])==row['objectSha256']
parent=P/'candidate-component';old=load(parent/'build.json');assert sha(parent/'fixture.cpp')==old['observerBindings'][(parent/'fixture.cpp').relative_to(R).as_posix()]
source=(parent/'fixture.cpp').read_text()
source=source.replace('struct World final:PlayerFrameWorld{};', '''struct World final:PlayerFrameWorld{
 u32 hud_calls=0;std::vector<u32> hud_values;
 bool display_lives(i32 lives,i32 fragments)override{++hud_calls;hud_values.insert(hud_values.end(),{u32(lives),u32(fragments)});return true;}
};''')
source+='''
std::vector<AnmVm*> observed;
API(observer_begin) void observer_begin(){
 auto& p=*probe;p.economy.lives=2;p.economy.life_fragments=0;observed.clear();
 p.animations.before_initial_update=[](const AnmVm& v){
  auto* ptr=const_cast<AnmVm*>(&v);if(std::find(observed.begin(),observed.end(),ptr)==observed.end())observed.push_back(ptr);return true;
 };
}
API(action) u32 action(u32 kind,i32 power){
 auto& p=*probe;auto& f=*p.player;auto& a=p.animations;p.economy.power=power;
 if(kind==0){if(!f.rebuild_th14_options())return 0;}
 else if(kind==1){if(!f.start_stage())return 0;}
 else if(kind==2){if(!a.update(true)||!a.update(false))return 0;}
 else return 0;
 const auto bits=[](float v){u32 w;std::memcpy(&w,&v,4);return w;};
 words={a.active_count(),a.script_rng.seed_value(),a.script_rng.call_count(),a.visual_rng.seed_value(),a.visual_rng.call_count(),
        u32(f.state.life_state),u32(f.motion.state.option_count),bits(f.motion.state.option_angle),u32(f.motion.state.focused)};
 for(const Timer* t:{&f.state.state_timer,&f.state.transition_timer,&f.state.th14_shooting_age,&f.shots.schedule.timer})
  words.insert(words.end(),{u32(t->previous),u32(t->current),bits(t->fractional),u32(t->rate!=nullptr),t->flags});
 constexpr u32 offsets[]={0,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x70,0xa8,0xb0,0xb4,0xd0,0xd4,0xd8};
 for(const auto& option:f.motion.options)for(u32 at:offsets){u32 w;std::memcpy(&w,reinterpret_cast<const u8*>(&option)+at,4);words.push_back(w);}
 for(const auto& pair:f.motion.state.th14_history){words.push_back(u32(pair[0]));words.push_back(u32(pair[1]));}
 std::vector<const AnmVm::Node*> heads;
 for(auto* vm:observed)if(vm->id&&a.find(vm->id)==vm){
  const auto* n=&vm->registry;u32 budget=0;while(n->previous){if(++budget>64)return 0;n=n->previous;}
  if(std::find(heads.begin(),heads.end(),n)==heads.end())heads.push_back(n);
 }
 u32 count=0;
 for(auto* n:heads)for(;n;n=n->next){if(++count>64)return 0;auto row=th14_title_observer::canonical_transition(n->value);words.insert(words.end(),row.begin(),row.end());}
 if(count!=a.active_count())return 0;
 words.push_back(p.world.hud_calls);return words.size();
}
'''
fixture=O/'fixture.cpp';fixture.write_text(source,encoding='utf8',newline='\n')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256']
cmd=[str(cc),*provider['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*[row['object']for row in provider['currentProviders']],'-o',str(O/'probe.wasm')]
assert '-fno-access-control'not in cmd
with(O/'build.log').open('wb')as log:subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
report=dict(sourceBindings=provider['sourceBindings'],objectBindings={row['object']:row['objectSha256']for row in provider['currentProviders']},
 observerBindings={p.relative_to(R).as_posix():sha(p)for p in [Path(__file__),fixture,parent/'fixture.cpp']},
 providerBuild=str(provider_path),providerBuildSha256=sha(provider_path),normalAccessControl=True,gameObjectsReused=141,
 wasmSha256=sha(O/'probe.wasm'),command=cmd,gameSource='b8e36ef27d96238352f5edaf9b368ca23394ceb3',completeGame=False)
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(wasmSha256=report['wasmSha256'],normalAccessControl=True)))
