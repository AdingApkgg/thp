"""Compare whole retail408690 ticks against old/current portable Timer.tick."""
from pathlib import Path
import hashlib,importlib,itertools,json,os,struct,subprocess,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/player-initialization-oracle-nov13';O=H/'timer-oracle'
O.mkdir();sys.path.insert(0,str(R/'tools'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert hashlib.sha256(image.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,count in image.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,image.data[off:off+count])
base=0x70000000;m.mem_map(base,0x10000);timer=base+0x1000;rate=base+0x2000;stack=base+0xf000;end=base+0xff00
rates=[0,0x80000000,0x3f000000,0x3f7d70a3,0x3f7d70a4,0x3f7d70a5,0x3f800000,0x3f8147ad,0x3f8147ae,0x3f8147af,0x3fc00000,0xbf800000,0x7f800000,0x7fc01234]
states=[(0,0),(17,0x418c0000),(0xfffffffd,0xc0300000),(0x7fffffff,0x4f000000)]
rows=[]
for value,(current,fraction),flags in itertools.product([None,*rates],states,[0,1,0x80000000,0xffffffff]):
 ptr=0 if value is None else rate
 m.mem_write(timer,struct.pack('<5I',0xfedcba98,current,fraction,ptr,flags))
 if value is not None:m.mem_write(rate,struct.pack('<I',value))
 m.mem_write(stack,struct.pack('<2I',end,0))
 for reg,word in [(UC_X86_REG_ECX,timer),(UC_X86_REG_ESP,stack),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,word)
 m.emu_start(0x408690,end,count=100)
 assert m.reg_read(UC_X86_REG_EIP)==end
 actual=list(struct.unpack('<5I',m.mem_read(timer,20)));actual[3]=int(bool(actual[3]))
 rows.append(dict(rate=value,current=current,fraction=fraction,flags=flags,expected=actual))
report=dict(rows=rows,originalEntry='0x408690',originalNullPageUnmapped=True,
            originalExecutableSha256=hashlib.sha256(image.data).hexdigest(),originalCodeUnmodified=True,
            toolSha256=sha(Path(__file__)),completeGame=False)
(O/'native.json').write_text(json.dumps(report,indent=2)+'\n')
provider=json.loads((R/'artifacts/th14/loading-control4-nov13/provider/build.json').read_bytes());cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==provider['compilerSha256']
flags=[f for f in provider['flags']if not f.startswith('-I')]+['-I'+str(R/'runtimes/th12/th12_web/cpp/game')]
builds={}
for name,header in [('baseline',H/'baseline-source/Timer.hpp'),('candidate',R/'runtimes/th12/th12_web/cpp/game/Timer.hpp')]:
 fixture=O/(name+'.cpp');fixture.write_text('''#include "'''+header.as_posix()+'''"
using namespace th11;
#define API(n) extern "C" __attribute__((export_name(#n)))
u32 out[5];
API(tick) const u32* tick(u32 current,u32 fraction,u32 flags,u32 hasRate,u32 rateBits){
 float value;std::memcpy(&value,&rateBits,4);float fractional;std::memcpy(&fractional,&fraction,4);
 Timer t{signed_bits(0xfedcba98),signed_bits(current),fractional,hasRate?&value:nullptr,flags};t.tick();
 u32 f;std::memcpy(&f,&t.fractional,4);out[0]=u32(t.previous);out[1]=u32(t.current);out[2]=f;out[3]=u32(t.rate!=nullptr);out[4]=t.flags;return out;
}
''',encoding='utf8')
 cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824',str(fixture),'-o',str(O/(name+'.wasm'))]
 with(O/(name+'.log')).open('wb')as log:subprocess.run(cmd,cwd=R,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=60)
 builds[name]=dict(wasmSha256=sha(O/(name+'.wasm')),fixtureSha256=sha(fixture),headerSha256=sha(header),command=cmd)
(O/'build.json').write_text(json.dumps(builds,indent=2)+'\n')
print(json.dumps(dict(nativeCases=len(rows),normalAccessControl=True,originalNullPageUnmapped=True)))
