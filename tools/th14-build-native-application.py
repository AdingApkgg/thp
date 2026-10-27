"""Compile the real SDL Application and devices for a native offscreen unit host.

SDL's public header declarations remain intact. The host will supply platform
I/O, clocks and callback scheduling; no browser or other application is driven.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess

R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--core-build',type=Path,required=True)
parser.add_argument('--backend',choices=['gles','webgpu'],default='gles')
parser.add_argument('--title-observer',action='store_true',help='Export read-only title age, startup inputs and RNG state; run the unchanged production tick')
args=parser.parse_args();O=args.output.resolve()
assert O.is_relative_to((R/'artifacts/th14').resolve())and not O.exists()
O.mkdir(parents=True);inc=O/'include';inc.mkdir();src=R/'runtimes/th12/th12_web/cpp/sdl'
spec=importlib.util.spec_from_file_location('test_storage',R/'tools/th14-test-storage.py')
storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(O)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
core_raw=args.core_build.read_bytes();build=json.loads(core_raw)
assert build['compiled']and build['readOnlyObserver']and len(build['objectBindings'])==141

for row in build['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
headers=R/'runtimes/th12/tools/emsdk/upstream/emscripten/cache/sysroot/include'
for name in ['SDL3','GLES3','KHR']:shutil.copytree(headers/name,inc/name)
(inc/'emscripten').mkdir()
(inc/'malloc.h').write_text('''#pragma once
#include_next <malloc.h>
// This diagnostics-only API is not exported by the component. A declaration
// lets the untouched Application compile; there is no fabricated statistic.
struct mallinfo {int uordblks;};
extern "C" struct mallinfo mallinfo();
''')
(inc/'emscripten.h').write_text('''#pragma once
#include <cstddef>
#define __EMSCRIPTEN__ 1
#define EMSCRIPTEN_KEEPALIVE __attribute__((visibility("default")))
#define EM_JS(ret,name,args,...) extern "C" ret name args
using EM_BOOL=int;
#define EM_TRUE 1
#define EM_FALSE 0
extern "C" double emscripten_get_now();
extern "C" void emscripten_async_call(void(*)(void*),void*,int);
''')
(inc/'emscripten/heap.h').write_text('''#pragma once
#include <cstddef>
inline std::size_t emscripten_get_heap_size(){return __builtin_wasm_memory_size(0)*65536u;}
''')
(inc/'emscripten/html5.h').write_text('''#pragma once
#include <emscripten.h>
extern "C" int emscripten_request_animation_frame_loop(EM_BOOL(*)(double,void*),void*);
''')
fixture='''#include "Application.cpp"
extern "C" {
EMSCRIPTEN_KEEPALIVE int component_initialize(){return th11::sdl::app.initialize();}
EMSCRIPTEN_KEEPALIVE int component_tick(unsigned held,unsigned pause){return th11::sdl::app.tick(held,pause!=0);}
EMSCRIPTEN_KEEPALIVE const unsigned* component_state(){using namespace th11;auto& a=th11::sdl::app;auto& s=a.session;static unsigned data[20];
data[0]=unsigned(s.state.phase);data[1]=s.state.stage;data[2]=s.state.frame;
data[3]=s.title?unsigned(s.title->screen):~0u;data[4]=s.title?unsigned(s.title->cursor.selected):~0u;data[5]=s.title?unsigned(s.title->substate):~0u;
data[6]=s.battle?s.battle->frame:0;data[7]=unsigned(s.economy.lives);data[8]=unsigned(s.economy.power);data[9]=unsigned(s.economy.score_units);
data[10]=s.battle?unsigned(s.battle->hud.score.continues):0;data[11]=s.pause_menu?unsigned(s.pause_menu->state):~0u;data[12]=s.pause_menu?unsigned(s.pause_menu->cursor.selected):~0u;
data[13]=unsigned(s.state.character);data[14]=unsigned(s.state.subtype);data[15]=unsigned(s.state.difficulty);data[16]=s.stage_load_host_flags;data[17]=a.fonts.writes;data[18]=unsigned(a.audio.current_music());data[19]=a.initialized;
return data;}
EMSCRIPTEN_KEEPALIVE const unsigned char* component_pixels(){auto& g=th11::sdl::app.graphics;g.backend.read(g.screen);auto* pixels=g.pixels(g.screen);return pixels?pixels->pixels.data():nullptr;}
EMSCRIPTEN_KEEPALIVE void component_audio_close(){th11::sdl::app.audio.close();}
}
'''
title_fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-native-title-fixture.cpp'
if args.title_observer:fixture=title_fixture.read_text()
(O/'fixture.cpp').write_text(fixture)
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-DTH_NATIVE_PLATFORM=1','-DTH11_DEVELOPMENT_HARNESS=0','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-I'+str(inc),'-I'+str(src)]
if args.backend=='webgpu':flags.append('-DTH14_WEBGPU_BACKEND=1')
if args.title_observer:
 flags.extend(['-fno-access-control','-I'+str(title_fixture.parent)]) # Read private title_idle; no state override.
units=[O/'fixture.cpp',src/'AudioDevice.cpp',src/'FontDevice.cpp',src/'GraphicsDevice.cpp',R/'runtimes/th12/portable/sdl/Renderer.cpp'];objects=[];bindings={}
for unit in units:
 raw=unit.read_bytes();bindings[unit.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));obj=O/(unit.stem+'.o');result=subprocess.run([str(compiler),*flags,'-c',str(unit),'-o',str(obj)],cwd=R,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)},capture_output=True);(O/(unit.stem+'.compile.log')).write_bytes(result.stdout+result.stderr)
 assert result.returncode==0,(O/(unit.stem+'.compile.log')).read_text()[-6000:]
 objects.append(obj);print('compiled',unit.name,flush=True)
exports=['component_initialize','component_tick','component_state','component_pixels','component_audio_close','th11_error','th11_last_resource','malloc','free']
if args.title_observer:exports.extend(['component_reference_state','component_live_state'])
linkflags=['-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,--export-table','-Wl,--allow-undefined','-Wl,-z,stack-size=1048576',*[f'-Wl,--export={name}'for name in exports]]
result=subprocess.run([str(compiler),*flags,*linkflags,*[str(p)for p in objects],*[row['path']for row in build['objectBindings']],'-o',str(O/'application.wasm')],cwd=R,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)},capture_output=True);(O/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,(O/'link.log').read_text()[-6000:]
# Bind the included production Application and all project headers. Reused game
# object provenance stays attached to its original frozen core build.
project_headers=[path for home in [src.parent,R/'runtimes/th12/portable/sdl',R/'runtimes/th12/portable/input']for path in sorted(home.rglob('*'))if path.is_file()and path.suffix in ['.h','.hpp','.inc']]
for source in [src/'Application.cpp',*project_headers]:
 raw=source.read_bytes();bindings[source.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
if args.title_observer:
 for source in [title_fixture,title_fixture.parent/'th14-native-title-live-observer.hpp']:
  raw=source.read_bytes();bindings[source.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw))
if args.backend=='webgpu':
 (O/'shaders').mkdir()
 for name in ['Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']:
  source=R/'runtimes/th12/portable/sdl'/name;raw=source.read_bytes();bindings[source.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=sha(raw));(O/'shaders'/name).write_bytes(raw)
names=set(re.findall(r'\b(gl[A-Z][A-Za-z0-9_]*)\s*\(', (R/'runtimes/th12/portable/sdl/Renderer.cpp').read_text()+(R/'runtimes/th12/portable/sdl/AlphaConversion.hpp').read_text()))
prototypes={}
for result,name,arguments in re.findall(r'GL_APICALL\s+([^;]+?)\s+GL_APIENTRY\s+(gl\w+)\s*\(([^;]+?)\);',(inc/'GLES3/gl3.h').read_text()):
 if name not in names:continue
 parameters=[]
 if arguments.strip()!='void':
  for argument in arguments.split(','):
   match=re.match(r'(.+?)([A-Za-z_]\w*)$',argument.strip());assert match,(name,argument);parameters.append(match[1].strip())
 prototypes[name]=dict(result=result.strip(),args=parameters)
assert names==set(prototypes)
signatures=json.dumps(prototypes,indent=2)+'\n';(O/'gl-signatures.json').write_text(signatures)
report=dict(schema='th14/native-application-build/1',backend=args.backend,toolSha256=sha(Path(__file__).read_bytes()),coreBuildSha256=sha(core_raw),coreSourceHashes=build['sourceHashes'],glSignaturesSha256=sha((O/'gl-signatures.json').read_bytes()),compiled=True,sourceBindings=bindings,productionSourceFilesUnmodified=True,wasmSha256=sha((O/'application.wasm').read_bytes()),compilerSha256=sha(compiler.read_bytes()),flags=flags,linkFlags=linkflags,coreWasmSha256=build['wasmSha256'],coreObjects=build['objectBindings'],newObjects={p.name:sha(p.read_bytes())for p in objects},headerFiles={str(p.relative_to(inc)):sha(p.read_bytes())for p in inc.rglob('*')if p.is_file()},exports=exports,browserAcceptance=False,productionChanged=False,scope='Actual production Application, graphics, font, audio and C++ renderer; only platform I/O is imported into an independent native unit host. Compilation is not runtime or browser acceptance.')
report['readOnlyReferenceStateExport']=args.title_observer
(O/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('linked',len((O/'application.wasm').read_bytes()))
(O/'build-tool.py').write_bytes(Path(__file__).read_bytes())
