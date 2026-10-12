"""Execute retail TH16 launch arithmetic, stopping before animation allocation."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x20000)
    manager,bullet,emitter,player,stack=base+0x1000,base+0x2000,base+0x4000,base+0x5000,base+0x1f000
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    for stop in (0x4133fb,0x413100):m.hook_add(UC_HOOK_CODE,lambda *unused:m.emu_stop(),begin=stop,end=stop)
    rows=[]
    for mode in range(14):
        for n in range(72):
            m.mem_write(manager,bytes(0x8000))
            m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
            count=(1,2,3,5,8,13)[n%6];layers=(1,2,3,4,7,12)[n//6%6];index=n%count;layer=(n//3)%layers
            position=[-20.125+n*.5,50.25-n*.125,-7.5];target=[-22.5+n%6,51.5,0]
            angle=(-11.25,-3.1415927410125732,-.3,0.,1.25,7.75)[n%6];spread=(-.7,0.,.3,1.125)[n%4]
            speed=(-1.5,0.,1.25,2.8)[n%4];slow=(0.,.75,2.,-1.125)[n//4%4];radius=(0.,5.,-2.)[n%3];aim=(-1.5,.25,2.75)[n%3];exclusion=(0.,.5,50.,5000.)[n%4];seed=(n*997+mode*123)&65535
            floats(emitter+8,*position,angle,spread,speed,slow,radius);m.mem_write(emitter+0x364,struct.pack('<hhh',count,layers,mode))
            floats(player+0x610,*target);floats(manager+0x44,exclusion);put(manager+0x60,bullet);put(0x4a6dac,manager);put(0x4a6ef8,player);put(0x4a6d88,seed);put(0x4a6d8c,0)
            put(stack,base);put(stack+4,emitter);put(stack+8,index);put(stack+12,layer);floats(stack+16,aim)
            m.reg_write(UC_X86_REG_ECX,manager);m.reg_write(UC_X86_REG_ESP,stack)
            try:m.emu_start(0x412cb0,base,count=100000)
            except Exception as error:raise RuntimeError(f'mode={mode} n={n} pc={m.reg_read(UC_X86_REG_EIP):x}') from error
            pc=m.reg_read(UC_X86_REG_EIP);assert pc in (0x4133fb,0x413100),hex(pc)
            rows.append(dict(mode=mode,n=n,count=count,layers=layers,index=index,layer=layer,position=position,player=target,angle=angle,spread=spread,speed=speed,slow=slow,radius=radius,aim=aim,exclusion=exclusion,seed=seed,accepted=pc==0x4133fb,
                result=[get(bullet+o) for o in (0xc20,0xc24,0xc28,0xc2c,0xc30,0xc38,0xc3c)],rng=[get(0x4a6d88)&65535,get(0x4a6d8c)]))
    out=ROOT/'artifacts/th16/bullet-launch-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} native TH16 bullet launches observed, including rejection and RNG state.')
if __name__=='__main__':main()
