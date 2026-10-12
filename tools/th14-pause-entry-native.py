"""Retail pause entry bindings and overlay factory; controlled ANM templates.

Executes 448d80 and 449d30 with audio/capture delivery as boundaries, then
executes the actual 44c1a0 overlay factory and ANM interpreter. GPU capture,
score records and menu input transitions are outside this proof.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,MENU,GAME,CONTROL,TEXT,FRONT,VM,CODE,STACK=tuple(0x70000000+n for n in (0,0x1000,0x5000,0x6000,0x7000,0x8000,0x9000,0xa000,0x1f000))

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x50000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    events=[];sounds=[];factory=False
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x46e3d0:sounds.append(get(sp+4))
        elif address==0x46e5e0:m.reg_write(UC_X86_REG_EAX,0)
        elif address==0x448bf0:events.append(['text',52])
        elif address==0x44c1a0 and not factory:
            out=get(sp+4);events.append(['text' if m.reg_read(UC_X86_REG_ECX)==TEXT else 'front',get(sp+8)]);put(out,100);m.reg_write(UC_X86_REG_EAX,out)
        elif address==0x47fcb0:m.reg_write(UC_X86_REG_EAX,VM)
        elif address==0x40af00:
            assert get(sp+4)==VM;put(VM+0x18,7);put(VM+0x1c,0x806000)
            put(VM+0x28,CODE);put(VM+0x38,CODE);put(VM+0x30,m.reg_read(UC_X86_REG_ECX))
            put(VM+0x554,0x4d8f58);put(VM+0x558,1);put(VM+0x580,VM)
            floats(VM+0x60,1,1,1,1);floats(VM+0x4e0,1,3.1415927410125732);put(VM+0x4e8,65536)
        elif address==0x47e9f0:
            out=get(sp+4);put(out,100);m.reg_write(UC_X86_REG_EAX,out)
    entry_hooks=((0x436ea0,0),(0x4373b0,0),(0x46e3d0,8),(0x46ef90,12),(0x46e5e0,0),(0x448bf0,0),(0x47f140,8),(0x433ba0,0),(0x44beb0,0),(0x445690,8))
    for address,cleanup in (*entry_hooks,(0x47fcb0,0),(0x40af00,8),(0x47e9f0,8)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    original=m.mem_read(0x44c1a0,3);m.mem_write(0x44c1a0,b'\xc2\x0c\x00');m.hook_add(UC_HOOK_CODE,boundary,begin=0x44c1a0,end=0x44c1a0)
    def reset():
        m.mem_write(BASE,bytes(0x1e000));events.clear();sounds.clear()
        for p,v in ((0x4db678,MENU),(0x4db550,GAME),(0x4db558,CONTROL),(0x4d967c,TEXT),(GAME+0x2a4,FRONT),(0x4f58b8,0),(0x4db68c,BASE+0x20000)):
            put(p,v)
        floats(0x4d8f58,1);m.mem_write(0x4f5815,b'\0');put(STACK,BASE)
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MENU)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    entries=[]
    for replay in (0,1):
        reset();put(CONTROL+0x94,replay);m.emu_start(0x448d80,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE
        entries.append(dict(kind='pause',replay=replay,bindings=events[:],sounds=sounds[:]))
    reset();m.emu_start(0x449d30,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE
    entries.append(dict(kind='game_over',replay=0,bindings=events[:],sounds=sounds[:]))
    # Verify that capture selects 52 by executing its actual prefix as well.
    reset();m.mem_write(0x448bf0,bytes.fromhex('55 8b ec'));m.ctl_remove_cache(0x448bf0,0x448d80);m.emu_start(0x448bf0,0x448c1c,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==0x448c1c
    assert events==[['text',52],['text',52]],events
    factory=True;m.mem_write(0x44c1a0,bytes(original));m.ctl_remove_cache(0x44c1a0,0x44c258);rows=[]
    def command(op,*args):return struct.pack('<hHhH',op,8+len(args)*4,0,0)+b''.join(struct.pack('<I',v) for v in args)
    f32=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
    for script in (52,129,130):
        for program in (0,1,2):
            reset();m.reg_write(UC_X86_REG_ECX,TEXT if script==52 else FRONT)
            code=command(304,35 if script==52 else 28)
            if program:code+=command(400,*map(f32,(3.25,-7.5,9.125)))
            if program==2:code+=command(305,1)
            m.mem_write(CODE,code+command(2)+command(-1));put(STACK+4,BASE+0x18000);put(STACK+8,script);put(STACK+12,0)
            m.emu_start(0x44c1a0,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==BASE
            rows.append(dict(script=script,program=program,vm=[get(VM+0x24),get(VM+0x1c)&0x66220,*[get(VM+p) for p in (0x59c,0x5a0,0x5a4,0x3c,0x40,0x44,0x50)]]))
    out=ROOT/'artifacts/th14/pause-entry-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),entries=entries,factories=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(entries)} pause/end entry paths and {len(rows)} native overlay factory cases.')
if __name__=='__main__':main()
