"""Execute retail TH14 42bf70 health/timeout selection with memory-backed globals."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    end,entity,game,spell,special,manager,stack=0x70000000,0x70001000,0x70008000,0x70009000,0x7000a000,0x7000b000,0x7000f000
    m.mem_map(end,0x10000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
    rows=[]
    for slot in range(8):
     for variant in range(6):
      for boss in range(2):
       for sf in (0,1,9,0x23,0x80,0xff):
        for active in (0,1,2):
         for spell_time in (59,60):
          m.mem_write(entity,bytes(0xd000))
          flags=0x1000000|(boss*0x800000);elapsed=(0,40,59,60,10000,60)[variant]
          timer_flags=slot%2;rate=0x4d8f58 if timer_flags else 0
          put(0x4db550,game);put(0x4db534,spell);put(0x4db52c,special);put(0x4db544,manager)
          put(entity+0x5164,200);put(entity+0x5244,flags)
          for n in range(8):
            p=entity+0x525c+16*n;put(p,-1);put(p+4,-1);put(p+8,0x100+n);put(p+12,0x200+n)
          p=entity+0x525c+slot*16
          if variant:put(p,200 if variant==1 else 100);put(p+4,60 if variant!=4 else 20000)
          if variant==5 and slot<7:put(p+16,200);put(p+20,1)
          for offset,value in ((0x14ac,elapsed-1),(0x14b0,elapsed),(0x14b4,bits(float(elapsed))),(0x14b8,rate),(0x14bc,timer_flags)):
            put(entity+offset,value)
          put(game+0x19c,777);put(game+0x1a0,888);put(spell+0x7c,sf);put(spell+0x28,spell_time);put(spell+0x80,999)
          put(special+0x40,active);put(manager+0x18,123)
          interrupts=[get(entity+0x525c+4*n) for n in range(32)]
          inputs=[200,elapsed,flags,sf,spell_time,active,timer_flags]+interrupts
          put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,entity)
          m.emu_start(0x42bf70,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
          result=[m.reg_read(UC_X86_REG_EAX),get(entity+0x5164),get(entity+0x516c),get(entity+0x5174),get(entity+0x5244),
                  *[get(entity+off) if off!=0x14b8 else int(get(entity+off)!=0) for off in range(0x14ac,0x14c0,4)],
                  get(game+0x19c),get(game+0x1a0),get(spell+0x7c),get(spell+0x80),get(manager+0x18),
                  *[get(entity+0x525c+16*n) for n in range(8)]]
          rows.append(dict(inputs=inputs,result=result))
    out=ROOT/'artifacts/th14/enemy-phase-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows))+'\n',encoding='utf8')
    print(f'{len(rows)} retail health/timeout phase cases')
if __name__=='__main__':main()
