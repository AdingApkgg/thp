"""Retail sidebar block and real score/grouping helpers, then real 40bf20.
CRT formatting, queue delivery, atlas binding and GPU calls are boundaries.
"""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,SUP,HUD,FRAME,RESOURCE,ATLAS,REQUEST,STACK,RETURN=0x70000000,0x70010000,0x70040000,0x70044000,0x70046000,0x70047000,0x70050000,0x70070000,0x70080000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x90000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def signed(p):return struct.unpack('<i',m.mem_read(p,4))[0]
    def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
    def string(p):return bytes(m.mem_read(p,256)).split(b'\0')[0].decode('ascii')
    def formatted(fmt,args):
        n=len(re.findall(r'%(?:\d+)?(?:\.\d+)?d',fmt));return fmt%tuple(signed(args+4*i) for i in range(n)) if n else fmt
    queued=[];glyphs=[]
    def record(text,p):queued.append(dict(text=text,position=[flt(p+i*4) for i in range(3)],color=get(SUP+0x191b0),scale=[flt(SUP+0x191b4),flt(SUP+0x191b8)],font=get(SUP+0x191c8),shadow=get(SUP+0x191c4),passIndex=get(SUP+0x191cc),horizontal=get(SUP+0x191d4),vertical=get(SUP+0x191d8)))
    def hook(machine,a,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if a==0x485ddf:
            text=formatted(string(get(sp+8)),sp+12);m.mem_write(get(sp+4),text.encode()+b'\0');m.reg_write(UC_X86_REG_EAX,len(text))
        elif a==0x40bb10:record(formatted(string(get(sp+12)),sp+16),get(sp+8))
        elif a==0x40b9b0:record(string(get(sp+8)),get(sp+4))
        elif a==0x40caf0:put(SUP+0x40,get(sp+4))
        elif a==0x4756e0:glyphs.append(dict(sprite=(get(SUP+0x40)-ATLAS)//72,x=flt(SUP+0x50),y=flt(SUP+0x54),color=get(SUP+0x548),filtered=bool(get(SUP+0x30)&0x400)))
    for a,cleanup in ((0x485ddf,0),(0x40bb10,0),(0x40b9b0,8),(0x4854a0,0),(0x40caf0,4),(0x476100,20),(0x4756e0,8)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.hook_add(UC_HOOK_CODE,lambda *args:m.emu_stop(),begin=0x4318b6,end=0x4318b6)
    rows=[];bounds=(0,99,100,99999,100000,99999999,100000000,999999999)
    for i,(high,current,alpha,awards) in enumerate(itertools.product(bounds,bounds,(0,80,255),(0,48,49))):
        power=(0,20,40,159,160)[i%5];continuations=i%10;life=i%3;bombs=i%8;points=(10000,5000000,123456789)[i%3];graze=(0,999,1000,999999,1000000,99999999)[i%6]
        m.mem_write(BASE,bytes(0x90000));queued.clear();glyphs.clear()
        put(0x4db520,SUP);put(HUD+0x58,FRAME);m.mem_write(FRAME+0x537,bytes([alpha]));put(HUD+0x140,current)
        for a,v in ((0x4f5898,high),(0x4f589c,8),(0x4f5838,continuations),(0x4f586c,awards),(0x4f5868,life),(0x4f5874,bombs),(0x4f5858,power),(0x4f585c,160),(0x4f5860,40),(0x4f584c,points),(0x4f5840,graze)):put(a,v)
        m.mem_write(SUP+0x191b4,struct.pack('<2f',1,1));put(SUP+0x191d4,1);put(SUP+0x191d8,1)
        m.reg_write(UC_X86_REG_ESI,SUP);m.reg_write(UC_X86_REG_EBX,HUD);m.reg_write(UC_X86_REG_EBP,STACK+0x4000);m.reg_write(UC_X86_REG_ESP,STACK);put(STACK+0x4000-4,0)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(0x43144a,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x4318b6
        assert len(queued)==(10 if awards==49 else 12)
        for q in queued[:]:
            m.mem_write(REQUEST,bytes(0x138));m.mem_write(REQUEST,q['text'].encode()+b'\0');m.mem_write(REQUEST+0x100,struct.pack('<3fI2f',*q['position'],q['color'],*q['scale']))
            for off,v in ((0x120,q['font']),(0x124,q['shadow']),(0x128,q['passIndex']),(0x130,q['horizontal']),(0x134,q['vertical'])):put(REQUEST+off,v)
            put(SUP+0x191e4,RESOURCE);put(RESOURCE+0x11c,ATLAS);put(SUP+0x191dc,9);put(0x4f56cc,BASE+0x60000);m.mem_write(0x4f7a6c,struct.pack('<f',1))
            put(STACK,RETURN);put(STACK+4,REQUEST);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP);m.emu_start(0x40bf20,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        rows.append(dict(high=high,displayed=current,alpha=alpha,power=power,continues=continuations,lifeFragments=life,bombFragments=bombs,pointValue=points,graze=graze,lifeAwards=awards,requests=queued[:],glyphs=glyphs[:]))
    out=ROOT/'artifacts/th14/hud-text-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} native HUD sidebar cases, {sum(len(r["glyphs"]) for r in rows)} glyphs.')
if __name__=='__main__':main()
