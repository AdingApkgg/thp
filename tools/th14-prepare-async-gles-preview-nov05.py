"""Local startup probe over the Asyncify-safe GLES candidate; no asset copies."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/browser-ordinary-gles-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main(home,out):
    parent=H/'startup-probe-v2/launcher-report.json';proof=json.loads(parent.read_bytes())
    build=json.loads((home/'build.json').read_bytes());assert build['frameAndWorkerCallbacksSerialized']and build['backend']=='gles'
    assert not out.exists();out.mkdir(parents=True)
    def route(key,path):
        b=path.read_bytes();proof['files'][key]=dict(path=path.relative_to(R).as_posix(),bytes=len(b),sha256=SHA(b))
    shell_row=proof['files']['runtime/th14/shell.mjs'];raw=(R/shell_row['path']).read_bytes();assert SHA(raw)==shell_row['sha256'];shell=raw.decode()
    def replace(a,b):
        nonlocal shell
        assert shell.count(a)==1,(a[:120],shell.count(a));shell=shell.replace(a,b)
    replace('0a9750bfe24129ec6005b197fe599b49c2adb62652e175c85e8c0b479f616794',build['wasmSha256'])
    # Apply the same queue integration as the checked-in shell, while retaining
    # only the existing output probe and TH14 packaging substitutions.
    shell=shell.replace('const runtime=Module.th14WebGpuRuntime;','const runtime=Module.th14AsyncRuntime??Module.th14WebGpuRuntime;')
    replace('if(Module.th14WebGpuRuntime){core=Module.th14WebGpuRuntime.bindCore(core);window.core=core;}',
        'const runtime=Module.th14AsyncRuntime??Module.th14WebGpuRuntime;\n if(runtime){core=runtime.bindCore(core);window.core=core;}')
    replace('Module.onWebGpuError=error;',"""Module.onWebGpuError=error;
 Module.onAsyncError=error;
 if(typeof Module._th14_async_frame==='function'){
  const {Th14AsyncRuntime}=await import('./Th14AsyncRuntime.mjs');
  Module.th14AsyncRuntime=new Th14AsyncRuntime(Module);
 }""")
    replace('loop:Module?.th14LocalLoopProbe,',"asyncCallbacks:Module?.th14AsyncRuntime?{pending:Module.th14AsyncRuntime.pendingCallbacks,completed:Module.th14AsyncRuntime.completedCallbacks,failure:String(Module.th14AsyncRuntime.failure??'')}:null,")
    dest=out/'shell.mjs';dest.write_text(shell,encoding='utf8',newline='\n');route('runtime/th14/shell.mjs',dest)
    for name,key in [('th14-sdl.mjs','loaderSha256'),('th14-sdl.wasm','wasmSha256')]:
        assert SHA((home/name).read_bytes())==build[key];route('runtime/th14/'+name,home/name)
    route('runtime/th14/Th14AsyncRuntime.mjs',home/'Th14AsyncRuntime.mjs')
    for name,row in build.get('independentRestoreModuleFiles',{}).items():
        assert SHA((home/name).read_bytes())==row['sha256'];route('runtime/th14/'+name,home/name)
    proof['roots']+=[out.relative_to(R).as_posix(),home.relative_to(R).as_posix()]
    proof.update(wasmSha256=build['wasmSha256'],parentLauncherSha256=SHA(parent.read_bytes()),
        diagnosticBuildReportSha256=SHA((home/'build.json').read_bytes()),callbackSchedulingChanged=True,
        sourceGameplayObjectsReused=141,browserAcceptance=False)
    (out/'launcher-report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(prepared=True,wasmSha256=build['wasmSha256'],routes=len(proof['files']),assetsCopied=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    home=a.build.resolve();out=a.output.resolve();assert home.is_relative_to(H)and out.is_relative_to(H);main(home,out)
