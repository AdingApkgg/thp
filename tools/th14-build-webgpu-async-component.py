"""Build actual C++ Renderer + Emscripten Asyncify for a windowless GPU unit.

The declared SDL lifetime boundary creates no OS window or browser DOM. This is
not a browser test; the real JavaScript WebGPU host can run in a native runtime.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lifetime-shim-build', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, default=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp')
    args = parser.parse_args(); out = args.output.resolve(); shim_home = args.lifetime_shim_build.resolve(strict=True)
    assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists()
    fixture_path = args.fixture.resolve(strict=True); assert fixture_path.is_relative_to(ROOT/'runtimes/th12/th12_web/tests/cpp')
    out.mkdir(parents=True)
    spec = importlib.util.spec_from_file_location('storage', ROOT/'tools/th14-test-storage.py')
    storage = importlib.util.module_from_spec(spec); spec.loader.exec_module(storage); storage.check_budget(out)
    shim_build_raw = (shim_home/'build.json').read_bytes(); shim_build = json.loads(shim_build_raw)
    shim = (shim_home/'include/SDL3/SDL.h').read_bytes(); assert SHA(shim) == shim_build['shimFiles']['SDL3/SDL.h']
    (out/'include/SDL3').mkdir(parents=True); (out/'include/SDL3/SDL.h').write_bytes(shim)
    src = out/'src'; src.mkdir(); bindings = {}
    names = ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','ResampleShader.hpp','AlphaConversion.hpp',
             'Th14RenderMath.hpp','WebGpuRenderer.hpp','Th14WebGpuCallbacks.hpp',
             'Th14WebGpuHost.mjs','Th14WebGpuRuntime.mjs','Th14WebGpuCore.mjs','Th14WebGpuLibrary.js','Th14WebGpu.wgsl','Th14WebGpuResample.wgsl',
             'Th14ArchiveDecodeClient.mjs','Th14ArchiveReadAhead.mjs']
    for name in names:
        path = ROOT/'runtimes/th12/portable/sdl'/name; raw = path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw), sha256=SHA(raw)); (src/name).write_bytes(raw)
        if path.suffix in ['.mjs','.wgsl']: (out/name).write_bytes(raw)
    raw = fixture_path.read_bytes(); bindings[fixture_path.relative_to(ROOT).as_posix()] = dict(bytes=len(raw),sha256=SHA(raw))
    fixture = raw.decode().replace('#include "../../../portable/sdl/Renderer.hpp"','#include "Renderer.hpp"')
    (src/'fixture.cpp').write_text(fixture)
    (src/'unit-post.js').write_text('Module["th14TestUpdateViews"] = () => updateMemoryViews();\nModule["th14TestMemory"] = () => wasmMemory;\n')
    exports = re.findall(r'EMSCRIPTEN_KEEPALIVE\s+[^;{]+?\b((?:gpu_|th11_)\w+)\s*\(', fixture)
    if 'Th14WebGpuCallbacks.hpp' in fixture:
        exports.extend(['th14_webgpu_invoke','th14_webgpu_frame'])
    assert exports and len(exports) == len(set(exports))
    sdk = ROOT/'runtimes/th12/tools/emsdk'
    flags = ['-DPORT_TITLE=14','-DTH14_WEBGPU_BACKEND=1','-O2','-g0','-std=c++17','-ffp-contract=off',
             '-fno-strict-aliasing','-fno-exceptions','-fno-rtti','--no-entry','-sDEFAULT_TO_CXX=1',
             '-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=node','-sALLOW_MEMORY_GROWTH=1',
             '-sINITIAL_MEMORY=67108864','-sMAXIMUM_MEMORY=1073741824','-sSTACK_SIZE=1048576',
             '-sASYNCIFY=1','-sASYNCIFY_STACK_SIZE=65536','-sASSERTIONS=1',
             '-sINCOMING_MODULE_JS_API=wasmBinary,noInitialRun,print,printErr,locateFile,onRuntimeInitialized,onAbort',
             '-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2',
             '-sEXPORTED_RUNTIME_METHODS=ccall,HEAPU8,HEAP32,HEAPU32',
             '-sEXPORTED_FUNCTIONS='+','.join('_'+name for name in exports),
             '--js-library',str(src/'Th14WebGpuLibrary.js'),'--post-js',str(src/'unit-post.js'),'-I'+str(out/'include'),'-I'+str(src)]
    command = [__import__('sys').executable,str(sdk/'upstream/emscripten/emcc.py'),*flags,str(src/'fixture.cpp'),str(src/'Renderer.cpp'),'-o',str(out/'component.mjs')]
    env = {**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out),'EMCC_CORES':'2',
           'EMSDK_PYTHON':__import__('sys').executable,'PATH':str(Path(__import__('sys').executable).parent)+os.pathsep+os.environ.get('PATH','')}
    result = subprocess.run(command,cwd=ROOT,env=env,capture_output=True); (out/'compile.log').write_bytes(result.stdout+result.stderr)
    assert result.returncode == 0, (out/'compile.log').read_text()[-6000:]
    report = dict(schema='th14/emscripten-webgpu-component-build/1',sourceBindings=bindings,
        sourceFiles={path.name:dict(bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))for path in src.iterdir()if path.is_file()},
        fixture=fixture_path.relative_to(ROOT).as_posix(),exports=exports,flags=flags,
        wasmSha256=SHA((out/'component.wasm').read_bytes()),loaderSha256=SHA((out/'component.mjs').read_bytes()),
        shimBuildSha256=SHA(shim_build_raw),sdlLifetimeShimSha256=SHA(shim),toolSha256=SHA(Path(__file__).read_bytes()),
        compilerVersion=(sdk/'upstream/emscripten/emscripten-version.txt').read_text().strip(),
        actualCppRenderer=True,asyncify=True,realSdlWindow=False,physicalAudioDevicesOpened=0,browserRun=False,
        browserAcceptance=False,completeGame=False,nativeEquivalent=False)
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(dict(wasmBytes=(out/'component.wasm').stat().st_size,wasmSha256=report['wasmSha256'])))
    (out/'build-tool.py').write_bytes(Path(__file__).read_bytes())


if __name__ == '__main__': main()
