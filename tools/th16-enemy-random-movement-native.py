"""TH14 movement setters and mode-zero timelines from the retail executable."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
COMMAND_ENTRIES={408:0x426a74,410:0x426a74,409:0x426b7f,411:0x426b7f}
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,owner,code,stack,end=0x70001000,0x70007000,0x70008000,0x7000f000,0x70000000;m.mem_map(end,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    fields=(0,4,8,0x34,0x38,0x3c,0x18,0x1c,0x20,0x24,0x28,0x2c,0x40)
    args=[]
    def argument(index):return args[index] if 0<=index<len(args) else args[-1]
    def boundary(machine,address,size,user):
        if address==0x46efa0:m.reg_write(UC_X86_REG_EAX,0)
        else:m.reg_write(UC_X86_REG_EAX if address in (0x473c90,0x4251d0) else UC_X86_REG_XMM0,argument(get(m.reg_read(UC_X86_REG_ESP)+4)))
    for address in (0x473d40,0x473c90,0x46efa0,0x4251d0,0x425200):
        m.mem_write(address,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    f32=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    def initial(n,flags):
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.mem_write(base,bytes(0x8000));put(base+0x44b8,owner);put(owner+0xc,owner+0x100);put(0x490eb0,0x4a5788);put(owner+4,owner+0x100);put(base+0x4060,flags)
        for k,offset in enumerate((0,0x44,0x88,0xcc)):
            values=[-32.125+k*3.25+n*.01,48.5-k*7.5,3.75+k,-.5+k*.25,.625-k*.125,.03125*(k+1),.5+k*.25,-.125+k*.0625,1,2,3,4]
            for field,value in zip(fields,values):floats(base+offset+field,value)
            put(base+offset+0x40,0)
        floats(base+0x3f60,10,100,25,35);floats(base+0x3f58,16,24)
        floats(0x4a5788,1);floats(0x4c140c,.125,-.25,.5)
        put(stack+0x2000-0x438,0x88)
    def state():return [get(base+offset+field) for offset in (0,0x44,0x88,0xcc) for field in fields]+[get(base+0x4060)]
    def interpolation():
        return [[get(base+offset+field) if field!=0x20 else int(bool(get(base+offset+0x24)&1)) for field in (0,4,8,12,0x14,0x18,0x1c,0x20,0x24,0x28,0x2c)] for offset in (0x3c8,0x3f8,0x428,0x458)]
    player=0x70010000;put(0x4a6ef8,player)
    cases=[]
    for op,x,y,seed,mode,duration,px in itertools.product((412,413),(0.,10.,20.),(80.,100.,120.),(0,1,0x9630,0xffff),(0,4,7),(-1,0,30),(-40.,40.)):
        n=len(cases);rate=(.5,1.,1.25)[n%3];speed_mode=(0,1,4,7)[n%4];initial(n,(0,0x20000,0x4000000,0x80000)[n%4])
        for off in (0,0x44,0x88):floats(base+off,x,y,0)
        floats(base+0xcc,0,0,0);floats(base+0x3f60,10,100,25,35);floats(player+0x610,px);floats(0x4a5788,rate)
        put(base+(0x3f8 if op==412 else 0x458)+0x2c,speed_mode)
        put(0x4a6d88,seed);put(0x4a6d8c,0xfffffffc);before=state();args[:]=[duration,mode,f32(3.25)]
        m.reg_write(UC_X86_REG_EBP,stack+0x2000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,base);m.reg_write(UC_X86_REG_ECX,op)
        entry=img.u32(0x422ab8+4*img.read(0x422d70+op-300,1)[0]);m.emu_start(entry,0x422a9b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
        configured=interpolation();configured_state=state();random=[get(0x4a6d88),get(0x4a6d8c)];frames=[]
        for frame in range(8):
            put(base+0x4060,get(base+0x4060)|0x40000);put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,base);m.emu_start(0x41bb50,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
            status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(result=state(),interpolation=interpolation(),status=status));put(base+0x4060,get(base+0x4060)&~0x40000)
            if status:break
        cases.append(dict(op=op,initial=before,args=list(args),seed=seed,calls=0xfffffffc,playerX=px,rate=rate,speedMode=speed_mode,configured=configured,configuredState=configured_state,random=random,frames=frames))
    out=ROOT/'artifacts/th16/enemy-random-movement-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(cases)} own random movement setters / {sum(len(r["frames"]) for r in cases)} frames')
if __name__=='__main__':main()
