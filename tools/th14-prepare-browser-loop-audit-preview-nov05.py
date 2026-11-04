"""Overlay a bounded-print Application build on the existing private routes."""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/browser-ordinary-gles-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main(build_home,out):
    p=H/'startup-probe-v2/launcher-report.json';proof=json.loads(p.read_bytes());build=json.loads((build_home/'build.json').read_bytes())
    assert build['localLoopAuditOnly']and build['compiledUnits']==1 and build['reusedObjectCount']==145
    assert not out.exists();out.mkdir(parents=True)
    def source(key):
        row=proof['files'][key];b=(R/row['path']).read_bytes();assert SHA(b)==row['sha256'];return b
    def route(key,path):
        b=path.read_bytes();proof['files'][key]=dict(path=path.relative_to(R).as_posix(),bytes=len(b),sha256=SHA(b))
    shell=source('runtime/th14/shell.mjs').decode()
    def replace(a,b):
        nonlocal shell
        assert shell.count(a)==1,(a[:90],shell.count(a));shell=shell.replace(a,b)
    replace('0a9750bfe24129ec6005b197fe599b49c2adb62652e175c85e8c0b479f616794',build['wasmSha256'])
    replace("let probeStage='module-loading',probeRaf=0,probeFrames=0,probeTicks=0;",
        "let probeStage='module-loading',probeRaf=0,probeFrames=0,probeTicks=0;let probeNativeLines=[],probeLastFrame=null;\nfunction probePrint(line){line=String(line);if(line.startsWith('[loop14]')||line.startsWith('[loading14]')){probeNativeLines.push(line);if(probeNativeLines.length>20)probeNativeLines.shift();}console.log(line);}")
    replace('loop:Module?.th14LocalLoopProbe,frameBridgeCalls:Module?.th14LocalFrameProbe,',
        'loop:Module?.th14LocalLoopProbe,frameBridgeCalls:Module?.th14LocalFrameProbe,lastNativeFrame:probeLastFrame,nativeOutput:probeNativeLines,')
    replace('print:console.log,printErr:console.error,','print:probePrint,printErr:line=>{probeNativeLines.push(String(line));console.error(line);},')
    replace("Module.onGameFrame=(ok,ms,count)=>{++probeFrames;probeTicks+=count;probeStage='frame-received';",
        "Module.onGameFrame=(ok,ms,count)=>{probeLastFrame={ok,ms,count};++probeFrames;probeTicks+=count;probeStage='frame-received';")
    shell_path=out/'shell.mjs';shell_path.write_text(shell,encoding='utf8',newline='\n');route('runtime/th14/shell.mjs',shell_path)
    loader_path=build_home/'th14-sdl.mjs';b=loader_path.read_bytes();assert SHA(b)==build['loaderSha256'];loader=b.decode()
    # Copy the already syntax-checked output-only JS probes onto the new loader.
    previous=source('runtime/th14/th14-sdl.mjs').decode()
    marker='var _emscripten_request_animation_frame_loop='
    start=previous.index(marker);end=previous.index(';var doRequestFullscreen=',start)
    old_start=loader.index(marker);old_end=loader.index(';var doRequestFullscreen=',old_start)
    loader=loader[:old_start]+previous[start:end]+loader[old_end:]
    old='function th11_browser_frame(ok,milliseconds,ticks){Module["onGameFrame"]?.(ok,milliseconds,ticks)}'
    new='function th11_browser_frame(ok,milliseconds,ticks){Module["th14LocalFrameProbe"]=(Module["th14LocalFrameProbe"]??0)+1;Module["onGameFrame"]?.(ok,milliseconds,ticks)}'
    assert loader.count(old)==1;loader=loader.replace(old,new)
    dest=out/'th14-sdl.mjs';dest.write_text(loader,encoding='utf8',newline='\n');route('runtime/th14/th14-sdl.mjs',dest)
    wasm=build_home/'th14-sdl.wasm';assert SHA(wasm.read_bytes())==build['wasmSha256'];route('runtime/th14/th14-sdl.wasm',wasm)
    proof['roots']+=[out.relative_to(R).as_posix(),build_home.relative_to(R).as_posix()]
    proof.update(wasmSha256=build['wasmSha256'],localLoopAuditOnly=True,ordinaryProductionWasmUnchanged=False,
        parentLauncher=p.relative_to(R).as_posix(),parentLauncherSha256=SHA(p.read_bytes()),
        diagnosticBuildReport=(build_home/'build.json').relative_to(R).as_posix(),diagnosticBuildReportSha256=SHA((build_home/'build.json').read_bytes()),
        productionSourceUnchanged=True,gameCoreObjectsReused=141,browserAcceptance=False)
    (out/'launcher-report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(prepared=True,report=(out/'launcher-report.json').relative_to(R).as_posix(),wasmSha256=build['wasmSha256'],gameAssetsCopied=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(H)and out.is_relative_to(H)and not out.exists();main(build,out)
