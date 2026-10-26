"""Measure finite rectangle color/depth/stencil Clear controls on an own D3D9 HAL.

No game executable, original resources, application input or audio is involved.
The device owns an undisplayed window handle and closes it on every exit path.
"""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import importlib.util
import itertools
import json
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir();spec=importlib.util.spec_from_file_location('types',ROOT/'tools/th14-gpu-raster-native.py')
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);P,U,I,F=t.P,t.U,t.I,t.F
    spec=importlib.util.spec_from_file_location('storage',ROOT/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
    header=t.SDK.read_text(encoding='utf8');types_raw=t.SDK.with_name('d3d9types.h').read_bytes();types=types_raw.decode();tables={}
    for name,value in [('D3DFMT_D24S8',75),('D3DRS_STENCILENABLE',52),('D3DRS_STENCILFUNC',56),('D3DRS_STENCILREF',57),('D3DRS_STENCILMASK',58),('D3DRS_STENCILWRITEMASK',59)]:
        assert re.search(r'\b'+name+r'\s*=\s*'+str(value)+r'\b',types),name
    for name in ['IDirect3D9','IDirect3DDevice9','IDirect3DSurface9']:
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        tables[name]={a.strip()or b.strip():index for index,(a,b)in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
    def call(obj,interface,name,signature,values):
        address=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]]
        value=C.WINFUNCTYPE(I,P,*signature)(address)(obj,*values)
        assert value>=0,(name,hex(value&0xffffffff));return value
    width,height=64,48;window=None;d3d=P();device=P();rt=P();depth=P();back=P();cases=[]
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
    dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 stencil clear HAL component',0,0,0,width,height,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d
        pp=t.Present(width,height,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[width,height,21,0,0,0,C.byref(rt),None])
        call(device,'IDirect3DDevice9','CreateDepthStencilSurface',[U,U,U,U,U,I,C.POINTER(P),P],[width,height,75,0,0,1,C.byref(depth),None])
        call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[width,height,21,2,C.byref(back),None])
        call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt]);call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[depth])
        viewport=t.Viewport(0,0,width,height,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(viewport)])
        def rs(key,value):call(device,'IDirect3DDevice9','SetRenderState',[U,U],[key,value])
        def ts(key,value):call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[0,key,value])
        for key,value in [(7,0),(14,0),(15,0),(22,1),(27,0),(28,0),(53,1),(54,1),(55,1),(56,3),(58,255),(59,0),(137,0),(168,15),(174,0)]:rs(key,value)
        for key,value in [(1,2),(2,0),(4,2),(5,0)]:ts(key,value)
        call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[1,1,1]);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None]);call(device,'IDirect3DDevice9','SetFVF',[U],[0x44])
        vertices=b''.join(struct.pack('<4fI',x,y,.5,1,0xffffffff)for x,y in[(-.5,-.5),(width-.5,-.5),(-.5,height-.5),(width-.5,height-.5)])
        vb=C.create_string_buffer(vertices);lock=t.Lock()
        def clear(flags,color,z,stencil,rects=None):
            data=(I*(4*len(rects)))(*(v for rect in rects for v in rect))if rects else None
            call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[len(rects)if rects else 0,C.byref(data)if data is not None else None,flags,color,z,stencil])
        def pixels():
            call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,back]);call(back,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
            data=b''.join(C.string_at(lock.bits+y*lock.pitch,width*4)for y in range(height));call(back,'IDirect3DSurface9','UnlockRect',[],[]);return data
        def draw():
            call(device,'IDirect3DDevice9','BeginScene',[],[]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,vb,20]);call(device,'IDirect3DDevice9','EndScene',[],[])
        def expected(mask,fg,bg):return b''.join(struct.pack('<I',fg if mask(x,y)else bg)for y in range(height)for x in range(width))
        rectangles=[[[3,7,41,35]],[[2,3,30,23],[19,17,61,46]],[[0,0,64,1],[0,1,1,48],[63,0,64,48],[0,47,64,48]]]
        for index,(flags,stencil,rects)in enumerate(itertools.product([4,5,6,7],[0,1,127,128,255,256,0x12345678,0xffffffff],rectangles)):
            baseline=17;rs(52,0);rs(7,0);clear(7,0x7fb13257,.25,baseline)
            clear(flags,0x7fa15327,.75,stencil,rects)
            mask=lambda x,y:any(left<=x<right and top<=y<bottom for left,top,right,bottom in rects)
            buffers={};buffers['color']=pixels();assert buffers['color']==expected(mask,0x7fa15327 if flags&1 else 0x7fb13257,0x7fb13257)
            for ref,label in [(stencil&255,'new-stencil'),(baseline,'old-stencil')]:
                clear(1,0xff010203,0,0);rs(7,0);rs(52,1);rs(57,ref);draw();buffers[label]=pixels()
                wanted=lambda x,y:(stencil&255 if mask(x,y)else baseline)==ref
                assert buffers[label]==expected(wanted,0xffffffff,0xff010203),(index,label)
            clear(1,0xff030507,0,0);rs(52,0);rs(7,1);rs(23,2);draw();buffers['depth']=pixels()
            assert buffers['depth']==expected(lambda x,y:bool(flags&2)and mask(x,y),0xffffffff,0xff030507),(index,'depth')
            row=dict(index=index,flags=flags,stencil=stencil,rectangles=rects,buffers={})
            for label,raw in buffers.items():
                name=f'case-{index:03d}-{label}.bgra';(out/name).write_bytes(raw);row['buffers'][label]=dict(file=name,bytes=len(raw),sha256=SHA(raw))
            cases.append(row)
        result=dict(schema='th14/d3d9-stencil-clear-hal-control/1',width=width,height=height,cases=cases,caseCount=len(cases),allIndependentCpuExpectationsEqual=True,
            actualD3d9Hal=True,originalGameProcess=False,visibleWindow=False,physicalAudioDevicesOpened=0,
            shaderProbeIsFixedFunction=True,depthFormat='D24S8',stencilLow8BitControls=True,toolSha256=SHA(Path(__file__).read_bytes()),
            d3d9Sha256=storage.sha256_file(Path('C:/Windows/System32/d3d9.dll')),sdkHeaderSha256=SHA(header.encode()),sdkTypesSha256=SHA(types_raw),
            browserAcceptance=False,completeGame=False,nativeEquivalent=False,
            scope='Own hidden D3D9 HAL Clear color/depth/stencil rectangle controls,96 finite cases. Stencil equality and depth-less probes read through actual fixed-function draws, compared with independent byte-array expectations. No original game/window-input, browser or whole-renderer acceptance.')
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key]for key in ['caseCount','allIndependentCpuExpectationsEqual','actualD3d9Hal','depthFormat','stencilLow8BitControls']}))
    finally:
        for obj,interface in [(back,'IDirect3DSurface9'),(depth,'IDirect3DSurface9'),(rt,'IDirect3DSurface9'),(device,'IDirect3DDevice9'),(d3d,'IDirect3D9')]:
            if obj.value:call(obj,interface,'Release',[],[])
        if window:user.DestroyWindow(window)


if __name__=='__main__':main()
