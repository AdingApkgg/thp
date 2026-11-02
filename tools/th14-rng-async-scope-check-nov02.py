"""Check actual current RNG scopes across Emscripten Asyncify suspension."""
import argparse,hashlib,importlib.util,json,os,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=pathlib.Path,required=True)
 p.add_argument('--summary',type=pathlib.Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
 game=R/'runtimes/th12/th12_web/cpp/game';platform=R/'runtimes/th12/portable/sdl';sdk=R/'runtimes/th12/tools/emsdk'
 fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-rng-async-scope-fixture-nov02.cpp'
 sources=[pathlib.Path(__file__),R/'tools/th14-rng-async-scope-check-nov02.mjs',fixture,
  *[game/x for x in ['Rng.hpp','Types.hpp','PortTitle.hpp']],
  *[platform/x for x in ['Th14WebGpuCallbacks.hpp','Th14WebGpuLibrary.js','Th14WebGpuRuntime.mjs','Th14WebGpuCore.mjs']]]
 post=out/'post.js';post.write_text('Module["rngTestMemory"]=()=>wasmMemory;Module["rngTestUpdateViews"]=()=>updateMemoryViews();\n')
 exports=['rng_async_status','rng_reference','rng_schedule','th11_key','th14_webgpu_invoke','th14_webgpu_frame']
 flags=['-O2','-g0','-std=c++17','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-DTH14_WEBGPU_BACKEND=1','--no-entry',
  '-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=node','-sALLOW_MEMORY_GROWTH=1',
  '-sINITIAL_MEMORY=16777216','-sMAXIMUM_MEMORY=134217728','-sSTACK_SIZE=1048576',
  '-sASYNCIFY=1','-sASYNCIFY_STACK_SIZE=65536','-sASSERTIONS=1',
  '-sINCOMING_MODULE_JS_API=wasmBinary,noInitialRun,print,printErr,locateFile,onRuntimeInitialized,onAbort',
  '-sEXPORTED_RUNTIME_METHODS=ccall,HEAPU8','-sEXPORTED_FUNCTIONS='+','.join('_'+x for x in exports),
  '--js-library',str(platform/'Th14WebGpuLibrary.js'),'--post-js',str(post),'-I'+str(game),'-I'+str(platform)]
 argv=[sys.executable,str(sdk/'upstream/emscripten/emcc.py'),*flags,str(fixture),'-o',str(out/'component.mjs')]
 env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,
  'PATH':str(pathlib.Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH',''),
  'EMCC_CORES':'2','TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
 result=subprocess.run(argv,cwd=R,env=env,capture_output=True,timeout=180);(out/'compile.log').write_bytes(result.stdout+result.stderr)
 assert result.returncode==0,(out/'compile.log').read_text()[-4000:]
 report=dict(compiled=True,argv=argv,sourceBindings={p.relative_to(R).as_posix():SHA(p.read_bytes())for p in sources},
  postJsSha256=SHA(post.read_bytes()),compilerVersion=(sdk/'upstream/emscripten/emscripten-version.txt').read_text().strip(),
  wasmSha256=SHA((out/'component.wasm').read_bytes()),loaderSha256=SHA((out/'component.mjs').read_bytes()),
  browserAcceptance=False,completeGame=False,nativeEquivalent=False)
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n')
 checked=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(R/'tools/th14-rng-async-scope-check-nov02.mjs'),str(out)],cwd=R,capture_output=True,timeout=90)
 (out/'comparison.log').write_bytes(checked.stdout+checked.stderr);assert checked.returncode==0,(out/'comparison.log').read_text()[-4000:]
 storage.check_budget(out)
 result=json.loads((out/'verified.json').read_bytes())
 assert result['passed']and result['cases']==80 and result['callbacks']==320 and result['negativeControl']['rawUnserializedKeyRejected']
 if a.summary:
  summary=a.summary.resolve();assert summary.is_relative_to(R/'docs/porting')and summary.suffix=='.json'
  receipt={k:v for k,v in result.items()if k not in ['rows','negativeControl']}
  receipt.update(sourceBindings=report['sourceBindings'],compilerVersion=report['compilerVersion'],
   referenceCoreCommit='4acbbc398fe3648ca8362e4fe803f56ee87818b7',
   exactCurrentRngHeaderSha256=SHA((game/'Rng.hpp').read_bytes()),
   localReport=out.relative_to(R).as_posix()+'/verified.json',localReportSha256=SHA((out/'verified.json').read_bytes()),
   rawUnserializedKeyNegativeControlRejected=True,negativeControlDetectedErrors=1,
   productionGameSourcesChanged=False)
  summary.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 print(checked.stdout.decode(),end='')

if __name__=='__main__':main()
