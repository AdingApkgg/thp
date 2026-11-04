"""Prepare an output-only local startup diagnostic over immutable GLES routes."""
from pathlib import Path
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/browser-ordinary-gles-nov05'
P=R/'artifacts/th14/gles-clip-portable-nov04/launcher-gles-nov05/launcher-report.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
H.mkdir(exist_ok=True)
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,default=H/'startup-probe')
a=p.parse_args();out=a.output.resolve()
assert out.is_relative_to(H) and out!=H
out.mkdir(exist_ok=False)
proof=json.loads(P.read_bytes())
key='runtime/th14/shell.mjs'
source=R/proof['files'][key]['path'];raw=source.read_bytes()
assert sha(raw)==proof['files'][key]['sha256']
s=raw.decode()
probe='''
// Local, output-only startup observation. No clock, input, RNG or state writes.
let probeStage='module-loading',probeRaf=0,probeFrames=0,probeTicks=0;
const probeNode=document.createElement('output');probeNode.id='th14-startup-probe';
probeNode.style.cssText='position:fixed;left:8px;top:8px;max-width:90vw;z-index:99999;color:#fff;background:#17212de8;font:14px monospace;white-space:pre-wrap;pointer-events:none';
document.body.appendChild(probeNode);
const probeText=p=>{if(!p||!Module?.HEAPU8)return '';const end=Module.HEAPU8.indexOf(0,p);return new TextDecoder().decode(Module.HEAPU8.subarray(p,Math.min(end<0?p+256:end,p+256)));};
function probeRefresh(){try{probeNode.textContent=JSON.stringify({stage:probeStage,jsAnimationFrames:probeRaf,frameReceipts:probeFrames,gameTicks:probeTicks,phase:core?.th11_phase?.(),gameFrame:core?.th11_frame?.(),lastResource:probeText(core?.th11_last_resource?.()),error:core?coreError():'',audioContext:Module?.SDL3?.audioContext?.state,loop:Module?.th14LocalLoopProbe,frameBridgeCalls:Module?.th14LocalFrameProbe,hidden:document.hidden,canvas:[canvas.width,canvas.height]},null,2);}catch(e){probeNode.textContent=String(e);}}
function probeAnimation(){++probeRaf;requestAnimationFrame(probeAnimation);}requestAnimationFrame(probeAnimation);
setInterval(probeRefresh,1000);
'''
needle='async function launch(){'
assert s.count(needle)==1;s=s.replace(needle,probe+'\n'+needle)
changes=[
 ('if(!await callCore(\'th11_initialize\'))throw Error(coreError());',"probeStage='initializing';probeRefresh();if(!await callCore('th11_initialize'))throw Error(coreError());probeStage='initialized';probeRefresh();"),
 ('core.th11_loop_start();',"probeStage='loop-start';core.th11_loop_start();probeStage='loop-start-returned';probeRefresh();"),
 ('Module.onGameFrame=(ok,ms,count)=>{',"Module.onGameFrame=(ok,ms,count)=>{++probeFrames;probeTicks+=count;probeStage='frame-received';"),
 ("emit('ready');","probeStage='ready';probeRefresh();emit('ready');")]
for a,b in changes:
 assert s.count(a)==1,a;s=s.replace(a,b)
dest=out/'shell.mjs';dest.write_text(s,encoding='utf8',newline='\n');b=dest.read_bytes()
proof['roots'].append(out.relative_to(R).as_posix())
proof['files'][key]=dict(path=dest.relative_to(R).as_posix(),bytes=len(b),sha256=sha(b))
loader_key='runtime/th14/th14-sdl.mjs'
loader_path=R/proof['files'][loader_key]['path'];loader_raw=loader_path.read_bytes()
assert sha(loader_raw)==proof['files'][loader_key]['sha256']
loader=loader_raw.decode()
old_loop='var _emscripten_request_animation_frame_loop=(cb,userData)=>{function tick(timeStamp){if(((a1,a2)=>dynCall_idi(cb,a1,a2))(timeStamp,userData)){requestAnimationFrame(tick)}}return requestAnimationFrame(tick)};'
new_loop='''var _emscripten_request_animation_frame_loop=(cb,userData)=>{const probe=Module["th14LocalLoopProbe"]??= {registrations:0,callbacks:0,lastReturn:null,error:null};++probe.registrations;function tick(timeStamp){++probe.callbacks;let result;try{result=((a1,a2)=>dynCall_idi(cb,a1,a2))(timeStamp,userData);}catch(e){probe.error=String(e);throw e;}probe.lastReturn=typeof result==='number'||typeof result==='boolean'?result:typeof result;if(result){requestAnimationFrame(tick)}}return requestAnimationFrame(tick)};'''
old_bridge='function th11_browser_frame(ok,milliseconds,ticks){Module["onGameFrame"]?.(ok,milliseconds,ticks)}'
new_bridge='function th11_browser_frame(ok,milliseconds,ticks){Module["th14LocalFrameProbe"]=(Module["th14LocalFrameProbe"]??0)+1;Module["onGameFrame"]?.(ok,milliseconds,ticks)}'
assert loader.count(old_loop)==1 and loader.count(old_bridge)==1
loader=loader.replace(old_loop,new_loop).replace(old_bridge,new_bridge)
loader_dest=out/'th14-sdl.mjs';loader_dest.write_text(loader,encoding='utf8',newline='\n');loader_bytes=loader_dest.read_bytes()
proof['files'][loader_key]=dict(path=loader_dest.relative_to(R).as_posix(),bytes=len(loader_bytes),sha256=sha(loader_bytes))
proof.update(localStartupProbe=True,parentLauncherReport=P.relative_to(R).as_posix(),parentLauncherReportSha256=sha(P.read_bytes()),productionGameplayChanged=False)
proof['generatedLoaderProbe']={'parentPath':loader_path.relative_to(R).as_posix(),'parentSha256':sha(loader_raw),'onlyRegistrationCallbackResultAndBridgeCounts':True,'callbackArgumentsAndReturnUnchanged':True,'exceptionsRethrown':True}
(out/'launcher-report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(report=(out/'launcher-report.json').relative_to(R).as_posix(),wasmUnchanged=True,ordinaryGlesFrameLoopUnchanged=True,onlyShellAndLoaderOutputAdded=True)))
