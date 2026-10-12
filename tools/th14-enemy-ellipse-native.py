"""Execute retail 421/423 and complete 4230d0 movement with radius and dormant ellipse bands."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,owner,code,stack,end=0x70001000,0x70007000,0x70008000,0x7000f000,0x70000000;m.mem_map(end,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40);args=[]
    def boundary(machine,address,size,user):
        if address==0x47f0a0:m.reg_write(UC_X86_REG_EAX,0)
        else:
            index=get(m.reg_read(UC_X86_REG_ESP)+4)
            m.reg_write(UC_X86_REG_EAX if address in (0x483f30,0x42c1d0) else UC_X86_REG_XMM0,args[index])
    for address in (0x483fc0,0x483f30,0x47f0a0,0x42c1d0,0x42c230):
        m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def state():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4054)]
    def scalar():return [[get(base+offset+f) if f!=0x20 else int(get(base+offset+f)!=0) for f in (0,4,8,12,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)] for offset in (0x3c8,0x3f8,0x428,0x458)]
    def radius():return [[get(base+offset+f) if f!=0x34 else int(get(base+offset+f)!=0) for f in (0,4,8,12,16,20,24,28,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40)] for offset in (0x488,0x4cc)]
    def ellipse():return [[get(base+offset+f) if f!=0x34 else int(get(base+offset+f)!=0) for f in (0,4,8,12,16,20,24,28,0x28,0x2c,0x30,0x34,0x38,0x3c,0x40)] for offset in (0x510,0x554)]
    rows=[]
    for op in (421,423):
      for mode in (*range(32),-1,80):
       for variant in range(6):
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.mem_write(base,bytes(0x8000));put(base+0x40ec,owner);put(owner+4,owner+0x100)
        put(base+0x4054,(0,0x80000,0x20000,0xa0000,0x4000000,0)[variant])
        for k,offset in enumerate((0,0x44,0x88,0xcc)):
            values=[-32.125+k*3.25,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),.5+k*.25,-.125+k*.0625,1,2,3,4]
            for field,value in zip(fields,values):floats(base+offset+field,value)
            put(base+offset+0x40,(0,1,2,3,7,2)[variant] if offset==(0x88 if op==421 else 0xcc) else 0)
        floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24);floats(0x4d9294,.125,-.25,.5)
        rate=(.5,1.,1.25)[variant%3];floats(0x4d8f58,rate);before=state()
        args[:]=[(0,-1,1,7,35,80)[variant]&0xffffffff,mode&0xffffffff,
                 f32((-999999.,-1000000.,-.25,0.,1.5,.017453292)[variant]),
                 f32((-999999.,-1000000.,0.,3.25,-2.75,16.)[variant]),
                 f32((-999999.,-1000000.,0.,-.125,2.5,0.)[variant]),
                 f32((-999999.,-1000000.,0.,.0625,-.125,.25)[variant]),
                 f32((-999999.,-1000000.,1.,.5,2.,-.5)[variant])]
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_EDX,owner)
        m.reg_write(UC_X86_REG_ECX,op);m.reg_write(UC_X86_REG_ESI,code);put(code+4,op)
        m.emu_start(0x426eee,0x429c28,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        configured=dict(result=state(),scalar=scalar(),radius=radius(),ellipse=ellipse());frames=[]
        for frame in range(85):
            put(base+0x4054,get(base+0x4054)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base)
            m.emu_start(0x4230d0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),scalar=scalar(),radius=radius(),ellipse=ellipse(),status=status))
            put(base+0x4054,get(base+0x4054)&~0x40000)
            if status:break
        rows.append(dict(op=op,mode=mode,variant=variant,rate=rate,initial=before,args=args[:],configured=configured,frames=frames))
    output=ROOT/'artifacts/th14/enemy-ellipse-native.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows)),encoding='utf-8')
    print(f'native ellipse: {len(rows)} timelines / {sum(len(r["frames"]) for r in rows)} frames')
if __name__=='__main__':main()
