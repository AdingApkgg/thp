"""Extend three frozen independent D3D9 HAL UV captures with full pixel bytes.

Uses only the existing own compiled PS2 probe and original captured inputs.
No retail game process, visible window, UI automation, or reconstructed oracle.
"""
import hashlib,json,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/th14/stage-current-residual-native-uv-fe406-oct14'
BASE=ROOT/'artifacts/th14/stage-gpu-stream-replay'
sha=lambda b:hashlib.sha256(b).hexdigest()
bindings={}
def bind(p):
    b=Path(p).read_bytes();bindings[str(Path(p))]={'bytes':len(b),'sha256':sha(b)};return b
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'capture-complete.json').exists(),'Completed capture is immutable'
assert not list(OUT.glob('frame-*.rgba32f')),'Partial full-buffer capture must be preserved; use a separately labeled attempt'
parent=ROOT/'tools/th14-stage-sampler-uv-hal.py';original=bind(parent)
assert sha(original)=='b3e677676867a3585185f413fe8a92b5354eaa4b182c52adcbd93204c814e207'
generation=json.loads(bind(BASE/'sampler-uv/generation.json'));old=json.loads(bind(BASE/'sampler-uv/native.json'))
assert generation['halSourceSha256']==sha(original) and generation['nativeSha256']==sha(bind(BASE/'sampler-uv/native.json'))
inputs=json.loads(bind(BASE/'sampler-uv/inputs.json'));prepared=json.loads(bind(BASE/'prepared.json'))
assert sha(bind(BASE/'prepared.json'))==old['preparedSha256'];assert sha(bind(BASE/'sampler-uv/inputs.json'))==generation['inputsSha256']
selected=[c for c in inputs['cases'] if (c['stage'],c['frame'],c['draw']) in [(2,599,47),(2,599,20),(4,599,9)]]
assert len(selected)==3
for c in selected:
    nr=next(r for r in old['frames'] if (r['stage'],r['frame'],r['originalDrawIndex'])==(c['stage'],c['frame'],c['draw']))
    assert c['points']==[[s['x'],s['y']] for s in nr['samples']]
for t in prepared['textures']:assert sha(bind(BASE/t['file']))==t['sha256']
probe=bind(BASE/'sampler-uv/probe.pso');assert sha(probe)==generation['shaderSha256']=='0896967f3ea1cb0655e9686fb635305f87f0eeeddc047f25d3b3b0b4b1aa441e'
assert sha(bind(BASE/'sampler-uv/probe.asm'))==generation['assemblySha256']
assert sha(bind(ROOT/'tools/th14-gpu-raster-native.py'))==old['typesSha256']
assert sha(bind('C:/Windows/System32/d3d9.dll'))==old['d3d9Sha256']
bind('C:/Windows/System32/user32.dll')
assert sha(bind('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h'))==old['sdkSha256']
(OUT/'inputs.json').write_text(json.dumps({'cases':selected},indent=2)+'\n',encoding='utf8')
source=original.decode('utf8')
def replace(a,b):
    global source
    assert source.count(a)==1,(a,source.count(a));source=source.replace(a,b)
replace("ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=INPUT/'sampler-uv'", "ROOT=Path("+repr(str(ROOT))+ ");INPUT=ROOT/'artifacts/th14/stage-gpu-stream-replay';OUT=ROOT/'artifacts/th14/stage-current-residual-native-uv-fe406-oct14'")
replace("user=C.WinDLL('user32')", "user=C.WinDLL('C:/Windows/System32/user32.dll')")
replace("dll=C.WinDLL('d3d9')", "dll=C.WinDLL('C:/Windows/System32/d3d9.dll')")
start=source.index("        compiler=C.WinDLL('d3dcompiler_47')")
end=source.index('        lock=t.Lock()',start)
source=source[:start]+"""        code=(INPUT/'sampler-uv/probe.pso').read_bytes()
        assert sha(code)=='0896967f3ea1cb0655e9686fb635305f87f0eeeddc047f25d3b3b0b4b1aa441e'
        (OUT/'probe.pso').write_bytes(code);buffer=C.create_string_buffer(code)
        call(device,'IDirect3DDevice9','CreatePixelShader',[P,C.POINTER(P)],[buffer,C.byref(pixel_shader)])
"""+source[end:]
replace("            pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))", "            (OUT/('frame-%03d.rgba32f'%(len(frames)-1))).write_bytes(raw)\n            pixels.extend(b''.join(struct.pack('<4I',*p['words']) for p in samples))")
replace("        d3d=P(dll.Direct3DCreate9(32));assert d3d", """        kernel=C.WinDLL('C:/Windows/System32/kernel32.dll')
        kernel.GetModuleFileNameW.argtypes=[P,C.c_wchar_p,U];kernel.GetModuleFileNameW.restype=U
        loaded=C.create_unicode_buffer(32768);assert kernel.GetModuleFileNameW(P(dll._handle),loaded,32768)
        assert Path(loaded.value).resolve()==Path('C:/Windows/System32/d3d9.dll').resolve()
        (OUT/'loaded-d3d9.json').write_text(json.dumps(dict(path=loaded.value,sha256=sha(Path(loaded.value).read_bytes()),hiddenWindowStyle=0)),encoding='utf8')
        d3d=P(dll.Direct3DCreate9(32));assert d3d""")
generated=OUT/'capture-hal.py';generated.write_text(source,encoding='utf8')
receipt=dict(diagnosticOnly=True,completeGame=False,nativeEquivalent=False,originalHelperPath=str(parent),originalHelperSha256=sha(original),adapterToolSha256=sha(Path(__file__).read_bytes()),adaptedHelperSha256=sha(generated.read_bytes()),compiledProbeSha256=sha(probe),selectedCases=selected,bindings=bindings,scope='Restricted extension of existing own hidden original-input D3D9 HAL fixture. Reuses existing PS2 UV bytecode and system D3D9. Only output/full-buffer archival and explicit system DLL paths differ. No retail game process or visible UI.')
(OUT/'preflight.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
if '--prepare-only' in sys.argv:
    print(json.dumps({'prepared':True,'cases':len(selected),'adaptedHelperSha256':receipt['adaptedHelperSha256']}));sys.exit(0)
runpy.run_path(str(generated),run_name='__main__')
observed=json.loads((OUT/'native.json').read_bytes());assert len(observed['frames'])==3
for i,nr in enumerate(observed['frames']):
    expected=next(r for r in old['frames'] if (r['stage'],r['frame'],r['originalDrawIndex'])==(nr['stage'],nr['frame'],nr['originalDrawIndex']))
    raw=(OUT/f'frame-{i:03d}.rgba32f').read_bytes();assert len(raw)==640*480*16
    assert sha(raw)==nr['fullFloatFrameSha256']==expected['fullFloatFrameSha256']
    assert nr['samples']==expected['samples']
completion=dict(originalNativeUVReportSha256=sha(bind(BASE/'sampler-uv/native.json')),newNativeReportSha256=sha((OUT/'native.json').read_bytes()),preflightSha256=sha((OUT/'preflight.json').read_bytes()),fullBufferBytes=3*640*480*16,originalFullHashesAndSamplesPreserved=True,toolSha256=sha(Path(__file__).read_bytes()))
(OUT/'capture-complete.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf8')
print(json.dumps(completion))
