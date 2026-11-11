"""Build the silent Control/rate loading comparison with current game objects."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--providers', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provider_path = args.providers.resolve() / 'build.json'
    provider = json.loads(provider_path.read_text())
    assert provider['normalEngineAccessControl']
    for path, digest in provider['sourceBindings'].items():
        assert sha(ROOT / path) == digest, path
    for row in provider['currentProviders']:
        assert sha(Path(row['object'])) == row['objectSha256']
    # Preserve the canonical observer's definitions without its private-registry
    # reader. This fixture walks public VM links and uses normal access control.
    observer = ROOT / 'runtimes/th12/th12_web/tests/cpp/th14-native-title-live-observer.hpp'
    observer_source = observer.read_text()
    helper = observer_source.split('inline void capture_live_rows(')[0]
    start = observer_source.index('   std::vector<u32> row={')
    stop = observer_source.index('rows.push_back(std::move(row));', start)
    canonical = ('namespace th14_title_observer {static std::vector<u32> canonical_transition(const AnmVm* vm){\n'
                 + observer_source[start:stop] + '\nreturn row;}}\n')
    source = '''#include "AnmManager.hpp"
#include "LoadingTh14.hpp"
#include "ControlStateTh14.hpp"
#include <cstdlib>
#include <algorithm>
using namespace th11;
u32 float_bits(float f){u32 w;std::memcpy(&w,&f,4);return w;}
'''+helper+'\n}\n'+canonical+'''
#define API(n) extern "C" __attribute__((export_name(#n)))
namespace {
AnmResource ascii;
std::unique_ptr<AnmManager> owner;
LoadingTh14 loading;
ControlStateTh14 control;
std::vector<AnmVm*> seen;
std::vector<u32> words;
u32 failure[8]{};
}
API(allocate) void* allocate(u32 n){return std::malloc(n);}
API(release) void release(void* p){std::free(p);}
API(setup) u32 setup(const u8* bytes,u32 size){return ascii.open(bytes,size);}
API(begin) u32 begin(float rate){
 owner=std::make_unique<AnmManager>();auto& a=*owner;
 a.rate=rate;a.fallback_sprites=&ascii;
 control.flags=0;a.th14_control.publish(control);
 if(!a.prepare_resource(ascii,2))return 0;
 a.script_rng={12345,0,0};a.visual_rng={54321,0,0};
 seen.clear();loading.handle=0;
 a.before_initial_update=[](const AnmVm& v){
  auto* p=const_cast<AnmVm*>(&v);
  if(std::find(seen.begin(),seen.end(),p)==seen.end())seen.push_back(p);
  return true;
 };
 return loading.begin(a,ascii);
}
API(step) u32 step(u32 frame,u32 finish,u32 flags){
 auto& a=*owner;control.flags=flags;
 failure[0]=0;failure[1]=frame;failure[2]=a.active_count();failure[3]=u32(seen.size());
 if(frame){if(frame==finish)loading.finish(a);if(!a.update(true)||!a.update(false))return 0;}
 words={frame,a.active_count(),a.script_rng.seed_value(),a.script_rng.call_count(),a.visual_rng.seed_value(),a.visual_rng.call_count()};
 std::vector<const AnmVm::Node*> heads;
 for(auto* p:seen)if(p->id&&a.find(p->id)==p){
  const auto* node=&p->registry;
  for(u32 budget=0;node->previous&&budget<64;++budget)node=node->previous;
  if(std::find(heads.begin(),heads.end(),node)==heads.end())heads.push_back(node);
 }
 u32 count=0;
 for(const auto* node:heads){
  for(;node;node=node->next){
   failure[4]=++count;if(count>64){failure[0]=1;return 0;}
   auto row=th14_title_observer::canonical_transition(node->value);
   failure[5]=u32(row.size());if(row.size()!=303){failure[0]=2;return 0;}words.insert(words.end(),row.begin(),row.end());
  }
 }
 if(count!=a.active_count()){failure[0]=3;return 0;}
 return u32(words.size());
}
API(data) const u32* data(){return words.data();}
API(failure_data) const u32* failure_data(){return failure;}
API(close) void close(){if(owner)owner->th14_control.retire(control);owner.reset();seen.clear();}
'''
    fixture = output / 'fixture.cpp'
    fixture.write_text(source, encoding='utf8')
    compiler = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    assert sha(compiler) == provider['compilerSha256']
    command = [str(compiler), *provider['flags'], '-mexec-model=reactor', '-Wl,--no-entry',
               '-Wl,--import-memory', '-Wl,--export-memory', '-Wl,--allow-undefined',
               '-Wl,--initial-memory=67108864', '-Wl,--max-memory=1073741824',
               '-Wl,-z,stack-size=1048576', str(fixture),
               *[row['object'] for row in provider['currentProviders']], '-o', str(output / 'probe.wasm')]
    with (output / 'build.log').open('wb') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                env=dict(os.environ, TMP=str(output), TEMP=str(output), TMPDIR=str(output)), timeout=240)
    if result.returncode:
        raise RuntimeError((output / 'build.log').read_text()[-4000:])
    tracked = [observer, Path(__file__), provider_path, fixture]
    report = dict(providerBuild=str(provider_path), providerBuildSha256=sha(provider_path),
                  gameObjectsReused=len(provider['currentProviders']), sourceBindings=provider['sourceBindings'],
                  observerBindings={p.relative_to(ROOT).as_posix(): sha(p) for p in tracked},
                  fixtureNormalAccessControl=True, privateRegistryAccess=False, wasmSha256=sha(output / 'probe.wasm'),
                  compilerSha256=sha(compiler), command=command, completeGame=False)
    (output / 'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['gameObjectsReused', 'fixtureNormalAccessControl', 'wasmSha256']}))


if __name__ == '__main__':
    main()
