"""Build actual Player initialization with normal current SDK providers."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/player-initialization-oracle-nov13'
O = H / 'candidate-component'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
O.mkdir(exist_ok=False)
provider_path = H / 'candidate-providers/build.json'
provider = json.loads(provider_path.read_bytes())
assert provider['normalEngineAccessControl']
for name, digest in provider['sourceBindings'].items():
    assert sha(R / name) == digest, name
for row in provider['currentProviders']:
    assert sha(R / row['object']) == row['objectSha256']
observer = R / 'tools/th14-anm-template303-fixture-nov10.inc'
helper = observer.read_text().split('static std::vector<u32> expanded_template_capture;')[0]
source = '''#include "PlayerFrame.hpp"
#include <cstdlib>
using namespace th11;
''' + helper + '''
#define API(n) extern "C" __attribute__((export_name(#n)))
struct World final:PlayerFrameWorld{};
struct Probe {
 AnmManager animations;
 AnmResource ascii,anm,bullet;
 ShtResource sht;
 GameEconomy economy;
 World world;
 std::unique_ptr<PlayerFrame> player;
};
std::unique_ptr<Probe> probe;
std::vector<u32> words;
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(reset) void reset(){probe=std::make_unique<Probe>();}
API(resource_open) u32 resource_open(u32 kind,const u8* bytes,u32 size){
 auto& p=*probe;
 if(kind==0){if(!p.ascii.open(bytes,size))return 0;p.animations.fallback_sprites=&p.ascii;
  p.animations.script_rng={12345,0,0};p.animations.visual_rng={54321,0,0};return p.animations.prepare_resource(p.ascii,2);}
 if(kind==1){if(!p.anm.open(bytes,size))return 0;
  p.animations.script_rng={12345,0,0};p.animations.visual_rng={54321,0,0};return p.animations.prepare_resource(p.anm,9);}
 if(kind==2)return p.sht.open(bytes,size);
 return 0;
}
API(initialize) u32 initialize(u32 slot){
 auto& p=*probe;
 p.player=std::make_unique<PlayerFrame>(p.sht,p.anm,p.bullet,p.animations,p.economy,p.world,9,7);
 auto& f=*p.player;f.input.movement.character=slot/2;f.input.movement.subtype=slot%2;
 if(!f.initialize())return 0;
 auto& s=f.motion.state;
 const auto bits=[](float v){u32 x;std::memcpy(&x,&v,4);return x;};
 words={bits(s.position.x),bits(s.position.y),bits(s.position.z),u32(s.x),u32(s.y),u32(s.normal_speed),
        u32(s.focus_speed),u32(s.normal_diagonal),u32(s.focus_diagonal),u32(f.state.life_state)};
 for(const Timer* t:{&f.state.state_timer,&f.state.transition_timer,&f.state.th14_shooting_age,
                    &f.state.invincibility,&f.shots.schedule.timer}){
  words.insert(words.end(),{u32(t->previous),u32(t->current),bits(t->fractional),u32(t->rate!=nullptr),t->flags});
 }
 words.insert(words.end(),{u32(p.economy.max_power),u32(p.economy.power_step),p.animations.script_rng.seed_value(),
             p.animations.script_rng.call_count(),p.animations.visual_rng.seed_value(),p.animations.visual_rng.call_count()});
 static_assert(sizeof(p.sht.header)==640);
 for(u32 at=0;at<sizeof(p.sht.header);at+=4){u32 w;std::memcpy(&w,reinterpret_cast<const u8*>(&p.sht.header)+at,4);words.push_back(w);}
 const auto body=th14_title_observer::canonical_transition(&f.motion.body);words.insert(words.end(),body.begin(),body.end());
 return words.size();
}
API(data) const u32* data(){return words.data();}
API(close) void close(){probe.reset();}
'''
fixture = O / 'fixture.cpp'
fixture.write_text(source, encoding='utf8', newline='\n')
cc = R / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc) == provider['compilerSha256']
command = [str(cc), *provider['flags'], '-mexec-model=reactor', '-Wl,--no-entry',
           '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
           '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824', '-Wl,-z,stack-size=1048576',
           str(fixture), *[r['object'] for r in provider['currentProviders']], '-o', str(O / 'probe.wasm')]
assert '-fno-access-control' not in command
with (O / 'build.log').open('wb') as log:
    subprocess.run(command, cwd=R, env=dict(os.environ, TEMP=str(O), TMP=str(O), TMPDIR=str(O)),
                   stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
report = dict(providerBuild=str(provider_path), providerBuildSha256=sha(provider_path),
              sourceBindings=provider['sourceBindings'], objectBindings={r['object']: r['objectSha256'] for r in provider['currentProviders']},
              observerBindings={p.relative_to(R).as_posix(): sha(p) for p in [Path(__file__), fixture, observer]},
              command=command, normalAccessControl=True, gameObjectsReused=141,
              wasmSha256=sha(O / 'probe.wasm'), gameSourceBase='84b8741af5b7ca617cc4046fe697d3cbfebbf4ad', nullRateCandidate=True, completeGame=False)
(O / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(wasmSha256=report['wasmSha256'], normalAccessControl=True)))
