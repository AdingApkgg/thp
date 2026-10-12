"""Retail deformation grid and per-frame calculation, D3DX normalization boundary."""
import hashlib,importlib,json,math,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x50000);enemy,effect,vertices,positions,stack=tuple(base+n for n in (0x1000,0x7000,0x10000,0x18000,0x4f000))
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));real=lambda p,n:list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
    def normalize(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);out,p=get(sp+4),get(sp+8);x,y,z=real(p,3);sq=f32(x*x+y*y+z*z)
        if abs(f32(sq-1))<=2**-23:v=(x,y,z)
        elif sq<=2**-126:v=(0,0,0)
        else:
            inv=f32(1/f32(math.sqrt(sq)));v=tuple(f32(c*inv) for c in (x,y,z))
        floats(out,*v);m.reg_write(UC_X86_REG_EAX,out)
    m.mem_write(base+0x49000,b'\xc2\x08\x00');put(0x4b12b8,base+0x49000);m.hook_add(UC_HOOK_CODE,normalize,begin=base+0x49000,end=base+0x49000)
    m.mem_write(0x4854a0,b'\xc3')
    def call(entry):
        put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(entry,base,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==base
    rows=[]
    for position in ((0,100,0),(-190,0,0),(185,440,0),(24.25,230.5,9)):
        for radius in (16,32,128):
            for rate in (.5,1,1.25):
                m.mem_write(enemy,bytes(0x8000));put(enemy+0x40f0,effect);put(effect,17);put(effect+4,17);put(effect+0x10,vertices);put(effect+0x14,positions);put(effect+0xc,base+0x8000)
                for j in range(16):p=base+0x20000+j*0x1000;put(base+0x8000+j*4,p);put(p+0x5b4,p+0x800)
                for p,v in ((0x4f7a64,640),(0x4f7a68,480),(0x4f7a70,128),(0x4f7a88,320),(0x4f7a8c,16)):put(p,v)
                floats(0x4d8f58,rate);floats(enemy+0x44,*position);floats(enemy+0x40f4,128,radius);put(enemy+0x40fc,0x008f8fff);floats(enemy+0x4100,.25,-.5)
                frames=[]
                for n in range(3):
                    call(0x424100)
                    result=[dict(position=real(vertices+j*28,3),w=real(vertices+j*28+12,1)[0],color=get(vertices+j*28+16),uv=real(vertices+j*28+20,2),source=real(positions+j*12,3)) for j in range(289)]
                    frames.append(dict(radius=real(enemy+0x40f8,1)[0],phase=real(enemy+0x4100,2),vertices=result))
                rows.append(dict(position=position,radius=radius,rate=rate,frames=frames))
    out=ROOT/'artifacts/th14/deformation-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=1)+'\n',encoding='utf-8');print(f'{len(rows)} deformation timelines / {len(rows)*3*289} vertices.')
if __name__=='__main__':main()
