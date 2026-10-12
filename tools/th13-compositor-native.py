"""Observe TH13's original camera reset, copy bindings and render callbacks.

Only GPU calls, ANM binding/drawing and the security-cookie helper are sinks.
Camera reset and Supervisor callback bodies execute from the pinned retail PE.
"""
import importlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
BASE, STACK, RETURN, MANAGER = 0x70000000, 0x700ff000, 0x700fe000, 0x71000000
SUP = 0x4dc6a0

def main():
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(13)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        first = base & ~4095
        m.mem_map(first, ((base+size+4095)&~4095)-first)
        m.mem_write(base, img.data[raw:raw+n])
    m.mem_map(BASE, 0x100000)
    m.mem_map(MANAGER, 0x1000000)
    def put(p, v): m.mem_write(p, struct.pack('<I', v & 0xffffffff))
    def get(p): return struct.unpack('<I', m.mem_read(p, 4))[0]
    def values(p, fmt): return list(struct.unpack(fmt, m.mem_read(p, struct.calcsize(fmt))))
    def run(address, args=()):
        m.mem_write(STACK, struct.pack('<'+'I'*(len(args)+1), RETURN, *args))
        m.reg_write(UC_X86_REG_ESP, STACK)
        m.reg_write(UC_X86_REG_ECX, SUP)
        m.reg_write(UC_X86_REG_FPCW, 0x37f)
        m.reg_write(UC_X86_REG_FPSW, 0)
        m.reg_write(UC_X86_REG_FPTAG, 0xffff)
        m.emu_start(address, RETURN, count=100000)
        assert m.reg_read(UC_X86_REG_EIP) == RETURN, hex(address)
    events, bindings = [], []
    device, table, texture, texture_table, resource, textures = [BASE+i*0x1000 for i in range(1, 7)]
    copies = [BASE+0x10000+i*0x1000 for i in range(4)]
    vertex_buffer, vertex_table, vertex_data = BASE+0x20000, BASE+0x21000, BASE+0x22000
    put(device, table); put(texture, texture_table)
    put(SUP+8, device); put(0x4dc688, MANAGER)
    put(SUP+0x5b4, resource); put(resource+0x124, textures)
    put(textures+0x30, texture); put(textures+0x48, texture)
    for i, vm in enumerate(copies): put(SUP+0x1bc+i*4, vm)
    def sink(machine, address, size, user):
        sp = machine.reg_read(UC_X86_REG_ESP)
        if address == RETURN+0x100:
            put(get(sp+20), 99)
        elif address == RETURN+0x110:
            out = get(sp+12); put(out, 2 if out == SUP+0x1ac else 3)
        elif address == RETURN+0x120:
            events.append(dict(kind='target', target=get(sp+12)))
        elif address == RETURN+0x130:
            rect = get(sp+12)
            events.append(dict(kind='clear', color=get(sp+20), rectangle=values(rect,'<4i') if rect else None))
        elif address == RETURN+0x140:
            events.append(dict(kind='state',state=get(sp+8),value=get(sp+12)))
        elif address == RETURN+0x160: put(get(sp+24), vertex_buffer)
        elif address == RETURN+0x170: put(get(sp+16), vertex_data)
        elif address == RETURN+0x1a0:
            events.append(dict(kind='sampler', sampler=get(sp+8), state=get(sp+12), value=get(sp+16)))
        elif address == RETURN+0x1b0:
            events.append(dict(kind='matrix', state=get(sp+8), values=values(get(sp+12),'<16f')))
        elif address == RETURN+0x1d0:
            data,stride=get(sp+16),get(sp+20)
            events.append(dict(kind='rectangle',topology=get(sp+8),count=get(sp+12),stride=stride,
                               vertices=[values(data+i*stride,'<3fI2f' if stride==24 else '<4fI') for i in range(get(sp+12)+(1 if get(sp+8)==3 else 2))]))
        elif address == 0x403800:
            bindings.append(dict(copy=copies.index(machine.reg_read(UC_X86_REG_EBX)), script=machine.reg_read(UC_X86_REG_EAX)))
        elif address == 0x46a700:
            events.append(dict(kind='copy', copy=copies.index(machine.reg_read(UC_X86_REG_EAX))))
        elif address == 0x46f380:
            events.append(dict(kind='layer', layer=machine.reg_read(UC_X86_REG_EAX)))
    stubs = [(RETURN+0x100,20),(RETURN+0x110,12),(RETURN+0x120,12),
             (RETURN+0x130,28),(RETURN+0x140,12),(RETURN+0x150,8),
             (RETURN+0x160,28),(RETURN+0x170,20),(RETURN+0x180,4),(RETURN+0x190,20),
             (RETURN+0x1a0,16),
             (RETURN+0x1b0,12),(RETURN+0x1c0,16),(RETURN+0x1d0,20),
             (0x403800,4),(0x462450,0),(0x46a700,4),(0x46f380,0),
             (0x4679a0,0),(0x43ba20,0),(0x47a09f,0)]
    for address, cleanup in stubs:
        m.mem_write(address, b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE, sink, begin=address, end=address)
    for offset, stub in ((0x48,0x100),(0x94,0x120),(0xac,0x130),(0xe4,0x140),(0xbc,0x150)):
        put(table+offset, RETURN+stub)
    put(texture_table+0x48, RETURN+0x110)
    put(table+0x68, RETURN+0x160)
    put(table+0x190, RETURN+0x190)
    put(vertex_buffer, vertex_table); put(vertex_table+0x2c, RETURN+0x170); put(vertex_table+0x30, RETURN+0x180)
    run(0x46c950)
    anchor_vertices=[values(vertex_data+i*20,'<5f') for i in range(36)]
    cameras=[]
    for restricted, entry in ((False,0x43bed0),(True,0x43bbc0)):
        run(entry)
        cameras.append(dict(restricted=restricted, full=values(0x4dcaa8,'<4I2f'),
                            play=values(0x4dc984,'<4I2f'), world=values(0x4dcbcc,'<4I2f')))
    run(0x43cd40, (SUP,))
    callbacks=[(1,0x43c4b0),(12,0x43c600),(14,0x43c870),(38,0x43c6a0),
               (40,0x43c920),(41,0x43c740),(42,0x43c9d0),(52,0x43c7e0),
               (53,0x43ca50),(76,0x43c840)]
    observations=[]
    for priority, entry in callbacks:
        events.clear(); run(entry)
        observations.append(dict(priority=priority,entry=hex(entry),events=list(events)))
    # Callback priorities are immediate operands in the registration code.
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    d=Cs(CS_ARCH_X86,CS_MODE_32)
    instructions=list(d.disasm(img.read(0x43a4b8,0x43a7dc-0x43a4b8),0x43a4b8))
    priority=1; callback=0; registered=[]
    for ins in instructions:
        if ins.mnemonic=='mov' and ins.op_str.startswith('ebx, '): priority=int(ins.op_str[5:],0)
        if ins.mnemonic=='mov' and ins.op_str.startswith(('dword ptr [eax + 8], 0x','dword ptr [esi + 8], 0x')):
            callback=int(ins.op_str.split(', ')[1],0)
        if ins.mnemonic=='call' and ins.op_str=='0x470a40': registered.append((priority,callback))
    assert registered==callbacks, registered
    put(table+0x114, RETURN+0x1a0)
    addressing=[]
    for u in range(4):
        for v in range(4):
            events.clear()
            put(copies[0]+0x1c,u); put(copies[0]+0x18,v<<30)
            m.mem_write(MANAGER+0xb78194,b'\xff\xff')
            m.reg_write(UC_X86_REG_ESP,STACK)
            m.reg_write(UC_X86_REG_EDI,copies[0]); m.reg_write(UC_X86_REG_ESI,MANAGER)
            m.emu_start(0x467281,0x467318,count=1000)
            assert m.reg_read(UC_X86_REG_EIP)==0x467318
            addressing.append(dict(u=u,v=v,events=list(events)))
    for offset,stub in ((0xb0,0x1b0),(0x104,0x140),(0x10c,0x1c0),(0x144,0x1c0),(0x164,0x150)):
        put(table+offset,RETURN+stub)
    sprite=BASE+0x23000;put(sprite+8,texture)
    world_transforms=[]
    for parent in (0,1,2):
        for root_offset,depth in ((0,0),(0,1),(1,0),(1,1)):
            vm,ancestor=copies[:2];m.mem_write(vm,bytes(0x700));m.mem_write(ancestor,bytes(0x700))
            put(vm+0x18,15|(8<<25)|(depth<<13));put(vm+0x1c,(0x10000 if parent==2 else 0)|(root_offset<<18));put(SUP+0x894,2)
            put(vm+0x528,0xffffffff);put(vm+0x2c,sprite)
            for offset,data in ((0x60,[1.5,.625,.75,1.25]),(0x78,[2.5,.75]),(0x90,[3.25,-5]),
                                (0x574,[127.25,200.75,.375]),(0x3c,[3.25,-9.5,.125]),(0x4e0,[4.5,2.25,.25]),(0x3b8,[.125,.25])):
                m.mem_write(vm+offset,struct.pack('<'+'f'*len(data),*data))
            matrix=[.5,0,0,0,0,.25,0,0,0,0,1,0,0,0,0,1]
            m.mem_write(vm+0x3e0,struct.pack('<16f',*matrix));m.mem_write(vm+0x460,struct.pack('<16f',*matrix))
            if parent:
                put(vm+0x570,ancestor);put(ancestor+0x1c,0x40000)
                m.mem_write(ancestor+0x574,struct.pack('<3f',11.25,-7.5,10))
            events.clear();m.reg_write(UC_X86_REG_EDX,vm)
            put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,MANAGER)
            m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
            m.emu_start(0x4692d0,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
            world_transforms.append(dict(parent=parent,rootOffset=root_offset,depthFlag=depth,depthWrites=[e['value'] for e in events if e['kind']=='state' and e['state']==14],matrices=[e for e in events if e['kind']=='matrix']))
    # Execute the real draw dispatcher for untextured shape modes. Only its
    # device calls remain sinks; capture the actual vertices submitted to D3D.
    m.mem_write(0x46a700,img.read(0x46a700,16));m.ctl_remove_cache(0x46a700,0x46a710);put(table+0x14c,RETURN+0x1d0)
    rectangles=[]
    for mode in (15,19,20,21):
        for ax in range(3):
            for ay in range(3):
                for parent in (0,1,2):
                    vm,ancestor=copies[:2];m.mem_write(vm,bytes(0x700));m.mem_write(ancestor,bytes(0x700))
                    put(vm+0x18,7|(mode<<25)|(ax<<21)|(ay<<23));put(vm+0x1c,0x10000 if parent==2 else 0)
                    put(vm+0x528,0x9f123456);put(vm+0x52c,0x6134abcd)
                    for offset,data in ((0x60,[1.5,.625,.75,1.25]),(0x80,[37.5,23.25]),(0x90,[3.25,-5]),
                                        (0x574,[127.25,200.75,.375]),(0x3c,[3.25,-9.5,.125]),(0x4e0,[4.5,2.25,.25]),(0x50,[.375])):
                        m.mem_write(vm+offset,struct.pack('<'+'f'*len(data),*data))
                    if parent:
                        put(vm+0x570,ancestor);put(ancestor+0x1c,0x40000)
                        m.mem_write(ancestor+0x574,struct.pack('<3f',11.25,-7.5,10))
                        m.mem_write(ancestor+0x60,struct.pack('<4f',.5,2,3,4))
                        m.mem_write(ancestor+0x50,struct.pack('<f',-.625))
                    put(MANAGER+0xf48200,BASE+0x30000)
                    events.clear();m.reg_write(UC_X86_REG_EAX,vm);run(0x46a700,(MANAGER,))
                    rectangles.append(dict(mode=mode,ax=ax,ay=ay,parent=parent,
                                           draws=[e for e in events if e['kind']=='rectangle']))
    circles=[]
    for mode in (16,17):
        for parent in (0,1,2):
            for segments in (2,7,24):
                vm,ancestor=copies[:2];put(vm+0x18,7|(mode<<25));put(vm+0x1c,0x10000 if parent==2 else 0)
                put(vm+0x570,ancestor if parent else 0);put(vm+0x4ac,segments)
                put(MANAGER+0xf48200,BASE+0x30000)
                events.clear();m.reg_write(UC_X86_REG_EAX,vm);run(0x46a700,(MANAGER,))
                circles.append(dict(mode=mode,parent=parent,segments=segments,draws=[e for e in events if e['kind']=='rectangle']))
    vertex_colors=[]
    for mode in range(4):
        for tinted in (0,1):
            vm=copies[0];put(vm+0x18,mode<<17);put(vm+0x528,0x9f123456);put(vm+0x52c,0x6134abcd)
            put(MANAGER+0xf53c40,0x4080c0ff);put(MANAGER+0xf53c44,tinted)
            m.reg_write(UC_X86_REG_ESP,STACK-32);m.reg_write(UC_X86_REG_EBP,STACK)
            m.reg_write(UC_X86_REG_EDI,vm);m.reg_write(UC_X86_REG_ESI,MANAGER)
            m.emu_start(0x4677cb,0x46792f,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x46792f
            vertex_colors.append(dict(mode=mode,tinted=tinted,colors=[get(0x4e47e8+i*28) for i in range(4)]))
    ribbon_draws=[]
    for parent in (0,1):
        for root_offset in (0,1):
            for depth in (0,1):
                vm=copies[0];m.mem_write(vm,bytes(0x700));put(vm+0x18,7|(depth<<13));put(vm+0x1c,root_offset<<18)
                put(vm+0x570,copies[1] if parent else 0);put(vm+0x2c,sprite);put(vm+0x58c,BASE+0x40000)
                for offset,data in ((0x60,[1.5,.625,.75,1.25]),(0x78,[2.5,.75]),(0x90,[3.25,-5]),
                                    (0x574,[127.25,200.75,.375]),(0x3c,[3.25,-9.5,.125]),(0x4e0,[4.5,2.25,.25]),(0x3b8,[.125,.25])):
                    m.mem_write(vm+offset,struct.pack('<'+'f'*len(data),*data))
                m.mem_write(vm+0x460,struct.pack('<16f',.5,0,0,0,0,.25,0,0,0,0,1,0,0,0,0,1))
                for i in range(32):m.mem_write(BASE+0x40000+i*24,struct.pack('<3fI2f',float(i),float(-i),float(i*2),0x80123456,i/32,.25))
                put(0x4dcf34,1-depth);put(0x4dcf30,0);events.clear()
                put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,vm)
                m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
                m.emu_start(0x402f20,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
                ribbon_draws.append(dict(parent=parent,rootOffset=root_offset,depth=depth,events=list(events)))
    import hashlib
    out=ROOT/'artifacts/th13/compositor-native.json'
    out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),
                                  cameras=cameras,bindings=bindings,callbacks=observations,
                                  anchorVertices=anchor_vertices,addressing=addressing,worldTransforms=world_transforms,rectangles=rectangles,circles=circles,vertexColors=vertex_colors,ribbonDraws=ribbon_draws),indent=2)+'\n',encoding='utf-8')
    print(f'Observed {len(bindings)} copy bindings, {len(cameras)} camera resets and {len(observations)} native render callbacks.')

if __name__=='__main__': main()
