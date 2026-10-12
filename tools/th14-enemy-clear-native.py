"""Execute retail 525, zero-drop death delivery and post-spawn metadata."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base,manager,stack=0x70000000,0x70020000,0x7003f000;m.mem_map(base,0x40000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    words=lambda p,n:list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
    sounds=[];effects=[]
    def hook(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x48f980:
            p,v,n=(get(sp+x) for x in (4,8,12));m.mem_write(p,bytes([v&255])*n);m.reg_write(UC_X86_REG_EAX,p)
        elif address==0x46e470:sounds.append([get(sp+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
        elif address==0x47ed10:
            effects.append([get(sp+8),*words(get(sp+12),3),get(sp+16),get(sp+20),get(sp+24),m.reg_read(UC_X86_REG_ECX)])
            put(get(sp+4),len(effects));m.reg_write(UC_X86_REG_EAX,get(sp+4))
    for address,cleanup in ((0x48f980,0),(0x46e470,4),(0x47ed10,28)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    def reset():
        m.mem_write(base,bytes(0x3e000));sounds.clear();effects.clear();put(stack,base)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    metadata=[]
    for file in (-1,0,1,2,3):
        for script in (-1,*range(94)):
            for override in (0,-1,19):
                reset();put(base+0x11e4,script&1);put(base+0x1458,file);put(base+0x145c,script);put(base+0x51c8,override);put(base+0x51cc,7)
                m.reg_write(UC_X86_REG_ESI,base);m.emu_start(0x4220d0,0x422181,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422181
                metadata.append(dict(file=file,script=script,override=override,id=script&1,result=words(base+0x51c4,3)))
    cases=[];flags=[0,0x20,0x80,0x400,0x40000,0x400000,0x800000,0x80000,0xc004a0,0xc005a0,0xffffffff,0x100]
    for n,flag in enumerate(flags):
        for rate in (.5,1,1.25):
            for variant in range(4):
                reset();put(0x4db544,manager);put(manager+0xa4,0x77770008);put(manager+0xd0,base+0x14d8)
                put(manager+0xb8,9);put(manager+0xbc,10);floats(manager+0xc0,10.5);put(manager+0xc4,0x4d8f58);floats(0x4d8f58,rate)
                put(0x4db510,12345);put(0x4db514,0)
                inputs=[]
                for j in range(3):
                    e=base+j*0x6000;f=flag if j==0 else flags[(n+j*3)%len(flags)];p=[(0.,0.),(10.,0.),(0.,10.),(4.,-9.)][(variant+j)%4]
                    put(e+0x14d8,e);put(e+0x14dc,e+0x6000+0x14d8 if j<2 else 0);put(e+0x5244,f)
                    floats(e+0x1234,*p,0);floats(e+0x1470,0,0);put(e+0x51c4,j+3);put(e+0x51c8,43);put(e+0x51cc,1)
                    for k in range(16):put(e+0x5180+k*4,1000+j*100+k)
                    inputs.append(dict(flags=f,position=p))
                m.emu_start(0x424cb0,base,count=50000);assert m.reg_read(UC_X86_REG_EIP)==base
                cases.append(dict(rate=rate,inputs=inputs,result=[[get(base+j*0x6000+0x5244),*words(base+j*0x6000+0x5180,16)] for j in range(3)],timer=words(manager+0xb8,3),sounds=sounds[:],effects=effects[:],rng=[get(0x4db510)&65535,get(0x4db514)]))
    sound_cases=[];sound_id=0
    def sound_argument(machine,address,size,user):
        assert get(m.reg_read(UC_X86_REG_ESP)+4)==0;m.reg_write(UC_X86_REG_EAX,sound_id)
    m.mem_write(0x42c1d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sound_argument,begin=0x42c1d0,end=0x42c1d0)
    for sound_id in (0,3,14,54,71,75):
      for x in (-192.,-.125,0.,12.25,192.):
        reset();floats(base+0x44,x);m.reg_write(UC_X86_REG_EDI,base)
        m.emu_start(0x4287ce,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        sound_cases.append(dict(id=sound_id,x=x,result=sounds[:]))
    inactive_spells=[]
    for health_flags in (0,1,2,3,0xa5a5a5a5,0xffffffff):
      for spell_flags in (0,2,8,0x80,0xfe):
        reset();put(0x4db534,manager);put(manager+0x7c,spell_flags);put(base+0x3f8c,health_flags);m.reg_write(UC_X86_REG_EDI,base)
        m.emu_start(0x4289ea,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
        inactive_spells.append(dict(healthFlags=health_flags,spellFlags=spell_flags,result=[get(base+0x3f8c),get(manager+0x7c)]))
    reset();put(0x4db664,manager);before=bytes(m.mem_read(manager,0x600))
    m.emu_start(0x429722,0x429c28,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28 and bytes(m.mem_read(manager,0x600))==before
    out=ROOT/'artifacts/th14/enemy-clear-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),emptyLaser545=True,inactiveSpells=inactive_spells,sounds=sound_cases,metadata=metadata,cases=cases),indent=2)+'\n',encoding='utf-8')
    print(f'{len(metadata)} spawn metadata cases, {len(cases)} three-enemy clearing cases.')
if __name__=='__main__':main()
