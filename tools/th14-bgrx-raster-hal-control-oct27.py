"""Own D3D9 HAL controls for opaque-alpha X8 render targets and A8 controls."""
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
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    spec=importlib.util.spec_from_file_location('types',ROOT/'tools/th14-gpu-raster-native.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);P,U,I,F=t.P,t.U,t.I,t.F
    spec=importlib.util.spec_from_file_location('storage',ROOT/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)
    header=t.SDK.read_text(encoding='utf8');tables={}
    for name in['IDirect3D9','IDirect3DDevice9','IDirect3DSurface9']:
        body=header.split('DECLARE_INTERFACE_('+name+',',1)[1].split('};',1)[0]
        tables[name]={a.strip()or b.strip():i for i,(a,b)in enumerate(re.findall(r'STDMETHOD_\([^,]+,([^\)]+)\)|STDMETHOD\(([^\)]+)\)',body))}
    def call(obj,interface,name,signature,values):
        addr=C.cast(obj,C.POINTER(C.POINTER(P))).contents[tables[interface][name]];value=C.WINFUNCTYPE(I,P,*signature)(addr)(obj,*values)
        assert value>=0,(name,hex(value&0xffffffff));return value
    width=height=16;window=None;d3d=P();device=P();resources=[];cases=[]
    user=C.WinDLL('user32');user.CreateWindowExW.restype=P;user.CreateWindowExW.argtypes=[U,C.c_wchar_p,C.c_wchar_p,U,I,I,I,I,P,P,P,P];user.DestroyWindow.argtypes=[P]
    dll=C.WinDLL('d3d9');dll.Direct3DCreate9.restype=P;dll.Direct3DCreate9.argtypes=[U]
    d3dx_path=Path('C:/Windows/System32/d3dx9_43.dll');d3dx=C.WinDLL(str(d3dx_path));convert=d3dx.D3DXLoadSurfaceFromSurface;convert.argtypes=[P,P,P,P,P,P,U,U];convert.restype=I
    raw_upper_values={}
    # D3D enums: source/destination factors, operation, enabled.
    blends=[('replace',2,1,1,False),('source-alpha',5,6,1,True),('destination-alpha',7,1,1,True),
        ('inverse-destination-alpha',8,2,1,True),('source-alpha-saturate',11,2,1,True),
        ('add',2,2,1,True),('subtract',5,6,2,True),('reverse-subtract',5,6,3,True)]
    try:
        window=user.CreateWindowExW(0,'STATIC','TH14 BGRX HAL component',0,0,0,width,height,None,None,None,None);assert window
        d3d=P(dll.Direct3DCreate9(32));assert d3d;pp=t.Present(width,height,21,1,0,0,1,window,1,0,0,0,0,0x80000000)
        call(d3d,'IDirect3D9','CreateDevice',[U,U,P,U,P,C.POINTER(P)],[0,1,window,0x40,C.byref(pp),C.byref(device)])
        def rs(key,value):call(device,'IDirect3DDevice9','SetRenderState',[U,U],[key,value])
        def ts(stage,key,value):call(device,'IDirect3DDevice9','SetTextureStageState',[U,U,U],[stage,key,value])
        for key,value in[(7,0),(14,0),(15,0),(22,1),(27,0),(28,0),(52,0),(137,0),(168,15),(174,0),(206,0)]:rs(key,value)
        for key,value in[(1,2),(2,0),(4,2),(5,0)]:ts(0,key,value)
        ts(1,1,1);call(device,'IDirect3DDevice9','SetTexture',[U,P],[0,None]);call(device,'IDirect3DDevice9','SetFVF',[U],[0x44])
        call(device,'IDirect3DDevice9','SetDepthStencilSurface',[P],[None]);vp=t.Viewport(0,0,width,height,0,1);call(device,'IDirect3DDevice9','SetViewport',[P],[C.byref(vp)])
        for fmt in[21,22]:
            rt=P();back=P();canonical=P();call(device,'IDirect3DDevice9','CreateRenderTarget',[U,U,U,U,U,I,C.POINTER(P),P],[width,height,fmt,0,0,0,C.byref(rt),None]);resources.append(rt)
            call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[width,height,fmt,2,C.byref(back),None]);resources.append(back)
            call(device,'IDirect3DDevice9','CreateOffscreenPlainSurface',[U,U,U,U,C.POINTER(P),P],[width,height,21,2,C.byref(canonical),None]);resources.append(canonical)
            call(device,'IDirect3DDevice9','SetRenderTarget',[U,P],[0,rt])
            lock=t.Lock()
            def pixels():
                call(device,'IDirect3DDevice9','GetRenderTargetData',[P,P],[rt,back]);call(back,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
                raw=b''.join(C.string_at(lock.bits+y*lock.pitch,width*4)for y in range(height));call(back,'IDirect3DSurface9','UnlockRect',[],[])
                result=convert(canonical,None,None,rt,None,None,2,0);assert result>=0,hex(result&0xffffffff)
                call(canonical,'IDirect3DSurface9','LockRect',[P,P,U],[C.byref(lock),None,16])
                converted=b''.join(C.string_at(lock.bits+y*lock.pitch,width*4)for y in range(height));call(canonical,'IDirect3DSurface9','UnlockRect',[],[])
                if fmt==21:assert raw==converted
                else:assert all(converted[i]==255 for i in range(3,len(converted),4))
                return raw,converted
            def clear(color,rects=None):
                data=(I*(len(rects)*4))(*(v for box in rects for v in box))if rects else None
                call(device,'IDirect3DDevice9','Clear',[U,P,U,U,F,U],[len(rects)if rects else 0,C.byref(data)if data is not None else None,1,color,1,0])
            def draw(color,left,top,right,bottom):
                raw=b''.join(struct.pack('<4fI',x-.5,y-.5,.5,1,color)for x,y in[(left,top),(right,top),(left,bottom),(right,bottom)])
                vertices=C.create_string_buffer(raw);call(device,'IDirect3DDevice9','BeginScene',[],[]);call(device,'IDirect3DDevice9','DrawPrimitiveUP',[U,U,P,U],[5,2,vertices,20]);call(device,'IDirect3DDevice9','EndScene',[],[])
            for alpha,blend,mask,source_alpha in itertools.product([0,49,199,255],blends,[0,1,2,4,7,8,15],[0,127,255]):
                name,sb,db,op,enabled=blend;clear_color=alpha<<24|0x398db7;partial_color=(255-alpha)<<24|0x7124c3
                rs(168,mask);clear(clear_color);clear(partial_color,[[2,3,11,12],[8,9,15,16]])
                buffers=dict(clear=pixels());rs(27,int(enabled));rs(19,sb);rs(20,db);rs(171,op)
                source_color=source_alpha<<24|0xc05329;draw(source_color,0,0,width,height);buffers['first']=pixels()
                # A later destination-alpha blend observes the stored alpha.
                rs(27,1);rs(19,7);rs(20,8);rs(171,1);rs(168,15)
                draw(0x6b27a1d3,4,5,14,15);buffers['chain']=pixels()
                index=len(cases);row=dict(index=index,format=fmt,clearColor=clear_color,partialColor=partial_color,rectangles=[[2,3,11,12],[8,9,15,16]],
                    blendName=name,sourceBlend=sb,destinationBlend=db,blendOperation=op,blendEnabled=enabled,colorMask=mask,sourceColor=source_color,buffers={})
                for label,(raw,converted)in buffers.items():
                    if fmt==22:raw_upper_values.setdefault(label,set()).update(raw[3::4])
                    file=f'case-{index:04d}-{label}.bgra';raw_file=f'case-{index:04d}-{label}.raw';(out/file).write_bytes(converted);(out/raw_file).write_bytes(raw)
                    row['buffers'][label]=dict(file=file,bytes=len(converted),sha256=SHA(converted),rawFile=raw_file,rawSha256=SHA(raw))
                cases.append(row)
        assert len(cases)==1344
        result=dict(schema='th14/bgrx-hal-raster-control/1',caseCount=len(cases),width=width,height=height,cases=cases,
            actualD3d9Hal=True,originalGameProcess=False,visibleWindow=False,physicalAudioDevicesOpened=0,x8CanonicalAlphaAlwaysOpaque=True,
            actualD3dxFormatConversion=True,x8RawUpperByteValues={key:sorted(value)for key,value in raw_upper_values.items()},d3dxSha256=storage.sha256_file(d3dx_path),
            formats=[21,22],clearAlphaValues=[0,49,199,255],sourceAlphaValues=[0,127,255],colorMasks=[0,1,2,4,7,8,15],
            toolSha256=SHA(Path(__file__).read_bytes()),d3d9Sha256=storage.sha256_file(Path('C:/Windows/System32/d3d9.dll')),
            sdkHeaderSha256=SHA(header.encode()),completeGame=False,nativeEquivalent=False,browserAcceptance=False,
            scope='Own D3D9 HAL full/partial Clear,8 blend families,7 write masks,source/destination alpha controls and a subsequent destination-alpha blend; A8 and X8 targets. Full retained buffers, no original game, audio or browser.')
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key]for key in['caseCount','formats','x8CanonicalAlphaAlwaysOpaque','x8RawUpperByteValues']}))
    finally:
        for obj in resources:
            if obj.value:call(obj,'IDirect3DSurface9','Release',[],[])
        if device.value:call(device,'IDirect3DDevice9','Release',[],[])
        if d3d.value:call(d3d,'IDirect3D9','Release',[],[])
        if window:user.DestroyWindow(window)


if __name__=='__main__':main()
