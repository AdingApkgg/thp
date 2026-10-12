"""Retail end-choice initialization and input, with ANM/audio/score I/O boundaries.

Executes original 44a3ee and 44a488 blocks. Native cursor methods run unchanged;
the overlay factory, handle lookup, interrupt delivery, audio and replay/score
I/O are controlled. This does not verify the help manager or exit destinations.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,MENU,FRONT,STACK=0x70000000,0x70001000,0x70004000,0x70010000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<i',m.mem_read(p,4))[0]
    events=[];sounds=[];scripts=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x44c1a0:
            scripts.append(get(sp+8));out=get(sp+4);put(out,100);m.reg_write(UC_X86_REG_EAX,out)
        elif address==0x47fb30:
            out=get(sp+4);scripts.append(get(sp+8));put(out,200);m.reg_write(UC_X86_REG_EAX,out)
        elif address==0x47f140:events.append([get(sp+4),get(sp+8)])
        elif address==0x46e3d0:sounds.append(get(sp+4))
    for address,cleanup in ((0x44c1a0,12),(0x47fb30,12),(0x47f140,8),(0x46e3d0,8),(0x447da0,0),(0x47f560,0),(0x44bef0,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def stop(machine,address,size,user):m.emu_stop()
    for p in (0x44a476,0x44b004):m.hook_add(UC_HOOK_CODE,stop,begin=p,end=p)
    def snapshot():
        count=get(MENU+0x10c)
        return dict(selected=get(MENU+0x38),previous=get(MENU+0x3c),count=get(MENU+0x40),wrap=get(MENU+0x108),
                    disabled=[get(MENU+0xc8+i*4) for i in range(count)],events=events[:],sounds=sounds[:],scripts=scripts[:],state=get(MENU+4))
    rows=[]
    for difficulty,limit in enumerate([3,3,4,5,0]):
        for continues in (0,1,limit,limit+1):
            for selected in range(-1,5):
                for pressed,repeat in ((0,0),(16,0),(32,0),(0,16),(0,32),(0x102,0),(1,0)):
                    # The help dispatch and replay I/O need additional fixtures.
                    if pressed==1 and selected in (2,3):continue
                    m.mem_write(BASE,bytes(0x20000));events.clear();sounds.clear();scripts.clear()
                    put(MENU+0x3e4,FRONT);put(0x4f5838,continues);put(0x4f58c8,limit-continues)
                    m.mem_write(0x4d8f58,struct.pack('<f',1));m.reg_write(UC_X86_REG_EDI,MENU);m.reg_write(UC_X86_REG_ESP,STACK)
                    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
                    m.emu_start(0x44a3ee,BASE,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x44a476
                    initial=snapshot()
                    if selected>=0:
                        put(MENU+0x38,selected);events.clear();sounds.clear();scripts.clear()
                        put(0x4d6884,pressed);put(0x4d6880,repeat)
                        m.reg_write(UC_X86_REG_EDI,MENU);m.reg_write(UC_X86_REG_ESP,STACK)
                        m.emu_start(0x44a488,BASE,count=100000)
                        assert m.reg_read(UC_X86_REG_EIP) in (0x44b004,0x44a476),hex(m.reg_read(UC_X86_REG_EIP))
                    rows.append(dict(difficulty=difficulty,continues=continues,selected=selected,pressed=pressed,repeat=repeat,initial=initial,result=snapshot()))
    out=ROOT/'artifacts/th14/end-choices-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} native end-choice initialization/input cases.')
if __name__=='__main__':main()
