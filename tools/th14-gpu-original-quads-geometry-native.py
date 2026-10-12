"""TH14 retail draw dispatcher, quad submission and material state oracle.

Only the D3D device, GPU batch/flush and security-cookie boundaries are sinks.
Geometry, culling, UV scaling, inherited color and material selection run in PE.
"""
import hashlib
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,STACK,RETURN,MANAGER=0x70000000,0x700ff000,0x700fe000,0x71000000
VM,PARENT,DEVICE,TABLE,SPRITE,TEXTURE,CAMERA=[BASE+i*0x1000 for i in range(7)]


def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll')
    dll_sha=hashlib.sha256(dll.data).hexdigest()
    assert dll_sha=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
    m.mem_map(BASE,0x100000);m.mem_map(MANAGER,0x1000000);m.mem_map(0,4096)
    for _,base,size,raw,n in dll.sections:
        first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,dll.data[raw:raw+n])
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    events=[];draws=[];device_state={};matrices={}
    vertex_buffer,vertex_table,vertex_data=BASE+0x8000,BASE+0x9000,BASE+0xa000
    def sink(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP)
        if address==RETURN+0x100:
            key,value=get(sp+8),get(sp+12);events.append(['state',key,value]);device_state[key]=value
        elif address==RETURN+0x110:events.append(['sampler',get(sp+12),get(sp+16)])
        elif address==RETURN+0x150:
            matrices[get(sp+8)]=list(struct.unpack('<16f',m.mem_read(get(sp+12),64)))
        elif address==RETURN+0x160:
            p,stride,count=get(sp+16),get(sp+20),get(sp+12)
            draws.append(dict(topology=get(sp+8),count=count,stride=stride,depth=device_state[14],fog=device_state.get(28,0),
                              matrices=dict(matrices),vertices=[list(struct.unpack('<3fI2f' if stride==24 else '<4fI' if stride==20 else '<4fI2f',m.mem_read(p+i*stride,stride))) for i in range(count+(1 if get(sp+8)==3 else 2))]))
        elif address==RETURN+0x170:put(get(sp+24),vertex_buffer)
        elif address==RETURN+0x180:put(get(sp+16),vertex_data)
        elif address==RETURN+0x1b0:
            first,count=get(sp+12),get(sp+16)
            draws.append(dict(topology=get(sp+8),count=count,depth=device_state[14],factor=device_state[60],matrices=dict(matrices),
                              vertices=[list(struct.unpack('<5f',m.mem_read(vertex_data+(first+i)*20,20))) for i in range(count+2)]))
        elif address==0x475f80:
            p=get(sp+4);draws.append([list(struct.unpack('<4fI2f',m.mem_read(p+i*28,28))) for i in range(4)])
    for address,cleanup in ((RETURN+0x100,12),(RETURN+0x110,16),(RETURN+0x120,12),(RETURN+0x130,16),(RETURN+0x140,8),(RETURN+0x150,12),(RETURN+0x160,20),(RETURN+0x170,28),(RETURN+0x180,20),(RETURN+0x190,4),(RETURN+0x1a0,20),(RETURN+0x1b0,16),(0x475eb0,0),(0x475f80,4),(0x4854a0,0)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,sink,begin=address,end=address)
    put(DEVICE,TABLE);put(TABLE+0xe4,RETURN+0x100);put(TABLE+0x114,RETURN+0x110);put(TABLE+0x104,RETURN+0x120)
    put(TABLE+0x10c,RETURN+0x130);put(TABLE+0x164,RETURN+0x140);put(TABLE+0xb0,RETURN+0x150);put(TABLE+0x14c,RETURN+0x160)
    put(TABLE+0x68,RETURN+0x170);put(TABLE+0x190,RETURN+0x1a0);put(TABLE+0x144,RETURN+0x1b0)
    put(vertex_buffer,vertex_table);put(vertex_table+0x2c,RETURN+0x180);put(vertex_table+0x30,RETURN+0x190)
    put(0x4d8f68,DEVICE);put(0x4f56cc,MANAGER);put(0x4d9640,CAMERA);put(SPRITE+8,TEXTURE);put(TEXTURE,123)
    for i,v in enumerate((0,0,640,480)):put(CAMERA+0xe0+i*4,v)
    floats(0x4f7a6c,[1]);put(0x4f7a88,320);put(0x4f7a8c,16);put(0x4f7a80,320);put(0x4f7a84,16)
    def run(entry,args):
        m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args));m.reg_write(UC_X86_REG_ESP,STACK)
        m.reg_write(UC_X86_REG_ECX,MANAGER);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.emu_start(entry,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN,hex(entry)
    # 10046a3e..10046a4e copies the baseline before a CPU-specific overlay.
    m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4))
    run(0x101bc521,(0x101ca068,))
    pe=struct.unpack_from('<I',dll.data,0x3c)[0];directory=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
    count=dll.u32(directory+24);functions,names,ordinals=[dll.image_base+dll.u32(directory+offset) for offset in (28,32,36)]
    exports={}
    for i in range(count):
        name=dll.read(dll.image_base+dll.u32(names+4*i),128).split(b'\0')[0].decode('ascii')
        ordinal=struct.unpack('<H',dll.read(ordinals+2*i,2))[0];exports[name]=dll.image_base+dll.u32(functions+4*ordinal)
    for iat,name in ((0x4b12d4,'D3DXMatrixMultiply'),(0x4b12d8,'D3DXMatrixRotationX'),(0x4b12f8,'D3DXMatrixRotationY'),(0x4b12cc,'D3DXMatrixRotationZ')):
        put(iat,exports[name])
    run(0x47b9f0,())
    def setup(mode,color_mode,relation,tinted,visibility,sample):
        m.mem_write(VM,bytes(0x2000));m.mem_write(MANAGER+0xbc8188,bytes([255])*16)
        m.mem_write(0x4fd218,bytes(112))
        for i in range(4):floats(0x4fd224+i*28,[1])
        flags2=(0x1000000 if relation==2 else 0)|(0x1008000 if relation==3 else 0)
        put(VM+0x18,3|(mode<<25)|(color_mode<<17)|((sample%3)<<21)|(((sample//3)%3)<<23))
        put(VM+0x1c,flags2|(0x20 if visibility==4 else 0));put(VM+0x2c,SPRITE)
        if visibility==3:put(VM+0x18,get(VM+0x18)&~1)
        put(VM+0x534,0x00123456 if visibility in (1,2) else 0x9f123456)
        put(VM+0x538,0x0034abcd if visibility==2 else 0x6134abcd);put(VM+0x53c,0x11223344)
        put(VM+0x594,PARENT if relation else 0);put(PARENT+0x53c,0x4080c0ff)
        floats(PARENT+0x60,[.5,2,3,4]);floats(PARENT+0x59c,[11.25,-7.5,10]);floats(PARENT+0x50,[-.625])
        for offset,v in ((0x60,[1.1,-.625,.75,1.25]),(0x78,[1.37,-.71]),(0x80,[31.75,47.625]),(0x90,[2.3,-7.1]),
                         (0x59c,[127.25+sample*7,200.75-sample*5,.375]),(0x3c,[3.25,-9.5,.125]),(0x4ec,[4.5,2.25,.25]),
                         (0x50,[0 if sample%2 else .375]),(0x88,[.17,-.23]),(0x3b8,[.123,.234,.789,.345,.246,.891,.912,.987])):floats(VM+offset,v)
        floats(MANAGER+0xd0,[.37,-.61]);put(MANAGER+0xff52cc,0x4080c0ff);put(MANAGER+0xff52d0,tinted)
        put(0x4d9964,1);events.clear();draws.clear()
    quads=[]
    for mode in range(4):
        for color_mode in range(4):
            for relation in range(4):
                for tinted in range(2):
                    for visibility in range(5):
                        sample=(mode+color_mode+relation+tinted)%9
                        setup(mode,color_mode,relation,tinted,visibility,sample);run(0x478f60,(VM,))
                        quads.append(dict(mode=mode,colorMode=color_mode,relation=relation,tinted=tinted,visibility=visibility,sample=sample,
                                          status=m.reg_read(UC_X86_REG_EAX),cachedColor=get(VM+0x53c),draws=list(draws),events=list(events)))
    materials=[]
    for blend in range(16):
        for u in range(4):
            for v in range(4):
                for point in range(2):
                    setup(0,0,0,0,0,0);put(VM+0x18,(blend<<5)|(v<<30));put(VM+0x1c,u|(point<<10))
                    run(0x4753a0,(VM,));materials.append(dict(blend=blend,u=u,v=v,point=point,events=list(events)))
    strips=[];geometry=BASE+0x10000
    for mode in (9,13,14,23,24,22):
        for parent in range(2):
            for origin in range(4):
                for depth in range(2):
                    for prior_depth in range(2):
                        for rotation in range(3):
                            setup(mode,0,0,0,0,0);put(VM+0x18,15|(mode<<25)|(depth<<13));put(VM+0x1c,origin<<17)
                            put(VM+0x594,PARENT if parent else 0);put(VM+0x5b4,geometry);put(VM+0x4ac,6)
                            put(VM+0x5bc,0x40b3a0 if mode==22 else 0)
                            angles=([0,0,0],[.375,-.75,1.125],[1.25,.25,-2.75])[rotation];floats(VM+0x48,angles)
                            floats(VM+0x460,[.5,0,0,0,0,.25,0,0,0,0,1,0,0,0,0,1]);floats(VM+0x78,[1.37,-.71])
                            count=80 if mode==22 else 12;world=mode in (22,23,24)
                            for i in range(count):
                                values=[i*.37,-i*.71,i*1.3]+([] if world else [1])+[0x80123456,i/count,.25]
                                m.mem_write(geometry+i*(24 if world else 28),struct.pack('<3fI2f' if world else '<4fI2f',*values))
                            put(0x4d9964,prior_depth);put(0x4d9960,0);device_state.clear();device_state[14]=prior_depth;matrices.clear()
                            try:run(0x478f60,(VM,))
                            except Exception:
                                print('strip failure',mode,parent,origin,depth,prior_depth,rotation,hex(m.reg_read(UC_X86_REG_EIP)))
                                raise
                            strips.append(dict(mode=mode,parent=parent,origin=origin,depth=depth,priorDepth=prior_depth,rotation=rotation,
                                               draws=list(draws),finalDepth=device_state[14],finalFog=device_state.get(28,0)))
    shapes=[]
    for mode in (15,16,17,19,20,21):
        for anchor in range(9):
            for parent in range(3):
                for resolution in range(5):
                    setup(mode,0,0,0,0,0)
                    put(VM+0x18,3|(mode<<25)|((anchor%3)<<21)|((anchor//3)<<23));put(VM+0x1c,(resolution<<19)|(0x8000 if parent==2 else 0))
                    put(VM+0x594,PARENT if parent else 0);put(VM+0x4ac,7)
                    put(MANAGER+0xfe8200,BASE+0x20000);device_state.clear();device_state[14]=1;matrices.clear()
                    run(0x478f60,(VM,));shapes.append(dict(mode=mode,anchor=anchor,parent=parent,resolution=resolution,draws=list(draws)))
    world_quads=[]
    for parent in range(3):
        for origin in range(4):
            for resolution in range(8):
                for order in range(8):
                    sample=(parent+origin+resolution+order)%9;depth=sample%2;color_mode=order%4;tinted=resolution%2
                    setup(8,color_mode,0,tinted,0,0);put(VM+0x18,15|(8<<25)|(depth<<13)|(color_mode<<17)|((sample%3)<<21)|((sample//3)<<23))
                    put(VM+0x1c,(origin<<17)|(resolution<<19)|(order<<2)|(0x8000 if parent==2 else 0)|0x400000)
                    put(VM+0x594,PARENT if parent else 0);put(PARENT+0x1c,1<<17)
                    matrix=[.5,0,0,0,0,.25,0,0,0,0,1,0,0,0,0,1];floats(VM+0x3e0,matrix);floats(VM+0x460,matrix);floats(VM+0x48,[.375,-.75,1.125])
                    put(MANAGER+0xbc8184,0);put(MANAGER+0xbc819c,vertex_buffer);device_state.clear();device_state[14]=1;matrices.clear()
                    run(0x478f60,(VM,));world_quads.append(dict(parent=parent,origin=origin,resolution=resolution,order=order,anchor=sample,depth=depth,colorMode=color_mode,tinted=tinted,draws=list(draws)))
    screen_strips=[]
    for blend in range(16):
      for visibility in range(5):
       for count in (2,12,240):
        for prior_depth in (0,1):
         setup(1,0,0,0,visibility,0);put(VM+0x18,(get(VM+0x18)&~0x1e0)|(blend<<5))
         for i in range(count):m.mem_write(geometry+i*28,struct.pack('<4fI2f',i*.37,-float(i)*.71,i*1.3,1,0xffffffff,i/count,.25))
         device_state.clear();device_state[14]=prior_depth;matrices.clear();run(0x478a10,(VM,geometry,count))
         screen_strips.append(dict(blend=blend,visibility=visibility,count=count,priorDepth=prior_depth,status=m.reg_read(UC_X86_REG_EAX),draws=list(draws),events=list(events)))
    out=ROOT/'artifacts/th14/gpu-original-quads/geometry/native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),d3dxSha256=dll_sha,quads=quads,materials=materials,strips=strips,shapes=shapes,worldQuads=world_quads,screenStrips=screen_strips),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Observed {len(quads)} TH14 quad draws, {len(materials)} materials, {len(strips)} strips, {len(shapes)} shapes and {len(world_quads)} world quads.')


if __name__=='__main__':main()
