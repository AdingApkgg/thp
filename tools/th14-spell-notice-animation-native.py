"""Whole retail ANM interpreter on original spell result/time resources.

Only memset/sprite binding are controlled; original interpolation and clocks run.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
    img,*_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x100000)
    vm,live,resource,code,table,stack=[base+n for n in (0x1000,0x2000,0x3000,0x4000,0x8000,0xf0000)]
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
    def hook(uc,a,n,u):
        sp=uc.reg_read(UC_X86_REG_ESP)
        if a==0x48f980:
            p,v,size=get(sp+4),get(sp+8),get(sp+12);m.mem_write(p,bytes([v&255])*size);uc.reg_write(UC_X86_REG_EAX,p);pop=0
        elif a==0x46f1e0:
            # No geometry/pixel claim. The interpreter itself supplies sprite index.
            uc.reg_write(UC_X86_REG_EAX,0);pop=8
        else:return
        uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
    for a in (0x48f980,0x46f1e0):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    m.mem_write(0x4854a0,b'\xc3');put(0x4db520,base+0x9000);put(0x4f56cc,base+0x9000);m.mem_write(0x4f5815,b'\0')
    def run(address,owner,args=()):
        m.mem_write(stack,struct.pack('<'+str(len(args)+1)+'I',base,*args))
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,owner)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        try:m.emu_start(address,base,count=100000)
        except Exception as e:raise RuntimeError(f'entry{address:x} pc{m.reg_read(UC_X86_REG_EIP):x}') from e
        assert m.reg_read(UC_X86_REG_EIP)==base
        return m.reg_read(UC_X86_REG_EAX)
    def state(p):
        return [get(p+0x24),get(p+0x534),get(p+0x54c),get(p+0x550),get(p+0x560),get(p+0x564),get(p+0x18)&2,
                *[get(p+o) for o in (0x3c,0x40,0x44,0x60,0x64,0x48,0x4c,0x50)],get(p+0x28)-code if get(p+0x28) else 0xffffffff]
    archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text());source=Path(archive['extraction'])/'front.anm'
    scripts={slot:body for slot,_,body in importlib.import_module('th-anm-script-dump').scripts(source.read_bytes())}
    rows=[]
    for script in (59,60,95):
        body=scripts[script]
        for rate in (.5,.99,1,1.01,1.25):
            m.mem_write(resource,bytes(0x200));m.mem_write(resource,struct.pack('<H',5));put(resource+0x120,table);put(table+script*4,code);m.mem_write(code,body)
            put(0x4d8f58,bits(rate));m.mem_write(vm,bytes(0x700));run(0x46f3e0,resource,(vm,script))
            for o,v in ((0x548,0xfffffffe),(0x54c,0xffffffff),(0x550,0xbf800000),(0x55c,0xfffffffe),(0x560,0xffffffff),(0x564,0xbf800000)):put(vm+o,v)
            assert run(0x46fe50,vm)==0
            template=state(vm);put(resource+0x10c,vm-script*0x5cc)
            m.mem_write(live,bytes(0x700));run(0x40af00,resource,(live,script));put(live+0x24,0);put(live+0x1c,get(live+0x1c)|0x200)
            frames=[]
            for frame in range(500):
                status=run(0x46fe50,live);frames.append(dict(frame=frame,status=status,state=state(live)))
                if status:break
            assert frames[-1]['status']==1
            rows.append(dict(script=script,rateBits=bits(rate),template=template,frames=frames))
    result=dict(passed=True,rows=rows,executableSha256=hashlib.sha256(img.data).hexdigest(),resourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope='Original front59 capture/front60 failure/front95 time scripts: whole46f3e0 bind, negative-time whole46fe50 initialization, whole40af00 template copy and complete46fe50 updates until retirement at five rates. Layer/color/two clocks/visibility/local position/scale/rotation/instruction offset compared. Sprite dimensions/UV, memset and optional debug service controlled; geometry, registry retirement, GPU pixels and wall-clock timing excluded.')
    (ROOT/'artifacts/th14/spell-notice-animation-native.json').write_text(json.dumps(result)+'\n',encoding='utf-8')
    print(f'PASS {len(rows)} original spell notice timelines / {sum(len(r["frames"]) for r in rows)} interpreter frames')
if __name__=='__main__':main()
