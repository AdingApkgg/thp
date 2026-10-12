"""Execute TH14 ECL emitter setters; only argument access and memset are sinks."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,code,stack=0x70001000,0x70008000,0x7000f000;m.mem_map(0x70000000,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    args=[];reads=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x48f980:
            p,value,n=(get(sp+x) for x in (4,8,12));m.mem_write(p,bytes([value&255])*n);m.reg_write(UC_X86_REG_EAX,p)
        else:
            index=get(sp+4);reads.append(index);m.reg_write(UC_X86_REG_XMM0 if address==0x42c230 else UC_X86_REG_EAX,args[index]&0xffffffff)
    for address,cleanup in ((0x48f980,0),(0x42c230,4),(0x42c1d0,4)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    entries={600:0x427a43,602:0x427ccb,603:0x427d05,604:0x427e3b,605:0x427e79,606:0x427eb7,607:0x428325,608:0x428352,
        609:0x42838c,610:0x42838c,611:0x42838c,612:0x42838c,614:0x427b09,624:0x427ef3,625:0x427f67,626:0x427d3a,627:0x427da0,628:0x427dce,641:0x428589}
    cases=[];f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    for op,entry in entries.items():
        for n in range(32):
            m.mem_write(base,bytes(0x9000));reads.clear();index=n%16;difficulty=(-1,0,1,2,3,4)[n%6]
            initial=b''.join(struct.pack('<I',(0x12345678+k*0x12345+n*0x456789)&0xffffffff) for k in range(0x39c0//4))
            m.mem_write(base+0x598,initial)
            for k in range(16):put(base+0x3d98+k*4,(n+k)%18)
            if op==641:put(base+0x3d98+index*4,(0,1,18,0x80000000)[n%4])
            args[:]=[index]+[(0x12345678+n*9+k*0x15555)&0xffffffff for k in range(1,16)]
            if op==614:args[1]=(index+7)%16
            if op in (603,604,605,626,627,628):args[1:3]=[f32((-1000.,-990.,-989.,3.5)[n%4]),f32(n*.375-6.25)]
            if op==624:args[1:9]=[f32(n*.25+k*.375) for k in range(1,9)]
            if op in (609,610,611,612):
                if n==31:args[0]=-1;index=0
                append=op in (611,612);wide=op in (610,612);a=1 if append else 2
                if not append:args[1]=n%18
                a+=6 if wide else 4
                for k in range(4 if wide else 2):args[a+k]=f32(n*.25+k*.375)
            before=bytes(m.mem_read(base+0x598,0x39c0)).hex();put(0x4f5834,difficulty)
            put(stack+0x1c,base);put(stack+0x28,code);put(code+4,op)
            m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ESI,code)
            m.emu_start(entry,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
            cases.append(dict(op=op,n=n,difficulty=difficulty,args=[v&0xffffffff for v in args],initial=before,
                result=bytes(m.mem_read(base+0x598,0x39c0)).hex(),reads=reads[:]))
    out=ROOT/'artifacts/th14/enemy-emitter-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(cases)} retail TH14 emitter configuration cases observed.')
if __name__=='__main__':main()
