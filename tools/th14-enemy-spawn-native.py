"""TH14 named 2D spawn descriptor; constructor and argument resolution are boundaries."""
import importlib,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,OWNER,CONTEXT,CODE,MANAGER,STACK,RETURN=0x70000000,0x70010000,0x70012000,0x70014000,0x70016000,0x700ff000,0x700fe000
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    output=[];resolutions=[];values=[];refs=0
    def boundary(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==0x48f980:m.mem_write(get(sp+4),bytes([get(sp+8)&255])*get(sp+12))
        elif address==0x4840f0:
            raw=machine.reg_read(UC_X86_REG_XMM1)&0xffffffff;index=int(struct.unpack('<f',struct.pack('<I',raw))[0]//4)-16
            resolutions.append(index+1);machine.reg_write(UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',values[index]))[0])
        elif address==0x420f70:
            index=get(sp+4);resolutions.append(index);machine.reg_write(UC_X86_REG_EAX,(int(values[index-1]) if refs&(1<<index) else get(sp+8))&0xffffffff)
        else:output.extend(struct.unpack('<21I',m.mem_read(get(sp+8),84)))
    for address,cleanup in ((0x48f980,0),(0x4840f0,0),(0x420f70,8),(0x421ef0,8)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    rows=[]
    for op in (300,301,304,305,309,310,311,312,321):
        for flags in (0,0x80000):
            for refs in (0,62):
                for n in range(4):
                    values=[.125+n*13.5,-20.25+n*11.25,100+n,1000+n,-1+n];position=[-99.5+n*32.25,27.75-n*9.5,9]
                    name=b'MapleEnemy\0\0';arguments=struct.pack('<I',len(name))+name
                    arguments+=struct.pack('<ffiii',64,68,72,76,80) if refs else struct.pack('<ffiii',*values)
                    code=struct.pack('<iHHHBBI',0,op,16+len(arguments),refs,255,6,0)+arguments
                    m.mem_write(BASE,bytes(0x5000));m.mem_write(CODE,code);put(BASE+0x4054,flags);put(BASE+0x40ec,OWNER);put(OWNER+4,CONTEXT);put(CONTEXT+4,CODE)
                    put(OWNER+0x11e4,123+n);put(0x4db544,MANAGER);put(MANAGER+0xd8,2);put(MANAGER+0xe4,99999);floats(BASE+0x44,position)
                    inherited=[0x12340000+i*100+n for i in range(12)]
                    for i,v in enumerate(inherited):put(BASE+0x28c+i*4,v)
                    put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,BASE);output.clear();resolutions.clear();m.emu_start(0x42a1e0,RETURN,count=5000)
                    assert m.reg_read(UC_X86_REG_EIP)==RETURN and len(output)==21
                    rows.append(dict(opcode=op,flags=flags,refs=refs,values=values,position=position,inherited=inherited,parent=123+n,code=code.hex(),output=list(output),resolutions=list(resolutions)))
    modes=[]
    # Run both public global getters; the float getter returns in x87 ST0.
    m.mem_write(RETURN,b'\xd9\x1d'+struct.pack('<I',RETURN+0x80))
    for value in (-1,0,1,52,128,16777217,0x7fffffff,-0x80000000):
        put(0x4f5844,value);put(STACK,RETURN);put(STACK+4,-9907);m.reg_write(UC_X86_REG_ECX,OWNER);m.reg_write(UC_X86_REG_ESP,STACK);m.emu_start(0x42a920,RETURN,count=1000)
        integer=m.reg_read(UC_X86_REG_EAX);put(STACK,RETURN);put(STACK+4,-9907);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,OWNER);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(0x42b230,RETURN+6,count=1000);modes.append(dict(value=value,integer=integer,floating=get(RETURN+0x80)))
    out=ROOT/'artifacts/th14/enemy-spawn-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,modes=modes),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native TH14 spawn descriptors and {len(modes)} mode globals observed.')
if __name__=='__main__':main()
