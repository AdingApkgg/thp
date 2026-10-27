"""Build a TH14 browser WebGPU candidate from a published source snapshot.

Only explicit TH14 work overlays the clean courier. No retail data, baked
assets, save files or unrelated worktree edits enter the source snapshot.
Compilation alone is not browser or complete-game acceptance.
"""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
OVERLAYS = ['th12_web/cpp/sdl/Application.cpp','portable/sdl/Th14WebGpuCallbacks.hpp',
            'portable/sdl/Th14WebGpuHost.mjs','portable/sdl/Th14WebGpuRuntime.mjs','portable/sdl/Th14WebGpuCore.mjs','portable/sdl/Th14WebGpuLibrary.js']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse-build',type=Path,help='Reuse unchanged translation units only when the complete header inventory and compiler flags match')
    args = parser.parse_args(); out = args.output.resolve(); courier = ROOT/'tools/tmp/github-source-release'; tool_raw = Path(__file__).read_bytes()
    assert out.is_relative_to(ROOT/'artifacts/th14') and not out.exists()
    assert subprocess.check_output(['git','-C',str(courier),'rev-parse','HEAD'],text=True).strip() == args.base_commit
    assert not subprocess.check_output(['git','-C',str(courier),'status','--porcelain'],text=True).strip()
    out.mkdir(parents=True)
    storage_raw = (ROOT/'tools/th14-test-storage.py').read_bytes()
    (out/'storage-tool.py').write_bytes(storage_raw)
    storage_path = ROOT/'tools/th14-test-storage.py'
    spec = importlib.util.spec_from_file_location('storage', storage_path)
    storage = importlib.util.module_from_spec(spec)
    # Execute the captured bytes with their original source location so the
    # helper's workspace root stays correct without rereading a mutable file.
    exec(compile(storage_raw,str(storage_path),'exec'),storage.__dict__)
    storage.check_budget(out)
    source = out/'source'; objects = out/'objects'; objects.mkdir()
    inventory = {}
    base = courier/'runtimes/th12'
    for directory in ['th12_web/cpp/game','th12_web/cpp/sdl','portable/sdl','portable/input']:
        for path in sorted((base/directory).rglob('*')):
            if not path.is_file() or path.suffix not in ['.cpp','.h','.hpp','.inc','.wgsl']: continue
            relative = path.relative_to(base).as_posix(); raw = path.read_bytes(); target = source/relative
            target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
            inventory[relative] = dict(bytes=len(raw),sha256=SHA(raw),origin='published-base')
    for relative in OVERLAYS:
        path = ROOT/'runtimes/th12'/relative; raw = path.read_bytes(); target = source/relative
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        inventory[relative] = dict(bytes=len(raw),sha256=SHA(raw),origin='explicit-th14-overlay')
    crypt = 'th12_web/cpp/game/ResourceCrypt.cpp'
    assert inventory[crypt]['sha256'] == 'd57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    for name in ['Th14WebGpuHost.mjs','Th14WebGpuRuntime.mjs','Th14WebGpuCore.mjs','Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']:
        shutil.copyfile(source/'portable/sdl'/name, out/name)
    sdk = ROOT/'runtimes/th12/tools/emsdk'; emcc = sdk/'upstream/emscripten/emcc.py'
    flags = ['-O2','-g0','--profiling-funcs','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',
             '-DPORT_TITLE=14','-DTH_NATIVE_PLATFORM=1','-DTH11_DEVELOPMENT_HARNESS=0','-DTH14_WEBGPU_BACKEND=1','--use-port=sdl3']
    (out/'build-tool.py').write_bytes(tool_raw)
    (out/'compile-inputs.json').write_text(json.dumps(dict(baseCommit=args.base_commit,sourceBindings=inventory,flags=flags,toolSha256=SHA(tool_raw)),indent=2)+'\n')
    env = {**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,
           'PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH',''),
           'EMCC_CORES':'2','TEMP':str(objects),'TMP':str(objects),'TMPDIR':str(objects)}
    units = sorted((source/'th12_web/cpp/game').rglob('*.cpp')) + sorted((source/'th12_web/cpp/sdl').rglob('*.cpp')) + [source/'portable/sdl/Renderer.cpp']
    def compile_unit(unit):
        relative = unit.relative_to(source).as_posix(); name = relative.replace('/','_')+'.o'; target = objects/name
        result = subprocess.run([sys.executable,str(emcc),*flags,'-c',str(unit),'-o',str(target)],cwd=source/'th12_web',env=env,capture_output=True)
        (objects/(name+'.log')).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, (objects/(name+'.log')).read_text()[-6000:]
        return target
    compiled = {}; reused = {}; reuse_report_sha = None
    if args.reuse_build:
        previous=args.reuse_build.resolve(strict=True);assert previous.is_relative_to(ROOT/'artifacts/th14')
        previous_raw=(previous/'build.json').read_bytes();before=json.loads(previous_raw);reuse_report_sha=SHA(previous_raw)
        assert before['compiled']and before['flags']==flags and before['compilerVersion']==(sdk/'upstream/emscripten/emscripten-version.txt').read_text().strip()
        cpp_inputs={path:row['sha256']for path,row in inventory.items()if Path(path).suffix in ['.cpp','.h','.hpp','.inc']}
        old_cpp_inputs={path:row['sha256']for path,row in before['sourceBindings'].items()if Path(path).suffix in ['.cpp','.h','.hpp','.inc']}
        assert set(cpp_inputs)==set(old_cpp_inputs),'C++ input inventory changed: cached objects cannot be reused'
        changed_inputs={path for path,digest in cpp_inputs.items()if digest!=old_cpp_inputs[path]}
        assert all(Path(path).suffix=='.cpp'for path in changed_inputs),'Headers changed: cached objects cannot be reused'
        unit_names={unit.relative_to(source).as_posix()for unit in units}
        assert changed_inputs<=unit_names,'Included C++ input changed: cached objects cannot be reused'
        # A complete unchanged header inventory isolates each changed .cpp
        # only if no other project input textually includes a .cpp file.
        if changed_inputs:
            for path in cpp_inputs:
                assert not re.search(r'^\s*#\s*include\s*[<\"][^>\"]*\.cpp[>\"]',(source/path).read_text(),re.M),path
        for unit in units:
            key=unit.relative_to(source).as_posix();name=key.replace('/','_')+'.o';original=previous/'objects'/name;target=objects/name
            if key in changed_inputs:continue
            digest=SHA(original.read_bytes());assert digest==before['objectHashes'][key]
            os.link(original,target);compiled[unit]=target;reused[key]=digest
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(compile_unit,unit):unit for unit in units if unit not in compiled}
        try:
            for future in concurrent.futures.as_completed(futures):
                unit = futures[future]; compiled[unit] = future.result()
                storage.check_budget(out)
                (out/'progress.json').write_text(json.dumps(dict(phase='compile',compiled=len(compiled),total=len(units)))+'\n')
                if len(compiled)%16 == 0: print('compiled',len(compiled),'/',len(units),flush=True)
        except BaseException:
            for future in futures: future.cancel()
            raise
    exports = ['malloc','free',*['th11_'+name for name in ['validate_file','save_scores','save_replay','initialize','last_resource','music_enabled','audio_statistics','return_title','restart','error','frame','phase','pause','resume','loop_start','loop_stop','loop_pause','key','keys_clear','touch','touch_cancel','touch_options','touch_controls','touch_stick']],
               'th14_webgpu_invoke','th14_webgpu_frame']
    link_flags = ['--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker',
                  '-sALLOW_MEMORY_GROWTH=1','-sSTACK_SIZE=1048576','-sINITIAL_MEMORY=536870912','-sMAXIMUM_MEMORY=1073741824',
                  '-sFILESYSTEM=1','-lidbfs.js','-sEXIT_RUNTIME=0','-sINVOKE_RUN=0','-sASSERTIONS=1',
                  '-sASYNCIFY=1','-sASYNCIFY_STACK_SIZE=65536',
                  '-sINCOMING_MODULE_JS_API=canvas,instantiateWasm,noInitialRun,locateFile,print,printErr,onRuntimeInitialized,onAbort,wasmBinary,wasmMemory,preRun,postRun',
                  '-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,HEAPU8,HEAP32,HEAPU32,ccall','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2',
                  '-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_FUNCTIONS='+','.join('_'+name for name in exports),
                  '--js-library',str(source/'portable/sdl/Th14WebGpuLibrary.js')]
    (out/'progress.json').write_text(json.dumps(dict(phase='link',compiled=len(compiled),total=len(units)))+'\n')
    storage.check_budget(out)
    result = subprocess.run([sys.executable,str(emcc),*flags,*link_flags,*[str(compiled[unit])for unit in units],'-o',str(out/'th14-sdl.mjs')],cwd=source/'th12_web',env=env,capture_output=True)
    (out/'link.log').write_bytes(result.stdout+result.stderr); assert result.returncode == 0, (out/'link.log').read_text()[-8000:]
    storage.check_budget(out)
    wasm = (out/'th14-sdl.wasm').read_bytes()
    report = dict(schema='th14/browser-webgpu-candidate-build/1',compiled=True,title=14,basePublishedCommit=args.base_commit,
        sourceBindings=inventory,overlays=OVERLAYS,sourceFiles=len(inventory),sourceUnits=len(units),compiledUnits=len(units)-len(reused),reusedObjectCount=len(reused),reusedObjectHashes=reused,reuseBuildReportSha256=reuse_report_sha,exports=exports,
        flags=flags,linkFlags=link_flags,compilerVersion=(sdk/'upstream/emscripten/emscripten-version.txt').read_text().strip(),
        wasmBytes=len(wasm),wasmSha256=SHA(wasm),loaderSha256=SHA((out/'th14-sdl.mjs').read_bytes()),
        objectHashes={unit.relative_to(source).as_posix():SHA(compiled[unit].read_bytes())for unit in units},
        toolSha256=SHA(tool_raw),storageToolSha256=SHA(storage_raw),rootUnrelatedResourceCryptExcluded=True,retailAssetsIncluded=False,
        actualSdlPort=True,asyncify=True,frameAndWorkerCallbacksSerialized=True,browserRun=False,browserAcceptance=False,
        completeGame=False,nativeEquivalent=False,scope='Fresh compilation of the published independent C++ TH14 engine, real SDL3 port and explicit WebGPU overlays. Browser-targeted candidate only; compilation does not prove startup, presentation, browser scheduling, persistence, physical devices or whole-game fidelity.')
    (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'progress.json').write_text(json.dumps(dict(phase='compiled',compiled=len(compiled),total=len(units)))+'\n')
    print(json.dumps(dict(compiled=True,units=len(units),wasmBytes=len(wasm),wasmSha256=report['wasmSha256'])),flush=True)


if __name__ == '__main__': main()
