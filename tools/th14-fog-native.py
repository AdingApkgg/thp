"""Retail ECL 557 fog setter and linear interpolation frames."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    end,entity,stage,stack,out=0x70000000,0x70001000,0x70008000,0x7001f000,0x70018000;m.mem_map(end,0x20000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    words=lambda p,n:[get(p+4*i) for i in range(n)]
    args=[];reads=[]
    def boundary(machine,address,size,user):
        n=get(m.reg_read(UC_X86_REG_ESP)+4);reads.append(n);m.reg_write(UC_X86_REG_EAX if address==0x42c1d0 else UC_X86_REG_XMM0,args[n])
    for a in (0x42c1d0,0x42c230):m.mem_write(a,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    def snapshot():return words(stage+0x158,14)+[get(stage+x) if x!=0x1f0 else int(get(stage+x)!=0) for x in range(0x1e4,0x200,4)]
    rows=[]
    for duration in (0,7,35):
     for rate in (.5,1,1.25):
      for color in (0,0x11223344,0x80ff00aa,0xffffffff):
        m.mem_write(entity,bytes(0x16000));reads.clear();put(0x4db528,stage);put(0x4d8f58,bits(rate))
        initial=[bits(15),bits(900),*[bits(float((0x668899aa>>(8*i))&255)) for i in range(4)],0x668899aa]
        for i,v in enumerate(initial):put(stage+0x4384+4*i,v)
        args[:]=[duration,0,color,bits(-3.25),bits(450.125)]
        m.reg_write(UC_X86_REG_EDI,entity);m.reg_write(UC_X86_REG_ESP,stack)
        m.emu_start(0x429954,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        configured=snapshot();frames=[]
        for frame in range(76):
            if get(stage+0x1f8):
                put(stack,end);put(stack+4,out);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,stage+0x158)
                m.emu_start(0x410940,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
                m.mem_write(stage+0x4384,bytes(m.mem_read(out,28)))
            frames.append(dict(fog=words(stage+0x4384,7),bands=snapshot()))
        rows.append(dict(duration=duration,rate=rate,color=color,initial=initial,configured=configured,reads=reads[:],frames=frames))
    (ROOT/'artifacts/th14/fog-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows))+'\n',encoding='utf8')
    print(f'{len(rows)} retail fog timelines')
if __name__=='__main__':main()
