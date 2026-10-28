"""Compare retail455180 with actual production Replay::tick at FPS/terminal edges.

The native reader receives controlled decoded records. Its41e710 edge routine
executes;448ef0 is a declared pause-request boundary. No OS/game UI is driven.
The C++ reader opens containers encoded by the actual production codec first.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,os,struct,subprocess,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX,UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
FIXTURE=r'''#include "Replay.hpp"
#include "Lzss.hpp"
#include "ResourceCrypt.hpp"
#include <cstdlib>
#include <cstring>
using namespace th11;
static Replay reader;
static void put(u8* p,u32 v){std::memcpy(p,&v,4);}
extern "C" int begin(const u8* data,u32 size,u32 selected){
 Lzss codec;auto packed=codec.encode(data,size);if(packed.empty())return 0;
 const u32 n=u32(packed.size());std::vector<u8> first(n),second(n),container(0x24+n);
 if(!resource_crypt(packed.data(),first.data(),n,{0x7d,0x3a,0x100,n},true)||
    !resource_crypt(first.data(),second.data(),n,{0x5c,0xe1,0x400,n},true))return 0;
 put(container.data(),0x72333174);put(container.data()+4,2);put(container.data()+28,n);put(container.data()+32,size);
 std::memcpy(container.data()+0x24,second.data(),n);
 if(!reader.open(container.data(),u32(container.size()))||reader.decoded().size()!=size||
    std::memcmp(reader.decoded().data(),data,size))return 0;
 return !selected||reader.select(selected);
}
extern "C" const u32* tick(u32 active){
 const auto x=reader.tick(active!=0);static u32 words[8];
 words[0]=reader.frame();words[1]=x.fps;words[2]=x.end_marker;words[3]=x.held;
 words[4]=x.previous;words[5]=x.pressed;words[6]=x.released;words[7]=reader.selected_stage();return words;
}
'''


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('core-build','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--compile-current-reader',action='store_true')
    p.add_argument('--wasmtime-site',type=Path,default=ROOT/'tools/tmp/th14-native-gles-python/site')
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    core_raw=a.core_build.read_bytes();core=json.loads(core_raw);objects=[];bindings=[];sources={}
    source_home=ROOT/'runtimes/th12/th12_web/cpp/game'
    for name in ('Replay.cpp','ResourceCrypt.cpp','Lzss.cpp'):
        key='th12_web/cpp/game/'+name;digest=core['sourceHashes'][key];sources[key]=digest
        row=next(x for x in core['objectBindings']if Path(x['path']).name==name+'.o')
        assert SHA(Path(row['path']).read_bytes())==row['sha256']
        objects.append(row['path']);bindings.append(dict(row))
    headers={}
    for name in ('Replay.hpp','ResourceCrypt.hpp','Lzss.hpp','Types.hpp','PortTitle.hpp'):
        digest=SHA((source_home/name).read_bytes());assert digest==core['headerHashes']['th12_web/cpp/game/'+name];headers[name]=digest
    compiler=ROOT/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
    env={**os.environ,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    if a.compile_current_reader:
        source=out/'Replay.cpp';source.write_bytes((source_home/'Replay.cpp').read_bytes());obj=out/'Replay.cpp.o'
        result=subprocess.run([str(compiler),*core['flags'],'-c',str(source),'-o',str(obj)],capture_output=True,env=env)
        (out/'reader.compile.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr
        objects[0]=str(obj);bindings[0]=dict(path=str(obj),sha256=SHA(obj.read_bytes()));sources['th12_web/cpp/game/Replay.cpp']=SHA(source.read_bytes())
    else:assert sources['th12_web/cpp/game/Replay.cpp']==SHA((source_home/'Replay.cpp').read_bytes())
    fixture=out/'fixture.cpp';fixture.write_text(FIXTURE);wasm=out/'reader.wasm'
    command=[str(compiler),*core['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',
        '-Wl,-z,stack-size=1048576',*['-Wl,--export='+x for x in ('begin','tick','malloc','free')],str(fixture),*objects,'-o',str(wasm)]
    result=subprocess.run(command,capture_output=True,env=env);(out/'link.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr
    sys.path.insert(0,str(a.wasmtime_site));import wasmtime as W
    engine=W.Engine();store=W.Store(engine);store.set_wasi(W.WasiConfig());linker=W.Linker(engine);linker.define_wasi()
    api=linker.instantiate(store,W.Module.from_file(engine,str(wasm))).exports(store);api['_initialize'](store);memory=api['memory']
    img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        page=b&~4095;m.mem_map(page,((b+size+4095)&~4095)-page);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x100000);manager=base+0x1000;header=base+0x3000;inputs=base+0x4000;rates=base+0x8000;stack=base+0xff000
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    pause_calls=[];fps_reads=[];fps=b''
    def pause_boundary(uc,pc,size,data):
        if pc==0x45529a:
            offset=uc.reg_read(UC_X86_REG_EAX)-rates
            assert 0<=offset<len(fps),'Native FPS read outside explicitly defined component data'
            fps_reads.append(offset);return
        if pc!=0x448ef0:return
        pause_calls.append(pc);sp=uc.reg_read(UC_X86_REG_ESP)
        uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EAX,1)
    m.hook_add(UC_HOOK_CODE,pause_boundary,begin=0x448ef0,end=0x448ef0)
    m.hook_add(UC_HOOK_CODE,pause_boundary,begin=0x45529a,end=0x45529a)
    original=ROOT/'artifacts/th14/native-frame-readback-oct28/browser-replay/native-codec/decoded.bin'
    if not original.exists():original=ROOT/'artifacts/th14/native-frame-readback-oct28/browser-replay/production-codec/decoded.bin'
    template=original.read_bytes();assert len(template)==4694 and SHA(template)=='c350adf403fa2651910c9b99b99c7ca0e5f21a028e9a4d87727e539aa94ea255'
    cases=[];mismatches=[];steps_total=0
    positions=(0,1,2,29,30,31,32,59,60,61,62,89,90,91,119,120,121)
    for terminal in (*positions,None):
        frames=terminal+1 if terminal is not None else 122
        for padding in (0,2):
            valid=frames-1 if terminal is not None else frames
            #455180 advances its FPS pointer after ticks0,30,... . Supply
            # every byte it will actually read; zero-filled arena tail is
            # not evidence of the original's out-of-payload behaviour.
            count=0 if valid==0 else 1 if valid==1 else 2+(valid-2)//30
            fps=bytes((29+37*i)%256 for i in range(count+padding))
            data=bytearray()
            for tick in range(frames):
                held=(tick*17)&0x21f
                data+=b'\xff'*6 if tick==terminal else struct.pack('<3H',held,0,0)
            decoded=bytearray(template[:0x94+0xdc]);struct.pack_into('<II',decoded,0x94+4,frames,len(data)+len(fps));decoded+=data+fps
            pointer=api['malloc'](store,len(decoded));memory.write(store,decoded,pointer)
            assert api['begin'](store,pointer,len(decoded),1)==1;api['free'](store,pointer)
            m.mem_write(base,bytes(0xfe000));m.mem_write(0x4d6878,bytes(0x240));put(0x4db558,1)
            m.mem_write(header,bytes(decoded[0x94:0x94+0xdc]));m.mem_write(inputs,bytes(data));m.mem_write(rates,fps or b'\0')
            put(manager+0x218,1);put(manager+0x210,0);slot=manager+40
            for off,value in ((0xd8,header),(0xcc,inputs),(0xd4,rates),(0xdc,0)):put(slot+off,value)
            active=[]
            for tick in range(frames+3):
                if tick in (0,1,29,30,31,60,frames):active.extend((False,False))
                active.append(True)
            rows=[]
            for step,running in enumerate(active):
                pause_calls.clear();fps_reads.clear()
                if running:
                    put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
                    m.emu_start(0x455180,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
                pointer=api['tick'](store,int(running));actual=list(struct.unpack('<8I',memory.read(store,pointer,pointer+32)))
                expected=[get(slot+0xdc),int(m.mem_read(manager+0x20c,1)[0]),int(bool(pause_calls))]
                assert get(slot+0xdc)==get(manager+0x210)
                equal=expected[:2]==actual[:2]and(not running or expected[2]==actual[2])
                row=dict(step=step,active=running,native=expected,cpp=actual[:3],nativeFpsReadOffsets=list(fps_reads),equal=equal)
                rows.append(row);steps_total+=1
                if not equal:mismatches.append(dict(case=len(cases),terminal=terminal,extraFpsBytes=padding,**row))
            cases.append(dict(terminal=terminal,frames=frames,extraFpsBytes=padding,recordedRates=list(fps),
                decodedSha256=SHA(decoded),cppOpenedProductionEncodedContainer=True,rows=rows))
    report=dict(passed=not mismatches,cases=len(cases),steps=steps_total,records=cases,mismatches=mismatches,
        firstMismatch=mismatches[0]if mismatches else None,sourceBindings=sources,headerBindings=headers,objectBindings=bindings,
        readerCompiledFromCurrentSource=a.compile_current_reader,wasmSha256=SHA(wasm.read_bytes()),fixtureSha256=SHA(fixture.read_bytes()),
        toolSha256=SHA(Path(__file__).read_bytes()),nativeExecutableSha256=SHA(img.data),coreBuildSha256=SHA(core_raw),
        comparedFields=['stage input cursor','recorded FPS byte','active terminal pause-request versus ReplayInput.end_marker'],
        nativeEntry=0x455180,nativeKeyboardEdgesExecute=True,nativePauseRequestControlledAt=0x448ef0,
        allNativeFpsReadsCheckedWithinExplicitData=True,nativeOutOfPayloadReadsExcluded=True,
        cppActualProductionCodecRoundTrip=True,rawReplayWordsAndNormalizedNativeInputNotConflated=True,
        noPhysicalGameOrBrowserOrAudio=True,completeGame=False,nativeEquivalent=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],cases=len(cases),steps=steps_total,mismatches=len(mismatches),firstMismatch=report['firstMismatch'])))
    if mismatches:raise SystemExit(1)


if __name__=='__main__':main()
