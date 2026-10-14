"""Own isolated HAL float32-composed VS2 control for three residual strips.

Uses frozen original matrices/vertices and existing compiled own PS2/VS2 probes.
No fitted coordinates, explicit snapping, retail child process or visible UI.
"""
import hashlib,json,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay'
FFP=ROOT/'artifacts/th14/stage-current-residual-native-uv-fe406-oct14'
OUT=ROOT/'artifacts/th14/stage-current-residual-native-composed-uv-fe406-oct14'
sha=lambda b:hashlib.sha256(b).hexdigest();bindings={}
def bind(p):
    p=Path(p);b=p.read_bytes();bindings[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'capture-complete.json').exists(),'Completed capture is immutable'
assert not list(OUT.glob('frame-*.rgba32f')),'Preserve partial capture and use another label'
helper=ROOT/'tools/th14-stage-sampler-matrix-float-hal.py';original=bind(helper)
assert sha(original)=='c687b408fa4ba02f98da1b4ea3524ea5044045a0d54b2660e1a3b8b0bc7a690e'
generation=json.loads(bind(BASE/'sampler-matrix-float/generation.json'))
old=json.loads(bind(BASE/'sampler-matrix-float/native.json'))
assert generation['halSourceSha256']==sha(original)==old['toolSha256']
assert generation['nativeSha256']==sha(bind(BASE/'sampler-matrix-float/native.json'))
inputs=json.loads(bind(FFP/'inputs.json'));ffp=json.loads(bind(FFP/'native.json'))
prepared=json.loads(bind(BASE/'prepared.json'));assert sha(bind(BASE/'prepared.json'))==old['preparedSha256']==ffp['preparedSha256']
for texture in prepared['textures']:assert sha(bind(BASE/texture['file']))==texture['sha256']
ps=bind(BASE/'sampler-matrix-float/probe.pso');vs=bind(BASE/'sampler-matrix-float/probe.vso')
assert ps==bind(BASE/'sampler-uv/probe.pso')
assert bind(BASE/'sampler-matrix-float/probe.asm')==bind(BASE/'sampler-uv/probe.asm')
bind(BASE/'sampler-matrix-float/probe.vs.asm')
assert sha(bind(ROOT/'tools/th14-gpu-raster-native.py'))==old['typesSha256']
assert sha(bind('C:/Windows/System32/d3d9.dll'))==old['d3d9Sha256']
bind('C:/Windows/System32/user32.dll')
assert sha(bind('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h'))==old['sdkSha256']
(OUT/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8')
source=original.decode('utf8')
def replace(a,b):
    global source
    assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
replace("ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'sampler-matrix-float'","ROOT=Path("+repr(str(ROOT))+");INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=ROOT/'artifacts/th14/stage-current-residual-native-composed-uv-fe406-oct14'")
replace("user=C.WinDLL('user32')","user=C.WinDLL('C:/Windows/System32/user32.dll')")
replace("dll=C.WinDLL('d3d9')","dll=C.WinDLL('C:/Windows/System32/d3d9.dll')")
start=source.index("        compiler=C.WinDLL('d3dcompiler_47')");end=source.index('        lock=t.Lock()',start)
source=source[:start]+f"""        code=(INPUT/'sampler-matrix-float/probe.pso').read_bytes();assert sha(code)=={sha(ps)!r}
        (OUT/'probe.pso').write_bytes(code);buffer=C.create_string_buffer(code)
        call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[buffer,C.byref(pixel_shader)])
        vertex_source=(INPUT/'sampler-matrix-float/probe.vs.asm').read_bytes()
        (OUT/'probe.vs.asm').write_bytes(vertex_source)
        code=(INPUT/'sampler-matrix-float/probe.vso').read_bytes();assert sha(code)=={sha(vs)!r}
        (OUT/'probe.vso').write_bytes(code);buffer=C.create_string_buffer(code)
        call(device,'IDirect3DDevice9','CreateVertexShader',[P,C.POINTER(P)],[buffer,C.byref(vertex_shader)])
"""+source[end:]
replace("            pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))","            (OUT/('frame-%03d.rgba32f'%(len(frames)-1))).write_bytes(raw)\n            pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))")
replace("fvf=frame['case']['fvf'],samples=samples,fullFloatFrameSha256=sha(raw)","fvf=frame['case']['fvf'],samples=samples,fullFloatFrameSha256=sha(raw),computedClipMatrixWords=list(struct.unpack('<16I',struct.pack('<16f',*combined)))")
replace("        d3d=P(dll.Direct3DCreate9(32));assert d3d","""        kernel=C.WinDLL('C:/Windows/System32/kernel32.dll')
        kernel.GetModuleFileNameW.argtypes=[P,C.c_wchar_p,U];kernel.GetModuleFileNameW.restype=U
        loaded=C.create_unicode_buffer(32768);assert kernel.GetModuleFileNameW(P(dll._handle),loaded,32768)
        assert Path(loaded.value).resolve()==Path('C:/Windows/System32/d3d9.dll').resolve()
        (OUT/'loaded-d3d9.json').write_text(json.dumps(dict(path=loaded.value,sha256=sha(Path(loaded.value).read_bytes()),hiddenWindowStyle=0)),encoding='utf8')
        d3d=P(dll.Direct3DCreate9(32));assert d3d""")
generated=OUT/'capture-hal.py';generated.write_text(source,encoding='utf8')
receipt=dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,originalHelperPath=str(helper),originalHelperSha256=sha(original),adapterToolSha256=sha(Path(__file__).read_bytes()),adaptedHelperSha256=sha(generated.read_bytes()),compiledPS2Sha256=sha(ps),compiledVS2Sha256=sha(vs),selectedCases=inputs['cases'],bindings=bindings,scope='Own hidden D3D9 HAL control. Existing sequential binary32 P*(V*W) helper, original world/view/projection/texture matrices and submitted vertices, existing compiled own m4x4 VS2 and PS2 UV probes. No fitted/Native clip injection or viewport snapping; no retail game process or visible UI. New archival and explicit system DLL paths only.')
(OUT/'preflight.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
if '--prepare-only' in sys.argv:
    print(json.dumps({'prepared':True,'adaptedHelperSha256':receipt['adaptedHelperSha256']}));sys.exit(0)
runpy.run_path(str(generated),run_name='__main__')
observed=json.loads((OUT/'native.json').read_bytes());assert len(observed['frames'])==3
matches=[]
for i,nr in enumerate(observed['frames']):
    expected=ffp['frames'][i];assert (nr['stage'],nr['frame'],nr['originalDrawIndex'])==(expected['stage'],expected['frame'],expected['originalDrawIndex'])
    raw=(OUT/f'frame-{i:03d}.rgba32f').read_bytes();assert len(raw)==640*480*16 and sha(raw)==nr['fullFloatFrameSha256']
    matches.append(sha(raw)==expected['fullFloatFrameSha256'] and nr['samples']==expected['samples'])
completion=dict(originalFFPReportSha256=sha(bind(FFP/'native.json')),composedReportSha256=sha((OUT/'native.json').read_bytes()),preflightSha256=sha((OUT/'preflight.json').read_bytes()),fullBufferBytes=3*640*480*16,allFFPFullHashesAndSamplesMatch=all(matches),caseMatches=matches,toolSha256=sha(Path(__file__).read_bytes()))
(OUT/'capture-complete.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf8');print(json.dumps(completion))
