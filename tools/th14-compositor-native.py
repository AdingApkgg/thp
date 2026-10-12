"""TH14 Supervisor/ANM callback ordering and render-target transitions.

D3D, camera upload/projection, ANM binding/updating/drawing and layer draw are
recording boundaries. Camera reset and callback bodies execute from retail PE.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,STACK,RETURN,MANAGER,SUP=0x70000000,0x700ff000,0x700fe000,0x71000000,0x4d8f60


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000);m.mem_map(MANAGER,0x1000000)
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def values(p,fmt):return list(struct.unpack(fmt,m.mem_read(p,struct.calcsize(fmt))))
    device,table,texture,texture_table,resource,textures=[BASE+i*0x1000 for i in range(6)]
    copies=[BASE+0x10000+i*0x1000 for i in range(4)]
    put(device,table);put(texture,texture_table);put(SUP+8,device);put(0x4f56cc,MANAGER)
    put(SUP+0x71c,resource);put(resource+0x124,textures);put(textures+0x30,texture);put(textures+0x48,texture)
    for i,p in enumerate(copies):put(SUP+0x1bc+i*4,p)
    events=[];bindings=[]
    def sink(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==RETURN+0x100:put(get(sp+20),99)
        elif address==RETURN+0x110:put(get(sp+12),2 if get(sp+12)==SUP+0x1ac else 3)
        elif address==RETURN+0x120:events.append(dict(kind='target',target=get(sp+12)))
        elif address==RETURN+0x130:
            rect=get(sp+12);events.append(dict(kind='clear',flags=get(sp+16),color=get(sp+20),rectangle=values(rect,'<4i') if rect else None))
        elif address==RETURN+0x140:events.append(dict(kind='state',state=get(sp+8),value=get(sp+12)))
        elif address==RETURN+0x150:events.append(dict(kind='viewport',viewport=values(get(sp+8),'<4I2f')))
        elif address==0x40af00:bindings.append(dict(copy=copies.index(get(sp+4)),script=get(sp+8)))
        elif address==0x478f60:events.append(dict(kind='copy',copy=copies.index(get(sp+4))))
        elif address==0x47e810:events.append(dict(kind='layer',layer=get(sp+4)))
        elif address in (0x4461e0,0x446250):events.append(dict(kind='cameraUpload' if address==0x4461e0 else 'screenCamera',camera=hex(get(sp+4))))
    for address,cleanup in ((RETURN+0x100,20),(RETURN+0x110,12),(RETURN+0x120,12),(RETURN+0x130,28),(RETURN+0x140,12),(RETURN+0x150,8),
                            (0x40af00,8),(0x46fe50,0),(0x478f60,4),(0x47e810,4),(0x4461e0,4),(0x446250,4),(0x475eb0,0),(0x4854a0,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,sink,begin=address,end=address)
    for offset,stub in ((0x48,0x100),(0x94,0x120),(0xac,0x130),(0xe4,0x140),(0xbc,0x150)):put(table+offset,RETURN+stub)
    put(texture_table+0x48,RETURN+0x110)
    def run(entry,ecx=SUP):
        put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ecx)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        try:m.emu_start(entry,RETURN,count=200000)
        except Exception:
            print('failure',hex(entry),hex(m.reg_read(UC_X86_REG_EIP)));raise
        assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(entry)
    cameras=[]
    for width,height,scale in ((640,480,1.),(960,720,1.5),(1280,960,2.)):
        put(0x4f7a64,width);put(0x4f7a68,height);m.mem_write(0x4f7a6c,struct.pack('<f',scale))
        run(0x4465e0)
        camera=dict(width=width,height=height,scale=scale,viewports=[values(SUP+offset+0xe0,'<4I2f') for offset in (0x230,0x35c,0x488,0x5b4)])
        put(SUP+0x1ac,0);put(SUP+0x1b4,0)
        for p in copies:put(p+0x18,0)
        bindings.clear();run(0x4474e0);camera['bindings']=list(bindings);cameras.append(camera)
    put(0x4f7a64,640);put(0x4f7a68,480);m.mem_write(0x4f7a6c,struct.pack('<f',1));run(0x4465e0)
    d=Cs(CS_ARCH_X86,CS_MODE_32)
    def registrations(start,end,anm=False):
        history=[];result=[]
        for i in d.disasm(img.read(start,end-start),start):
            if i.mnemonic=='call' and i.op_str=='0x4011d0':
                pushes=[int(x.op_str,0) for x in history if x.mnemonic=='push' and (x.op_str.startswith('0x') or x.op_str.isdigit())]
                if anm:
                    writes=[x for x in history if x.mnemonic=='mov' and '+ 8], 0x' in x.op_str];callback=int(writes[-1].op_str.split(', ')[1],0)
                else:callback=pushes[-2]
                result.append((pushes[-1],callback))
            history.append(i);history=history[-24:]
        return result
    supervisor=registrations(0x444eaa,0x444fdd)
    animation=registrations(0x47aae5,0x47b885,True)
    assert len(supervisor)==10 and len(animation)==32
    def observations(rows,ecx):
        result=[]
        for priority,entry in rows:
            events.clear();run(entry,ecx)
            result.append(dict(priority=priority,entry=hex(entry),events=list(events),origin=values(0x4f7a88,'<2i'),playSize=values(0x4f7a78,'<2i'),offsets=values(MANAGER+0xd0,'<2f')))
        return result
    callbacks=observations(supervisor,SUP);layers=observations(animation,MANAGER)
    out=ROOT/'artifacts/th14/compositor-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cameras=cameras,callbacks=callbacks,animation=layers),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(cameras)} display modes, {len(supervisor)} Supervisor and {len(animation)} ANM callbacks.')


if __name__=='__main__':main()
