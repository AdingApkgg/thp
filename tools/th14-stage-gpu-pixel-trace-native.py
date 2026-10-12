"""Trace selected mismatching pixels after each direct draw, on our own HAL."""
import hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'
OUT=INPUT/'pixel-trace';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
native_bytes=(INPUT/'native.json').read_bytes();native=json.loads(native_bytes)
reference=(INPUT/'native.bgra').read_bytes();portable=(INPUT/'webgl.bgra').read_bytes()
assert sha(reference)==native['pixelsSha256']
baseline=json.loads((INPUT/'browser-result.json').read_bytes());assert sha(portable)==baseline['portablePixelsSha256']
selected=[]
for row in native['frames']:
    if (row['stage'],row['frame']) not in ((3,599),(3,1199),(5,599)):continue
    offset=row['offset'];candidates=[]
    for p in range(640*480):
        delta=max(abs(reference[offset+p*4+k]-portable[offset+p*4+k]) for k in range(4))
        if delta>8:candidates.append((delta,p%640,p//640))
    points=[[x,y] for _,x,y in sorted(candidates,reverse=True)[:16]];assert points
    selected.append(dict(stage=row['stage'],frame=row['frame'],points=points,expectedFinalSha256=row['sha256'],portableFinalSha256=next(r['portableSha256'] for r in baseline['reports'] if r['stage']==row['stage'] and r['frame']==row['frame'])))
input_report=dict(frames=selected,nativeProofSha256=sha(native_bytes),nativePixelsSha256=sha(reference),portablePixelsSha256=sha(portable),toolSha256=sha(Path(__file__).read_bytes()))
(OUT/'inputs.json').write_text(json.dumps(input_report,indent=2)+'\n',encoding='utf8')
base=ROOT/'tools/th14-stage-gpu-stream-hal.py';text=base.read_text(encoding='utf8')
text=text.replace("OUT=ROOT/'artifacts/th14/stage-gpu-stream-replay'","INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'pixel-trace'")
text=text.replace("(OUT/'prepared.json').read_bytes()","(INPUT/'prepared.json').read_bytes()").replace("(OUT/n['file']).read_bytes()","(INPUT/n['file']).read_bytes()")
anchor="        def execute(c):\n";assert text.count(anchor)==1
text=text.replace(anchor,'''        trace_inputs=json.loads((OUT/'inputs.json').read_bytes());trace_frames=[];active_trace=None
        def sample_pixels():
            call(device,'IDirect3DDevice9','EndScene',[],[])
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,readback]);call(readback,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            colors=[list(C.string_at(lock.bits+y*lock.pitch+x*4,4)) for x,y in active_trace['points']]
            call(readback,'IDirect3DSurface9','UnlockRect',[],[]);call(device,'IDirect3DDevice9','BeginScene',[],[])
            return colors
        def execute(c):
''')
anchor="        for frame in prepared['frames']:\n";assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''            selected=next((r for r in trace_inputs['frames'] if (r['stage'],r['frame'])==(frame['stage'],frame['frame'])),None)
            if selected is None:continue
            active_trace=dict(**selected,draws=[])
''')
anchor="            for c in frame['commands']:execute(c)\n";assert text.count(anchor)==1
text=text.replace(anchor,'''            active_trace['beforeDraws']=sample_pixels()
            for command_index,c in enumerate(frame['commands']):
                execute(c)
                if c['kind']=='draw':active_trace['draws'].append(dict(commandIndex=command_index,drawIndex=len(active_trace['draws']),colors=sample_pixels()))
''')
anchor="            pixels.extend(raw);print(";assert text.count(anchor)==1
text=text.replace(anchor,"            assert sha(raw)==active_trace['expectedFinalSha256'],(frame['stage'],frame['frame'],'readback barriers changed final output')\n            active_trace['finalSha256']=sha(raw);trace_frames.append(active_trace)\n"+anchor)
anchor="        (OUT/'native.bgra').write_bytes(pixels)\n";assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''        trace_report=dict(traced=True,completeGame=False,nativeEquivalent=False,frames=trace_frames,inputsSha256=sha((OUT/'inputs.json').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),scope='Selected mismatching pixel coordinates after each direct draw; independent HAL EndScene/readback/BeginScene barriers are inserted, final full frames must still exactly match the unmodified replay. No retail framebuffer or native depth-value readback.')
        (OUT/'trace.json').write_text(json.dumps(trace_report,separators=(',',':'))+'\\n',encoding='utf8')
''')
generated=ROOT/'tools/th14-stage-gpu-pixel-trace-hal.py';generated.write_text(text,encoding='utf8')
runpy.run_path(str(generated),run_name='__main__')
