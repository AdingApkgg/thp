"""Build the current TH14 C++ renderer as an offscreen WASI/GLES component.

The SDL lifetime shim creates no real window, input source or audio device.
Graphics calls remain imports and are executed by th14-native-gles-component.py.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
SOURCES = ['Renderer.cpp', 'Renderer.hpp', 'GraphicsState.hpp', 'Shaders.hpp',
           'AlphaConversion.hpp', 'ResampleShader.hpp']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('test_storage', ROOT / 'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(storage)
    storage.check_budget(out, 100 * 1024**3, 2 * 1024**3)
    src, inc = out / 'src', out / 'include'
    src.mkdir()
    (inc / 'SDL3').mkdir(parents=True)
    bindings = {}
    for name in SOURCES:
        path = ROOT / 'runtimes/th12/portable/sdl' / name
        raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw))
        (src / name).write_bytes(raw)
    fixture_path = ROOT / 'runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp'
    fixture_bytes = fixture_path.read_bytes()
    bindings[fixture_path.relative_to(ROOT).as_posix()] = dict(bytes=len(fixture_bytes), sha256=SHA(fixture_bytes))
    fixture = fixture_bytes.decode().replace('#include "../../../portable/sdl/Renderer.hpp"', '#include "Renderer.hpp"')
    assert fixture != fixture_bytes.decode()
    (src / 'fixture.cpp').write_text(fixture)
    headers = ROOT / 'runtimes/th12/tools/emsdk/upstream/emscripten/cache/sysroot/include'
    for folder in ['GLES3', 'KHR']:
        shutil.copytree(headers / folder, inc / folder)
    (inc / 'emscripten.h').write_text('''#pragma once
#define __EMSCRIPTEN__ 1
#define EMSCRIPTEN_KEEPALIVE __attribute__((visibility("default")))
#define EM_JS(ret,name,args,...) extern "C" ret name args
''')
    (inc / 'SDL3/SDL.h').write_text('''#pragma once
#include <cstdint>
struct SDL_Window{};using SDL_GLContext=void*;struct SDL_Event{};
constexpr int SDL_INIT_VIDEO=1,SDL_INIT_EVENTS=2,SDL_WINDOW_OPENGL=4;
constexpr int SDL_GL_CONTEXT_PROFILE_MASK=1,SDL_GL_CONTEXT_PROFILE_ES=2,SDL_GL_CONTEXT_MAJOR_VERSION=3,SDL_GL_CONTEXT_MINOR_VERSION=4,SDL_GL_ALPHA_SIZE=5,SDL_GL_DEPTH_SIZE=6,SDL_GL_STENCIL_SIZE=7,SDL_GL_DOUBLEBUFFER=8;
#define SDL_HINT_EMSCRIPTEN_CANVAS_SELECTOR "canvas"
inline bool SDL_Init(int){return true;}inline const char* SDL_GetError(){return "Standalone GLES unit boundary";}
inline bool SDL_GL_SetAttribute(int,int){return true;}
inline SDL_Window* SDL_CreateWindow(const char*,int,int,int){static SDL_Window window;return &window;}
inline bool SDL_SetWindowSize(SDL_Window*,int,int){return true;}
inline SDL_GLContext SDL_GL_CreateContext(SDL_Window*){return reinterpret_cast<void*>(1);}
inline bool SDL_GL_SetSwapInterval(int){return true;}inline void SDL_GL_DestroyContext(SDL_GLContext){}
inline void SDL_DestroyWindow(SDL_Window*){}inline void SDL_Quit(){}inline bool SDL_GL_SwapWindow(SDL_Window*){return true;}
inline int SDL_GetVersion(){return 3000000;}inline std::uint64_t SDL_GetTicksNS(){return 0;}
inline bool SDL_SetHint(const char*,const char*){return true;}inline bool SDL_PollEvent(SDL_Event*){return false;}
''')
    names = set(re.findall(r'\b(gl[A-Z][A-Za-z0-9_]*)\s*\(', (src / 'Renderer.cpp').read_text() + (src / 'AlphaConversion.hpp').read_text()))
    prototypes = {}
    for result, name, arguments in re.findall(r'GL_APICALL\s+([^;]+?)\s+GL_APIENTRY\s+(gl\w+)\s*\(([^;]+?)\);', (inc / 'GLES3/gl3.h').read_text()):
        if name not in names:
            continue
        parameters = []
        if arguments.strip() != 'void':
            for argument in arguments.split(','):
                match = re.match(r'(.+?)([A-Za-z_]\w*)$', argument.strip())
                assert match, (name, argument)
                parameters.append(match[1].strip())
        prototypes[name] = dict(result=result.strip(), args=parameters)
    assert names == set(prototypes), names - set(prototypes)
    (out / 'gl-signatures.json').write_text(json.dumps(prototypes, indent=2) + '\n')
    compiler = ROOT / 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    exports = re.findall(r'EMSCRIPTEN_KEEPALIVE\s+[^;{]+?\b(gpu_\w+)\s*\(', fixture)
    assert len(exports) == 16
    flags = ['--target=wasm32-wasip1', '-DPORT_TITLE=14', '-std=c++17', '-O2', '-g0', '-ffp-contract=off', '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti', '-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--export-memory', '-Wl,--allow-undefined', '-Wl,-z,stack-size=1048576', '-I' + str(inc), '-I' + str(src), *[f'-Wl,--export={name}' for name in exports]]
    result = subprocess.run([str(compiler), *flags, str(src / 'fixture.cpp'), str(src / 'Renderer.cpp'), '-o', str(out / 'probe.wasm')], cwd=ROOT, env={**os.environ, 'TEMP': str(out), 'TMP': str(out), 'TMPDIR': str(out)}, capture_output=True)
    (out / 'compile.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, (out / 'compile.log').read_text()
    report = dict(sourceBindings=bindings, wasmSha256=SHA((out / 'probe.wasm').read_bytes()), compilerSha256=SHA(compiler.read_bytes()), sourceFiles={path.name: SHA(path.read_bytes()) for path in src.iterdir()}, shimFiles={path.relative_to(inc).as_posix(): SHA(path.read_bytes()) for path in inc.rglob('*') if path.is_file()}, signaturesSha256=SHA((out / 'gl-signatures.json').read_bytes()), toolSha256=SHA(Path(__file__).read_bytes()), flags=flags, glFunctions=len(prototypes), originalRendererSourcesUnmodified=True, renderProfile='WebGL upload branch, deterministic SDL lifetime shim, imported native GLES; no browser context', browserRun=False, productionChanged=False)
    (out / 'build.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(wasmBytes=(out / 'probe.wasm').stat().st_size, glFunctions=len(prototypes), wasmSha256=report['wasmSha256'])))


if __name__ == '__main__':
    main()
