"""Execute retail 44ae10..44aee9 and its real 447a80 power helper.

HUD/option calls are boundaries. This proves counter restoration, not the
player option implementation, audio restoration or native respawn lifecycle.
"""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,HUD,CONTROL,STACK=0x70000000,0x70001000,0x70002000,0x70010000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x20000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<i',m.mem_read(p,4))[0]
    notices=[]
    def notice(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP);notices.append([get(sp+4),get(sp+8)])
    for address,cleanup in ((0x434fd0,8),(0x434ef0,8),(0x44f970,0),(0x434430,8)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
    m.hook_add(UC_HOOK_CODE,notice,begin=0x434430,end=0x434430)
    m.hook_add(UC_HOOK_CODE,lambda *args:m.emu_stop(),begin=0x44aef0,end=0x44aef0)
    rows=[]
    for maximum,step,continues,fragments in itertools.product((-40,0,40,80,160,200,400,600),(40,100),(0,1,8,9),(-1,0,2,7)):
        m.mem_write(BASE,bytes(0x20000));notices.clear()
        put(0x4db550,HUD);put(0x4db558,CONTROL);put(0x4db67c,BASE+0x3000)
        for p,v in ((0x4f5830,123456),(0x4f5838,continues),(0x4f5858,7),(0x4f585c,maximum),(0x4f5860,step),
                    (0x4f5864,-1),(0x4f5868,2),(0x4f5870,0),(0x4f5874,fragments),(0x4f58c8,5),(CONTROL+0x80,0x3517)):
            put(p,v)
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EDI,BASE+0x4000)
        m.emu_start(0x44ae10,BASE,count=100000)
        assert m.reg_read(UC_X86_REG_EIP)==0x44aef0
        rows.append(dict(maximum=maximum,step=step,continues=continues,bombFragments=fragments,
            result=[get(p) for p in (0x4f5864,0x4f5868,0x4f5870,0x4f5874,0x4f5858,0x4f5838,0x4f5830)],
            capped=bool(notices),notice=notices[:],remaining=get(0x4f58c8),controlFlags=get(CONTROL+0x80)))
    out=ROOT/'artifacts/th14/continue-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8')
    print(f'{len(rows)} native Continue counter cases.')
if __name__=='__main__':main()
