"""Compare production replay FPS text with the complete retail455380 body.

CRT formatting and ASCII queue delivery are declared component boundaries.
Independent actual-game full-buffer comparison is required for raster claims.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,os,struct,subprocess,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_MXCSR

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--wasmtime-site',type=Path,default=ROOT/'tools/tmp/th14-native-gles-python/site')
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    out.mkdir(parents=True);sys.path.insert(0,str(a.wasmtime_site));import wasmtime as W
    fixture='''#include "ReplayTextTh14.hpp"
#include <cstring>
static unsigned bits(float value){unsigned word;std::memcpy(&word,&value,4);return word;}
extern "C" const unsigned* probe(unsigned controller,unsigned mode,unsigned fps){
 static th11::AsciiRequest request;static unsigned words[12];
 words[0]=th11::th14_replay_fps_request(controller!=0,mode,(th11::u8)fps,request);
 words[1]=(unsigned)(uintptr_t)request.text.c_str();
 words[2]=bits(request.position.x);words[3]=bits(request.position.y);words[4]=bits(request.position.z);
 words[5]=request.style.color;words[6]=bits(request.style.scale.x);words[7]=bits(request.style.scale.y);
 words[8]=request.style.font;words[9]=request.style.shadow;words[10]=request.style.pass;words[11]=request.style.playfield;
 return words;
}
'''
    source=out/'probe.cpp';source.write_text(fixture)
    compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    cmd=[str(compiler),'--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
        '-I'+str(ROOT/'runtimes/th12/th12_web/cpp/game'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export=probe','-Wl,--export-memory',str(source),'-o',str(out/'probe.wasm')]
    result=subprocess.run(cmd,capture_output=True,env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)})
    (out/'compile.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr
    engine=W.Engine();store=W.Store(engine);store.set_wasi(W.WasiConfig());linker=W.Linker(engine);linker.define_wasi()
    api=linker.instantiate(store,W.Module.from_file(engine,str(out/'probe.wasm'))).exports(store);api['_initialize'](store);memory=api['memory']
    img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x40000);owner=base+0x1000;ascii_owner=base+0x10000;stack=base+0x3f000
    put=lambda at,value:m.mem_write(at,struct.pack('<I',value&0xffffffff))
    get=lambda at:struct.unpack('<I',m.mem_read(at,4))[0]
    requests=[]
    def capture(uc,pc,size,data):
        if pc!=0x40bb10:return
        sp=uc.reg_read(UC_X86_REG_ESP);position=get(sp+8);fmt=bytes(uc.mem_read(get(sp+12),16)).split(b'\0',1)[0].decode('ascii')
        assert fmt=='%3d';fps=get(sp+16)
        requests.append(dict(text=fmt%fps,words=[get(position+i*4)for i in range(3)]+[get(ascii_owner+i)for i in (0x191b0,0x191b4,0x191b8,0x191c8,0x191c4,0x191cc)]+[0]))
        uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
    m.hook_add(UC_HOOK_CODE,capture);rows=[]
    for controller in (0,1):
        for mode in (0,1,2,3):
            for fps in range(256):
                m.mem_write(base,bytes(0x3e000));requests.clear()
                for at,value in [(0x4db558,controller),(0x4db520,ascii_owner),(owner+0x10,mode),(owner+0x20c,fps),
                    (ascii_owner+0x191b0,0xff123456),(ascii_owner+0x191b4,0x3f800000),(ascii_owner+0x191b8,0x3f800000),(stack,base)]:put(at,value)
                m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
                m.emu_start(0x455380,base,count=1000);assert m.reg_read(UC_X86_REG_EIP)==base
                pointer=api['probe'](store,controller,mode,fps);words=list(struct.unpack('<12I',memory.read(store,pointer,pointer+48)))
                expected=bool(requests);assert words[0]==expected and len(requests)<=1
                if expected:
                    text=bytes(memory.read(store,words[1],words[1]+16)).split(b'\0',1)[0].decode()
                    assert text==requests[0]['text']and words[2:]==requests[0]['words']
                    assert get(ascii_owner+0x191b0)==0xffffffff
                else:assert get(ascii_owner+0x191b0)==0xff123456
                rows.append(dict(controller=controller,mode=mode,fps=fps,requests=list(requests),passed=True))
    header=ROOT/'runtimes/th12/th12_web/cpp/game/ReplayTextTh14.hpp'
    report=dict(passed=True,cases=len(rows),queuedCases=sum(bool(x['requests'])for x in rows),rows=rows,
        actualRetailEntry=0x455380,actualRetailAsciiBoundary=0x40bb10,nativeExecutableSha256=SHA(img.data),
        productionHeaderSha256=SHA(header.read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
        wasmSha256=SHA((out/'probe.wasm').read_bytes()),fixtureSha256=SHA(source.read_bytes()),compilerSha256=SHA(compiler.read_bytes()),
        nativeAsciiStyleControlled=dict(font=0,shadow=False,scale=[1,1],passIndex=0),
        scope='Whole retail455380 and actual production header; all256 recorded-rate bytes, controller and four manager modes; text/position/color/default style and native color restoration. Formatting/ASCII queue boundary controlled. No native renderer, browser or whole-game acceptance.',
        physicalAudioDevicesOpened=0,completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),queuedCases=report['queuedCases'])))


if __name__=='__main__':main()
