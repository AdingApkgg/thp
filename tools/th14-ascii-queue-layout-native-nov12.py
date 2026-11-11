"""Observe retail TH14 40bf20; sprite binding and GPU calls are controlled.

Executes original queue40b9b0 then traversal40bf20 across display sizes, passes and alignments. Atlas entries
are synthetic and identify requested glyphs without substituting the layout.
"""
import importlib, hashlib, json, struct, itertools
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
SUP,REQUEST,RESOURCE,ATLAS,STACK,RETURN=0x70000000,0x70020000,0x70021000,0x70022000,0x7003f000,0x70040000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        begin=base&~4095;m.mem_map(begin,((base+size+4095)&~4095)-begin);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(SUP,0x41000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
    glyphs=[]
    def observe(machine,address,size,user):
        if address==0x40caf0:put(SUP+0x40,get(m.reg_read(UC_X86_REG_ESP)+4))
        elif address==0x4756e0:
            glyphs.append(dict(sprite=(get(SUP+0x40)-ATLAS)//72,x=flt(SUP+0x50),y=flt(SUP+0x54),z=flt(SUP+0x58),color=get(SUP+0x548),filtered=bool(get(SUP+0x30)&0x400)))
    for a,cleanup in ((0x40caf0,4),(0x476100,20),(0x4756e0,8)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,observe,begin=a,end=a)
    cases=[]
    texts=['0123456789 /:.-*%$+s,','Abcz Z\n1. 2,3 s.4']
    for width,font,(sx,sy),shadow,text,pass_index,(horizontal,vertical) in itertools.product([480,640,800,801,960,1280],range(6),[(1.,1.),(1.5,.75),(.7,.3)],(False,True),texts,[0,1,2],[(1,1),(0,0),(2,2),(0,2),(2,0)]):
        m.mem_write(SUP,bytes(0x191f4));m.mem_write(REQUEST,bytes(0x138));m.mem_write(REQUEST,text.encode('ascii')+b'\0')
        m.mem_write(REQUEST+0x100,struct.pack('<3fI2f',16.25,28.5,-.125,0xa5345678,sx,sy))
        for off,v in ((0x120,font),(0x124,int(shadow)),(0x130,1),(0x134,1)):put(REQUEST+off,v)
        put(SUP+0x191e4,RESOURCE);put(RESOURCE+0x11c,ATLAS);put(SUP+0x191dc,9)
        m.mem_write(0x4f7a6c,struct.pack('<f',width/640.));put(0x4f56cc,SUP+0x38000)
        for off,v in [(0x191b0,0xa5345678),(0x191c8,font),(0x191c4,int(shadow)),(0x191cc,pass_index),(0x191d4,horizontal),(0x191d8,vertical)]:put(SUP+off,v)
        m.mem_write(SUP+0x191b4,struct.pack('<2f',sx,sy));put(0x4f7a80,width//2);put(0x4f7a84,int(width/640.*16))
        m.mem_write(STACK,struct.pack('<3I',RETURN,REQUEST+0x100,REQUEST));m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP)
        m.emu_start(0x40b9b0,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN and get(SUP+0x191ac)==1
        queued_position=[flt(SUP+0xbac+0x100+i*4)for i in range(3)]
        m.mem_write(STACK,struct.pack('<2I',RETURN,SUP+0xbac));m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        glyphs.clear();m.emu_start(0x40bf20,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        cases.append(dict(width=width,font=font,passIndex=pass_index,horizontal=horizontal,vertical=vertical,queuedPosition=queued_position,scale=[sx,sy],shadow=shadow,text=text,glyphs=glyphs[:]))
    out=ROOT/'artifacts/th14/ascii-queue-layout-nov12/native.json';assert not out.exists();out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases,original40bf20Executed=True,geometryAndGpuDeclaredServices=True,syntheticSpriteAtlas=True,leftTopAlignmentOnly=False,original40b9b0Executed=True,queueAndTraversalSameDisplayScaleDeclared=True,pass1OriginsDerivedFromNativeReset=True,noPixels=True,newGameRuns=0,completeGame=False),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(cases)} native TH14 layouts; {sum(len(c["glyphs"]) for c in cases)} glyph submissions.')
if __name__=='__main__':main()
