"""Independent full-byte copy comparison; keep every failure and before receipt."""
import hashlib,importlib.util,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';REPORT=ROOT/'docs/porting/th14-deferred-capture-pixels-observed-oct14.json';SHA=lambda b:hashlib.sha256(b).hexdigest()
def bind(p):return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=SHA(p.read_bytes()))
def model(source,c,center=False,truncate=False):
    bpp=c['bpp'];value=0x5a6b if bpp==2 else 0x917c3a5e;output=bytearray(value.to_bytes(bpp,'little')*(512*512));sl,st,sr,sb=c['sourceRect'];dl,dt,dr,db=c['destinationRect'];sw,sh=sr-sl,sb-st;dw,dh=dr-dl,db-dt
    for y in range(dh):
        yy=st+((2*y+1)*sh//(2*dh) if center else y*sh//dh)
        for x in range(dw):
            xx=sl+((2*x+1)*sw//(2*dw) if center else x*sw//dw);p=source[(yy*640+xx)*4:(yy*640+xx)*4+4]
            if bpp==2:
                b,g,r=p[:3]
                if truncate:v=(r>>3)<<11|(g>>2)<<5|(b>>3)
                else:v=((r*62+255)//510)<<11|((g*126+255)//510)<<5|((b*62+255)//510)
                p=struct.pack('<H',v)
            at=((dt+y)*512+dl+x)*bpp;output[at:at+bpp]=p
    return bytes(output)
def difference(a,b,bpp):
    assert len(a)==len(b);bad=0;pixels=0;maximum=0;first=[]
    for at in range(0,len(a),bpp):
        pixels+=a[at:at+bpp]!=b[at:at+bpp]
        for k in range(bpp):
            if a[at+k]!=b[at+k]:
                bad+=1;maximum=max(maximum,abs(a[at+k]-b[at+k]))
                if len(first)<20:first.append(dict(x=at//bpp%512,y=at//bpp//512,byte=k,portable=a[at+k],native=b[at+k]))
    return dict(differentBytes=bad,differentPixels=pixels,maxByteDelta=maximum,first=first)
def main():
    assert not REPORT.exists(),'Completed comparison immutable'
    native=json.loads((OUT/'native.json').read_bytes());build=json.loads((OUT/'webgl-build.json').read_bytes());web=json.loads((OUT/'webgl-capture/report.json').read_bytes());source=(OUT/'source.bgra').read_bytes()
    assert native['nativePixelControlsCaptured'] and native['sourceUploadReadbackByteExact'] and not native['nativeEquivalent']
    assert native['toolSha256']==SHA((ROOT/'tools/th14-deferred-capture-native-pixels.py').read_bytes())
    assert native['filter']==2 and native['colorKey']==0 and native['actualSourceDescription']==[21,1,1,0,0,0,640,480]
    for row in native['bindings']+native['sourceModuleBindings']:assert bind_external(row),row
    assert build['wasmSha256']==web['wasmSha256']==SHA((OUT/'capture.wasm').read_bytes()) and build['loaderSha256']==SHA((OUT/'capture.mjs').read_bytes())
    assert build['toolSha256']==SHA((ROOT/'tools/th14-deferred-capture-webgl-build.py').read_bytes())
    assert build['captureConsumerSha256']==web['captureConsumerSha256']==SHA((OUT/'private/cpp/sdl/ApplicationCaptureTh14.hpp').read_bytes())
    for row in build['bindings']:assert SHA((OUT/row['snapshot']).read_bytes())==row['sha256']
    assert SHA((OUT/'private/fixture.cpp').read_bytes())==build['fixtureSha256'] and web['sourceBindings']==build['bindings']
    assert len(native['cases'])==len(web['reports'])==web['frames']==8
    comparisons=[];native_models=[];exact=0;total=0;controls=web['controls']
    for n,w in zip(native['cases'],web['reports']):
        assert n['index']==w['index'] and n['request']==w['request'] and n['sourceRect']==w['sourceRect'] and n['destinationRect']==w['destinationRect']
        a=(OUT/'webgl-capture'/f"portable-{n['index']:03d}.pixels").read_bytes();b=(OUT/n['pixelFile']).read_bytes();assert len(a)==len(b)==n['bytes'] and SHA(a)==w['portableSha256'] and SHA(b)==n['pixelSha256']
        diff=difference(a,b,n['bpp'])
        for key,value in diff.items():assert w[key]==value,(n['name'],key)
        assert w['strictFullBufferEqual']==(a==b);assert w['words']==[-1,1,1,1,1,1,0,1,2,1],w['words']
        exact+=a==b;total+=len(a);comparisons.append(dict(name=n['name'],role=n['role'],sourceRect=n['sourceRect'],destinationRect=n['destinationRect'],format=n['destinationFormat'],bytes=len(a),nativeSha256=SHA(b),portableSha256=SHA(a),strictFullBufferEqual=a==b,**diff))
        em=model(source,n);cm=model(source,n,center=True);tm=model(source,n,truncate=True)
        native_models.append(dict(name=n['name'],fullBytes=len(b),edgeFloorNormalizedNearest565=difference(em,b,n['bpp'])['differentPixels'],rejectedCenterNormalizedNearest565=difference(cm,b,n['bpp'])['differentPixels'],rejectedEdgeBitshift565=difference(tm,b,n['bpp'])['differentPixels'],scope='Pure declared-input arithmetic diagnostic compared against archived actualHAL bytes; never substituted for Native capture. ARGB controls have no565 conversion.'))
        assert em==b
    assert web['exactFullBuffers']==exact and web['differentBytes']==sum(c['differentBytes'] for c in comparisons)
    assert [c['mode'] for c in controls]==[0,1,2]
    assert controls[0]['words']==controls[1]['words']==[-1,0,0,0,0,0,0,1,2,0]
    assert controls[2]['words']==[-1,1,1,1,1,0,0,1,2,0]
    hp=ROOT/'tools/th14-loading-lifecycle-evidence-check.py';spec=importlib.util.spec_from_file_location('capture_image',hp);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);image=h.Image();branches=[]
    for result in (0,1,0x8876086c,0x88760b59):
        u=image.machine();manager=0x2000000;u.mem_map(manager,0xc00000);esi=manager+0x28;h.word(u,esi-8,0);h.word(u,esi-4,1);h.word(u,manager+0xbc7b0c,0x660000);h.word(u,0x660124,0x670000);h.word(u,0x670018,0x680000);h.word(u,0x680000,0x690000);h.word(u,0x680014,0x690000);h.word(u,0x7ff000-0x28,0x680014)
        for register,value in [(UC_X86_REG_EAX,result),(UC_X86_REG_EBP,0x7ff000),(UC_X86_REG_ESP,0x7ff100),(UC_X86_REG_EDI,manager),(UC_X86_REG_ESI,esi)]:u.reg_write(register,value)
        def stop(guest,address,size,user):
            if address in (0x4691c5,0x4691ce):guest.emu_stop()
        hook=u.hook_add(UC_HOOK_CODE,stop);u.emu_start(0x4691a3,0x4691d1,count=100);u.hook_del(hook);at=u.reg_read(UC_X86_REG_EIP);assert at==(0x4691c5 if result==0 else 0x4691ce)
        u.emu_start(0x4691d1,0x4691d8,count=1);assert struct.unpack('<i',u.mem_read(esi-8,4))[0]==-1
        branches.append(dict(declaredD3DXHresult=hex(result),originalEntry='0x4691a3',stoppedBeforeHostCall=hex(at),dirtyCalledBeforeRelease=result==0,recordFileAfterOriginalRetirement=-1,hostCallsExecuted=0,originalImageBytesChanged=False))
    prior=ROOT/'docs/porting/th14-deferred-capture-private-queue-verified-oct14.json';q=json.loads(prior.read_bytes());assert q['retirementCasesMatched']==15 and q['privateQueueEvidenceVerified']
    report=dict(deferredPixelEvidenceVerified=True,productionChanged=False,completeGame=False,nativeEquivalent=False,cases=8,comparedRawBytes=total,exactFullBuffers=exact,copyPathStrictPixelsEqual=exact==8,differentBytes=sum(c['differentBytes'] for c in comparisons),comparisons=comparisons,nativeInputArithmeticControls=native_models,nullTargetAndControlledFalseCases=controls,originalDirtyAndRetirementControls=branches,rendererReportedErrors=[w['words'][6] for w in web['reports']],gpu=web['gpu'],captureConsumerSha256=build['captureConsumerSha256'],wasmSha256=build['wasmSha256'],bindings=[bind(p) for p in [OUT/'native.json',OUT/'native-output.bin',OUT/'native-source.bgra',OUT/'source.bgra',OUT/'inputs.json',OUT/'webgl-build.json',OUT/'webgl-capture/report.json',OUT/'capture.wasm',OUT/'capture.mjs',ROOT/'tools/th14-deferred-capture-native-pixels.py',ROOT/'tools/th14-deferred-capture-surface32-helper.cpp',ROOT/'tools/th14-deferred-capture-webgl-build.py',ROOT/'tools/th14-deferred-capture-webgl.html',ROOT/'tools/th14-deferred-capture-webgl-serve.mjs',hp,prior]],toolSha256=SHA(Path(__file__).read_bytes()),officialReferences=[dict(url='https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dxloadsurfacefromsurface',claim='Eight API arguments, rectangle semantics, color conversion, D3D_OK success and error return contract.'),dict(url='https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dx-filter',claim='POINT and optional dither are separate flags; no dither flag was captured.')],scope='Full raw original32 HAL D3DX versus actual frozen ApplicationCapture/production Renderer WebGL resample on the same explicit synthetic backbuffer, real text52 format/dimensions and8 declared rectangle/format controls. Nullresource/texture controls exercise helper retirement; false-return is a controlled adapter result, not an observed actualGLerror or NativeHRESULT mapping. Before helper currently calls changed/invalidate after false; original result-branch controls dirty only on0 and retire regardless. No full game/compositor/frame/audio equivalence.')
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({k:report[k] for k in ['deferredPixelEvidenceVerified','cases','comparedRawBytes','exactFullBuffers','differentBytes']}))
def bind_external(row):
    p=Path(row['path']);return p.stat().st_size==row['bytes'] and SHA(p.read_bytes())==row['sha256']
if __name__=='__main__':main()
