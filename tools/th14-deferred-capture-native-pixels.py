"""Own hidden original32 D3DX HAL copy controls, never launches retail TH14."""
import gzip,hashlib,importlib.util,json,os,struct,subprocess
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/deferred-capture-pixels-oct14';OUT.mkdir(parents=True,exist_ok=True)
SHA=lambda b:hashlib.sha256(b).hexdigest()
def bind(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':SHA(p.read_bytes())}
def frozen(p,b):
    if p.exists():assert p.read_bytes()==b,('immutable capture',str(p))
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
    assert not (OUT/'native.json').exists(),'Completed capture is immutable'
    hp=ROOT/'tools/th14-loading-lifecycle-evidence-check.py';spec=importlib.util.spec_from_file_location('capture_image',hp);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);image=h.Image()
    native=ROOT/'artifacts/th14/native-zps-reimua-lunatic-full-oct14';manifest=json.loads((native/'manifest.json').read_bytes());assert SHA((native/'memory.bin.gz').read_bytes())==manifest['memorySha256']
    sup=None
    with gzip.open(native/'memory.bin.gz','rb') as f:
        for r in manifest['regions']:
            b=f.read(r['bytes']);assert len(b)==r['bytes'] and SHA(b)==r['sha256']
            if r['base']<=0x4d8f60 and 0x4d9120<=r['base']+r['bytes']:sup=b[0x4d8f60-r['base']:0x4d9120-r['base']]
        assert not f.read(1)
    assert sup is not None
    pp=list(struct.unpack_from('<14I',sup,0xf4));assert pp[:4]==[640,480,21,1]
    frozen(OUT/'native-supervisor-prefix.bin',sup)
    loader=ROOT/'artifacts/th14/anm-physical-resource-loader/native.json';table=json.loads(loader.read_bytes());text=next(r for r in table['rows'] if r['name']=='text.anm' and r['rate']==1);target=text['uploads'][1];assert target['creationArguments']==[512,512,1,0,23,1]
    menu=ROOT/'docs/porting/th14-deferred-capture-intrinsic-code-verified-oct14.json';entry=json.loads(menu.read_bytes())['cases'][4]['entry'];assert entry[:10]==[0,1,32,16,384,448,0,0,256,256]
    rows=[('actual_text52',23,[32,16,416,464],[0,0,256,256]),('nonzero_destination',23,[32,16,416,464],[17,29,273,285]),('odd_scale',23,[11,7,394,456],[13,19,268,272]),('identity_scale',23,[32,16,416,464],[5,7,389,455]),('upsample',23,[33,17,160,146],[31,47,286,304]),('micro_scale',23,[37,41,54,54],[71,83,82,90]),('argb8_coordinate_control',21,[32,16,416,464],[17,29,273,285]),('argb8_odd_control',21,[11,7,394,456],[13,19,268,272])]
    cases=[];params=[]
    for index,(name,fmt,src,dst) in enumerate(rows):
        record=[0,1,src[0],src[1],src[2]-src[0],src[3]-src[1],dst[0],dst[1],dst[2]-dst[0],dst[3]-dst[1]]
        u=image.machine();u.mem_write(0x620000,struct.pack('<10i',*record));h.word(u,0x4d9114,0x640014);h.word(u,0x7ff000-0x28,0x640028)
        u.reg_write(UC_X86_REG_ESI,0x620008);u.reg_write(UC_X86_REG_EBP,0x7ff000);u.reg_write(UC_X86_REG_ESP,0x7ff100);u.emu_start(0x46914d,0x46919d,count=100)
        assert u.reg_read(UC_X86_REG_EIP)==0x46919d
        arguments=list(struct.unpack('<8I',u.mem_read(u.reg_read(UC_X86_REG_ESP),32)));actual_src=list(struct.unpack('<4i',u.mem_read(arguments[5],16)));actual_dst=list(struct.unpack('<4i',u.mem_read(arguments[2],16)))
        assert arguments[0]==0x640028 and arguments[1]==0 and arguments[3]==0x640014 and arguments[4]==0 and arguments[6:]==[2,0] and actual_src==src and actual_dst==dst
        cases.append(dict(index=index,name=name,destinationFormat=fmt,sourceRect=src,destinationRect=dst,request=record,textureWidth=512,textureHeight=512,bpp=2 if fmt==23 else 4,role='actual_request' if index==0 else 'declared_control'))
        params.append(dict(name=name,entry='0x46914d',stop='0x46919d',originalInstructionsExecuted=True,hostCallsExecuted=0,arguments=arguments,sourceRect=actual_src,destinationRect=actual_dst))
    source=bytes(c for y in range(480) for x in range(640) for c in ((x*97+y*31+11)&255,(x*41+y*73+19)&255,(x*53+y*109+37)&255,(x*17+y*29+131)&255))
    request=b'TH14CAP\0'+struct.pack('<I',len(cases))+source+b''.join(struct.pack('<9I',c['destinationFormat'],*c['sourceRect'],*c['destinationRect']) for c in cases)
    frozen(OUT/'source.bgra',source);frozen(OUT/'requests.bin',request)
    inputs=dict(cases=cases,sourceWidth=640,sourceHeight=480,sourceFormat=21,sourceSha256=SHA(source),sourceBytes=len(source),sourcePixelFormula='BGRA: (97x+31y+11,41x+73y+19,53x+109y+37,17x+29y+131) modulo256',targetRgb565Prefill=0x5a6b,targetArgb8Prefill=0x917c3a5e,filter=2,colorKey=0,nativePresentParameters=pp,nativeBackbufferHandle=hex(struct.unpack_from('<I',sup,0x1b4)[0]),nativeParameterControls=params)
    frozen(OUT/'inputs.json',(json.dumps(inputs,indent=2)+'\n').encode())
    vc=Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207');sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0';env=dict(os.environ)
    env['INCLUDE']=';'.join(str(p) for p in [vc/'include',sdk/'Include'/version/'ucrt',sdk/'Include'/version/'shared',sdk/'Include'/version/'um'])
    env['LIB']=';'.join(str(p) for p in [vc/'lib/x86',sdk/'Lib'/version/'ucrt/x86',sdk/'Lib'/version/'um/x86'])
    helper=ROOT/'tools/th14-deferred-capture-surface32-helper.cpp';exe=OUT/'capture32.exe';flags=['/nologo','/O2','/EHsc','/std:c++17',str(helper),'/Fe:'+str(exe),'/Fo:'+str(OUT/'capture32.obj'),'d3d9.lib','user32.lib']
    compilation=subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),*flags],cwd=OUT,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);frozen(OUT/'native-build.log',compilation.stdout+compilation.stderr);assert compilation.returncode==0,compilation.stdout.decode(errors='replace')
    p=subprocess.run([str(exe),str(OUT/'requests.bin'),str(OUT/'native-output.bin')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);frozen(OUT/'native-run.log',p.stdout+p.stderr);assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
    raw=(OUT/'native-output.bin').read_bytes();pre,post,count=struct.unpack_from('<3I',raw);assert count==len(cases) and post&0x30000==0x20000;desc=list(struct.unpack_from('<8I',raw,12));assert [desc[0],desc[6],desc[7]]==[21,640,480]
    offset=44;backbuffer=raw[offset:offset+len(source)];assert backbuffer==source;frozen(OUT/'native-source.bgra',backbuffer);offset+=len(source)
    observed=[]
    for c in cases:
        level,copy,dirty=struct.unpack_from('<3i',raw,offset);td=list(struct.unpack_from('<8I',raw,offset+12));offset+=44;assert level==copy==dirty==0 and [td[0],td[6],td[7]]==[c['destinationFormat'],512,512]
        size=512*512*c['bpp'];pixels=raw[offset:offset+size];assert len(pixels)==size;offset+=size;name=f"native-{c['index']:03d}.pixels";frozen(OUT/name,pixels)
        observed.append(dict(**c,getSurfaceResult=level,copyResult=copy,dirtyResult=dirty,surfaceDescription=td,bytes=size,pixelFile=name,pixelSha256=SHA(pixels)))
    assert offset==len(raw)
    md=Cs(CS_ARCH_X86,CS_MODE_32);asm=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str,bytes=i.bytes.hex()) for i in md.disasm(image.bytes(0x46914d,0x86),0x46914d)]
    report=dict(nativePixelControlsCaptured=True,productionChanged=False,completeGame=False,nativeEquivalent=False,cases=observed,actualSourceDescription=desc,sourceUploadReadbackByteExact=True,filter=2,colorKey=0,preDeviceControl=pre,postDeviceControl=post,retailExecutableSha256=h.EXPECTED_EXE_SHA,callImport=image.imports()[0x4b12bc],nativeCode=asm,sourceModuleBindings=[bind(Path('C:/Windows/SysWOW64/d3d9.dll')),bind(Path('C:/Windows/SysWOW64/d3dx9_43.dll'))],bindings=[bind(helper),bind(exe),bind(hp),bind(loader),bind(menu),bind(native/'manifest.json'),bind(OUT/'inputs.json'),bind(OUT/'source.bgra'),bind(OUT/'requests.bin'),bind(OUT/'native-output.bin')],compiler=str(vc/'bin/Hostx64/x86/cl.exe'),compilerFlags=flags,toolSha256=SHA(Path(__file__).read_bytes()),scope='Own hidden original32 system D3D9 HAL backbuffer and original32 D3DXLoadSurfaceFromSurface. Same captured640x480 ARGB8 present configuration; actual own GetDesc and source upload/readback bound. Real text52 target512x512 RGB565 and actual request plus explicit rectangle/offset/ARGB8 controls. No retail child, visible window, Present, reconstructed Native output, or full game frame equivalence. Null target retirement is a separate unchanged-original queue evidence contract.')
    frozen(OUT/'native.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'nativePixelControlsCaptured':True,'cases':count,'bytes':sum(c['bytes'] for c in observed),'actualSourceDescription':desc}))
if __name__=='__main__':main()
