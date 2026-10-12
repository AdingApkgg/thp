"""Retail 41b2f0 circle and 41ac70 cancellation, delivery sinks only."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for opcode in (613,):
        group=img.data[next(raw+0x429ef4-base+opcode-300 for _,base,size,raw,n in img.sections if base<=0x429ef4<base+size)]
        assert img.u32(0x429c50+group*4)==0x4287ba
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0xa20000);manager,bullet,node,center,stack=tuple(base+n for n in (0,0x9d0000,0x9d5000,0x9d6000,0xa1f000))
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));bits=lambda f:struct.unpack('<I',struct.pack('<f',f))[0]
    reward_entry=bytes(m.mem_read(0x41ae00,1))
    events=[]
    def hook(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x47ed10:
            p=get(sp+12);events.append([0,get(sp+8),get(p),get(p+4),get(p+8),get(sp+16),get(sp+20)])
            put(get(sp+4),1);m.reg_write(UC_X86_REG_EAX,get(sp+4))
        elif address==0x41ae00:
            p=m.reg_read(UC_X86_REG_ECX)
            if m.reg_read(UC_X86_REG_EDX):events.append([2,m.reg_read(UC_X86_REG_EDX),get(p),get(p+4),get(p+8)])
        else:events.append([1,get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
    for address,cleanup in ((0x47ed10,28),(0x46e470,4),(0x41ae00,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    rows=[]
    for reward in (0,1):
      for state in (0,1,2,3,4):
          for flags in (0,0x10,0x200,0x210):
              for rate in (.5,1,1.25):
                  for position in ((0,0),(14,0),(14.00001,0),(0,14),(10,10),(-9,-9)):
                      events.clear();m.mem_write(bullet,bytes(0x3000));put(0x4db530,manager);put(manager+0x80,node);put(node,bullet);put(node+4,0)
                      put(bullet+0x20,flags);floats(bullet+0xbc0,*position,2);floats(bullet+0xbcc,1.25,-.75,.5);floats(bullet+0xbe0,8,8)
                      m.mem_write(bullet+0xc0e,struct.pack('<h',state));put(bullet+0xc00,6);put(bullet+0x13d0,1);put(bullet+0x13cc,0x4d8f58)
                      put(bullet+0x13c0,19);put(bullet+0x13c4,20);floats(bullet+0x13c8,20.5);floats(center,0,0,0);floats(0x4d8f58,rate)
                      put(stack,base+0xa10000);put(stack+4,center);put(stack+8,reward);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,bits(10))
                      m.emu_start(0x41b2f0,base+0xa10000,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base+0xa10000
                      offsets=(0x20,0xbc0,0xbc4,0xbc8,0x13c0,0x13c4,0x13c8,0x4c8)
                      rows.append(dict(reward=reward,state=state,flags=flags,rate=rate,position=position,result=[*[get(bullet+p) for p in offsets],int.from_bytes(m.mem_read(bullet+0xc0e,2),'little')],events=events[:]))
    delayed_rows=[]
    for delay in (0,1,30):
      for state in (0,1,2,3,4):
       for flags in (0,0x200):
        for rate in (.5,1,1.25):
         for position in ((0,0),(14,0),(14.00001,0),(0,14),(10,10),(-9,-9),(-0.0,0),(float('nan'),0),(float('inf'),0)):
          events.clear();m.mem_write(bullet,bytes(0x3000));put(0x4db530,manager);put(manager+0x80,node);put(node,bullet);put(node+4,0)
          put(bullet+0x20,flags);put(bullet+0x24,delay);floats(bullet+0xbc0,*position,2);floats(bullet+0xbcc,1.25,-.75,.5);floats(bullet+0xbe0,8,8)
          m.mem_write(bullet+0xc0e,struct.pack('<h',state));put(bullet+0xc00,6);put(bullet+0x13d0,1);put(bullet+0x13cc,0x4d8f58)
          put(bullet+0x13c0,19);put(bullet+0x13c4,20);floats(bullet+0x13c8,20.5);floats(center,0,0,0);floats(0x4d8f58,rate)
          put(stack,base+0xa10000);put(stack+4,center);put(stack+8,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM2,bits(10))
          m.emu_start(0x41b3f0,base+0xa10000,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base+0xa10000
          offsets=(0x20,0xbc0,0xbc4,0xbc8,0x13c0,0x13c4,0x13c8,0x4c8)
          delayed_rows.append(dict(delay=delay,state=state,flags=flags,rate=rate,positionBits=[bits(f) for f in position],result=[*[get(bullet+p) for p in offsets],int.from_bytes(m.mem_read(bullet+0xc0e,2),'little')],events=events[:]))
    m.mem_write(0x41ae00,reward_entry);m.ctl_remove_cache(0x41ae00,0x41ae01)
    all_rows=[]
    for slot in (0,1999):
      for state in (0,1,2,3,4):
        for flags in (0,0x10,0x200,0x210):
          for rate in (.5,1,1.25):
            events.clear();m.mem_write(manager,bytes(0x9bf700));put(0x4db530,manager)
            b=manager+0x8c+slot*0x13f4;position=(12.25,-9.5)
            put(b+0x20,flags);floats(b+0xbc0,*position,2);floats(b+0xbcc,1.25,-.75,.5)
            m.mem_write(b+0xc0e,struct.pack('<h',state));put(b+0xc00,6);put(b+0x13d0,1);put(b+0x13cc,0x4d8f58)
            put(b+0x13c0,19);put(b+0x13c4,20);floats(b+0x13c8,20.5);floats(0x4d8f58,rate)
            put(stack,base+0xa10000);put(stack+4,0);m.reg_write(UC_X86_REG_ESP,stack)
            m.emu_start(0x41b880,base+0xa10000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base+0xa10000
            all_rows.append(dict(slot=slot,state=state,flags=flags,rate=rate,position=position,result=[*[get(b+p) for p in offsets],int.from_bytes(m.mem_read(b+0xc0e,2),'little')],events=events[:]))
    etex_rows=[]
    for state in (1,2,3,4):
     for flags in (0,0x10,0x200,0x210):
      for parameter in (-1,0,1,2):
       for index in (0,1):
        for active in (0,4,0x100):
         for concurrent in (0,1):
          for rate in (.5,1.,1.25):
           events.clear();m.mem_write(bullet,bytes(0x2000));put(0x4db530,manager);put(bullet+0x20,flags);floats(bullet+0xbc0,12.25,-9.5,2.);floats(bullet+0xbcc,1.25,-.75,.5);m.mem_write(bullet+0xc0e,struct.pack('<h',state));put(bullet+0xc00,6);put(bullet+0xc20,index);put(bullet+0xc04,active)
           put(bullet+0x13d0,1);put(bullet+0x13cc,0x4d8f58);put(bullet+0x13c0,19);put(bullet+0x13c4,20);floats(bullet+0x13c8,20.5);floats(0x4d8f58,rate)
           t=bullet+0xc28+index*0x2c;put(t+0x10,parameter);put(t+0x20,0x400);put(t+0x24,concurrent);put(stack,base+0xa10000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullet)
           m.emu_start(0x418140,base+0xa10000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base+0xa10000
           etex_rows.append(dict(state=state,flags=flags,parameter=parameter,index=index,active=active,concurrent=concurrent,rate=rate,result=[*[get(bullet+p) for p in offsets],int.from_bytes(m.mem_read(bullet+0xc0e,2),'little'),get(bullet+0xc00),get(bullet+0xc20),get(bullet+0xc04)],events=events[:]))
    timer_rows=[];argument_value=0
    def timer_argument(machine,a,size,user):m.reg_write(UC_X86_REG_EAX,argument_value&0xffffffff)
    m.mem_write(0x42c1d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,timer_argument,begin=0x42c1d0,end=0x42c1d0)
    for argument_value in (-2147483648,-1,0,60,2147483647):
      for flags in (0,1,2,3,0xa5a5a5a5,0xffffffff):
       for pointer in (0,base+0xa00000):
        owner=base+0x9d0000;timer=owner+0x3fec;m.mem_write(owner,bytes(0x5000));put(timer,0xfffffff0);put(timer+4,19);floats(timer+8,21.25);put(timer+12,pointer);put(timer+16,flags)
        m.reg_write(UC_X86_REG_EDI,owner);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x4278e5,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        timer_rows.append(dict(value=argument_value,flags=flags,pointer=int(bool(pointer)),result=[get(timer),get(timer+4),get(timer+8),0 if not get(timer+12) else 1 if get(timer+12)==base+0xa00000 else 2,get(timer+16)]))
    out=ROOT/'artifacts/th14/bullet-cancel-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,delayedCases=delayed_rows,allCases=all_rows,timerCases=timer_rows,etexCases=etex_rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} circle and {len(all_rows)} all-pool cancellation cases; {len(timer_rows)} ECL 515 timer setters; {len(etex_rows)} ETEX 400 dispatch/cancel cases.')
if __name__=='__main__':main()
