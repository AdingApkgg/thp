"""Retail TH14 STD camera observation; animation/resource effects are sinks."""
import importlib,json,struct,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
STATE,CODE,STACK,RETURN=0x70000000,0x70010000,0x700ff000,0x700fe000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(STATE,0x100000);m.mem_map(0,4096)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def values(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    events=[]
    def boundary(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==0x40af00:events.append(['animation',get(sp+8)])
        if address==0x40f610:events.append(['interrupt',get(sp+4)])
        if address==0x4854af:machine.reg_write(UC_X86_REG_EAX,0)
    for address,cleanup in ((0x40af00,8),(0x46fe50,0),(0x40f610,4),(0x4854af,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def run():
        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,STATE)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        events.clear();m.emu_start(0x40f670,RETURN,count=200000)
        assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(m.reg_read(UC_X86_REG_EIP))
    def reset(code,rate):
        m.mem_write(STATE,bytes(0x5000));m.mem_write(CODE,code)
        put(STATE+0x1c,CODE);put(STATE+0x4c,CODE);put(STATE+0x38,-1);put(STATE+0x44,0x4d8f58);put(STATE+0x48,1)
        floats(0x4d8f58,[rate]);floats(STATE+0x4274,[0,0,-600,0,300,600,0,1,0]);floats(STATE+0x42c8,[.5235987901687622])
    def snapshot():
        return dict(values=values(STATE+0x4274,9)+values(STATE+0x42b0,6)+values(STATE+0x4378,3)+values(STATE+0x42c8,1)+values(STATE+0x4384,6)+values(STATE+0x40,1)+values(STATE+0x2c,1),
                    integers=[get(STATE+0x3c),get(STATE+0x28),get(STATE+0x4c)-CODE,get(STATE+0x439c)],events=list(events))
    def cmd(op,args=b'',time=0):return struct.pack('<ihh',time,op,len(args)+8)+args
    rows=[];archive=json.loads((ROOT/'artifacts/archive-differential/th14.json').read_text())
    for number in range(1,8):
        name=f'st0{number}.std';raw=(Path(archive['extraction'])/name).read_bytes();expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name)
        assert hashlib.sha256(raw).hexdigest()==expected;code=raw[struct.unpack_from('<I',raw,8)[0]:]
        for rate in (.5,1,2):
            reset(code,rate);timeline=[]
            for frame in range(1200):
                floats(STATE+0x4378,[0,0,0]);run();timeline.append(snapshot())
            rows.append(dict(name=name,sha256=expected,rate=rate,code=code.hex(),timeline=timeline))
    effects=[]
    for kind in range(10):
        for rate in (.5,1,2):
            for frame in (0,1,127,511,1023,1535,2047,3071):
                reset(cmd(0),rate);m.mem_write(STATE+0x20,bytes([kind]));put(STATE+0x24,frame-1);put(STATE+0x28,frame);floats(STATE+0x2c,[frame]);put(STATE+0x30,0x4d8f58);put(STATE+0x34,1)
                run();effects.append(dict(kind=kind,rate=rate,frame=frame,output=snapshot()))
    observed={};camera=STATE+0x8000
    def camera_sink(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==RETURN+0x200:observed['lookAt']=[values(get(sp+8+i*4),3) for i in range(3)]
        elif address==RETURN+0x210:observed['perspective']=values(sp+8,4)
    for slot,address,cleanup in ((0x4b12ec,RETURN+0x200,16),(0x4b12e8,RETURN+0x210,20),(0x4b12b8,RETURN+0x220,8)):
        put(slot,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,camera_sink,begin=address,end=address)
    device,table=camera+0x1000,camera+0x2000
    put(0x4f56cc,0);put(0x4d8f68,device);put(device,table);put(table+0xb0,RETURN+0x230);m.mem_write(RETURN+0x230,b'\xc2\x0c\x00')
    views=[]
    for i in range(12):
        position=[i*7.5,-i*3.25,-600+i*40];direction=[30,300,600];up=[i*.01,1,0];cached=[.125+i*.015625,.25,.875];eye=[i*2.5,-i*1.25,i*.75]
        m.mem_write(camera,bytes(0x12c));floats(camera,position+direction+up+cached+[0,0,0]+eye+[9,13,17]+[.625]);put(camera+0xe8,408);put(camera+0xec,472)
        m.mem_write(STACK,struct.pack('<II',RETURN,camera));m.reg_write(UC_X86_REG_ESP,STACK);observed.clear();m.emu_start(0x446400,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
        views.append(dict(input=position+direction+up+cached+eye,output=dict(observed)))
    out=ROOT/'artifacts/th14/stage-native.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,effects=effects,views=views),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(rows)} TH14 STD timelines / 25,200 camera states and {len(effects)} effect states observed.')

if __name__=='__main__':main()
