"""Execute retail TH13 STD camera timelines and bounding-box generation.

Animation creation is a boundary sink. Culling uses identity view/projection;
the D3DX boundary applies that known projection and records native vertices.
"""
import importlib, json, struct, hashlib
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
STATE,CODE,OBJ,POS,CAMERA,STACK,RETURN=0x70000000,0x70010000,0x70030000,0x70031000,0x70032000,0x700ff000,0x700fe000

def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(13)
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(STATE,0x100000);m.mem_map(0,4096)
    for a,cleanup in ((0x47a09f,0),(0x403800,4),(0x462450,0)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    def values(p,n):return list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
    def run(address,args=(),regs=()):
        m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args));m.reg_write(UC_X86_REG_ESP,STACK)
        for reg,value in regs:m.reg_write(reg,value)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(address,RETURN,count=200000)
        assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(m.reg_read(UC_X86_REG_EIP))
    def reset(code,rate):
        m.mem_write(STATE,bytes(0x5000));m.mem_write(CODE,code)
        put(STATE+0x1c,CODE);put(STATE+0x4c,CODE)
        put(STATE+0x38,-1);put(STATE+0x44,0x4c0a28);put(STATE+0x48,1)
        floats(0x4c0a28,[rate]);floats(STATE+0x409c,[0,0,-600,0,300,600,0,1,0]);floats(STATE+0x40f0,[.5235987901687622])
    def snapshot():
        return dict(values=values(STATE+0x409c,9)+values(STATE+0x40d8,6)+values(STATE+0x4198,3)+values(STATE+0x40f0,1)+values(STATE+0x41a4,6)+values(STATE+0x40,1)+values(STATE+0x2c,1),
                    integers=[get(STATE+0x3c),get(STATE+0x28),get(STATE+0x4c)-CODE,get(STATE+0x41bc)])
    def cmd(op,args=b'',time=0):return struct.pack('<ihh',time,op,len(args)+8)+args
    rows=[]
    archive=json.loads((ROOT/'artifacts/archive-differential/th13.json').read_text())
    for number in range(1,8):
        name=f'st0{number}.std';raw=(Path(archive['extraction'])/name).read_bytes()
        expected=next(r['sha256'] for r in archive['decoded'] if r['name']==name)
        assert hashlib.sha256(raw).hexdigest()==expected
        code=raw[struct.unpack_from('<I',raw,8)[0]:]
        for rate in (.5,1,2):
            reset(code,rate);timeline=[]
            for frame in range(1200):
                floats(STATE+0x4198,[0,0,0]);run(0x408390,(STATE,));timeline.append(snapshot())
            rows.append(dict(name=name,sha256=expected,rate=rate,code=code.hex(),timeline=timeline))
    effects=[]
    for kind in range(10):
        for rate in (.5,1,2):
            for frame in (0,1,127,511,1023,1535,2047,3071):
                reset(cmd(0),rate);m.mem_write(STATE+0x20,bytes([kind]))
                put(STATE+0x24,frame-1);put(STATE+0x28,frame);floats(STATE+0x2c,[frame]);put(STATE+0x30,0x4c0a28);put(STATE+0x34,1)
                run(0x408390,(STATE,));effects.append(dict(kind=kind,rate=rate,frame=frame,output=snapshot()))
    # Additional instruction 18 and effect cancellation, absent from shipped scripts.
    synthetic=[]
    for rate in (.5,1,2):
        code=cmd(6,struct.pack('<3f',.25,1,.5))+cmd(18,struct.pack('<ii3f',8,0,-.5,.75,.125))+cmd(12,struct.pack('<i',1))+cmd(12,struct.pack('<i',0),4)+cmd(0,time=12)
        reset(code,rate);timeline=[]
        for _ in range(30):run(0x408390,(STATE,));timeline.append(snapshot())
        synthetic.append(dict(name='up-and-cancel',rate=rate,code=code.hex(),timeline=timeline))
    # D3DX identity camera boundary, not a claim about native D3DX arithmetic.
    points=[]
    def math_sink(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==RETURN+0x100:
            out=get(sp+4);v=values(sp+8,3);floats(out,[1,0,0,0,0,1,0,0,0,0,1,0,*v,1]);machine.reg_write(UC_X86_REG_EAX,out)
        else:
            out,stride,src,src_stride,viewport,projection,view,world,count=[get(sp+4+i*4) for i in range(9)]
            offset=values(world+48,3);points.clear()
            for i in range(count):
                p=values(src+i*src_stride,3);points.append(p)
                floats(out+i*stride,[(p[0]+offset[0]+1)*204+116,(1-p[1]-offset[1])*238+2,p[2]+offset[2]])
            machine.reg_write(UC_X86_REG_EAX,out)
    for slot,at,cleanup in ((0x4a22b8,RETURN+0x100,16),(0x4a22dc,RETURN+0x110,36)):
        put(slot,at);m.mem_write(at,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,math_sink,begin=at,end=at)
    culling=[]
    for x in (-2,-1,-.95,-.5,0,.5,.95,1,2):
        for y in (-2,-1,0,1,2):
            for z in (-.5,0,.25,.75,1,1.5):
                position=[x,y,z];size=[.25,.5,.75];instance=[.125,-.125,.0625]
                m.mem_write(CAMERA,bytes(0x124));floats(OBJ+4,position+size);floats(POS,instance)
                points.clear();run(0x4076c0,(struct.unpack('<I',struct.pack('<f',9610000))[0],CAMERA),((UC_X86_REG_ECX,OBJ),(UC_X86_REG_EDX,POS)))
                culling.append(dict(position=position,size=size,instance=instance,points=list(points),visible=1-m.reg_read(UC_X86_REG_EAX)))
    # Observe 43ba20's D3DX arguments; the DLL itself is outside this oracle.
    observed={}
    def camera_sink(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==RETURN+0x200:observed['lookAt']=[values(get(sp+8+i*4),3) for i in range(3)]
        elif address==RETURN+0x210:observed['perspective']=values(sp+8,4)
    for slot,at,cleanup in ((0x4a22d4,RETURN+0x200,16),(0x4a22d0,RETURN+0x210,20),(0x4a22a0,RETURN+0x220,8)):
        put(slot,at);m.mem_write(at,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,camera_sink,begin=at,end=at)
    device,table=CAMERA+0x1000,CAMERA+0x2000
    put(0x4dc688,0);put(0x4dc6a8,device);put(device,table);put(table+0xb0,RETURN+0x230);m.mem_write(RETURN+0x230,b'\xc2\x0c\x00')
    views=[]
    for i in range(12):
        position=[i*7.5,-i*3.25,-600+i*40];direction=[30,300,600];up=[i*.01,1,0];cached=[.125+i*.015625,.25,.875];eye=[i*2.5,-i*1.25,i*.75]
        m.mem_write(CAMERA,bytes(0x124));floats(CAMERA,position+direction+up+cached+[0,0,0]+eye+[9,13,17]+[.625])
        put(CAMERA+0xe0,408);put(CAMERA+0xe4,476);observed.clear()
        run(0x43ba20,regs=((UC_X86_REG_EDI,CAMERA),))
        views.append(dict(input=position+direction+up+cached+eye,output=dict(observed)))
    out=ROOT/'artifacts/th13/stage-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,effects=effects,synthetic=synthetic,culling=culling,views=views),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(rows)} retail camera timelines, {len(effects)} effect states, {len(culling)} culling cases.')
if __name__=='__main__':main()
