"""Retail 436769..436baa result/old-background gates; called services controlled."""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]

def main():
    img, *_ = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, base, size, raw, n in img.sections:
        start = base & ~4095
        m.mem_map(start, ((base+size+4095)&~4095)-start)
        m.mem_write(base, img.data[raw:raw+n])
    base = 0x70000000
    m.mem_map(base, 0x100000)
    control, hud, owner, stack = base+0x1000, base+0x2000, base+0x10000, base+0xf0000
    managers = [0x4db678,0x4db67c,0x4db530,0x4db544,0x4db660,0x4db664,0x4db53c,0x4db52c,0x4db694,0x4db534]
    services = {0x434d80:('entry',0),0x40f170:('incoming_std',0),0x4105f0:('outgoing_std',0),0x410740:('background_overlap',0),0x416240:('bullets_reset',0),0x44cc10:('player_start',0),0x41d8c0:('items_reset',0),0x41da20:('enemies_reset',0),0x435990:('stage_state',0),0x455ed0:('replay_start',0),0x48f980:('zero_spawn',0),0x421ef0:('spawn_main',8),0x42ed00:('hud_start',0),0x44f970:('manager_service',0),0x445710:('music',8),0x445810:('music_service',0),0x47f140:('interrupt',8),0x408b00:('clock_set',4)}
    services.update({0x434360:('control_service',0),0x46fe50:('animation_service',0),0x408690:('clock_tick',4),0x46ef90:('music_command',12)})
    calls=[]
    full_execution=False
    def put(p,v): m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p): return struct.unpack('<I',m.mem_read(p,4))[0]
    def hook(uc,a,n,u):
        if a==0x436d18 and not full_execution:
            uc.emu_stop();return
        if full_execution and a in (0x445710,0x445810):return
        if a not in services:return
        name,pop=services[a];sp=uc.reg_read(UC_X86_REG_ESP)
        args=[get(sp+4+i*4) for i in range(pop//4)]
        calls.append(dict(service=name,args=args))
        if name=='zero_spawn':uc.mem_write(get(sp+4),bytes(get(sp+12)))
        if name=='clock_set':put(uc.reg_read(UC_X86_REG_ECX)+4,args[0])
        if name=='clock_tick':
            timer=uc.reg_read(UC_X86_REG_ECX);put(timer+4,get(timer+4)+1)
        uc.reg_write(UC_X86_REG_EAX,0)
        uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
        uc.reg_write(UC_X86_REG_EIP,get(sp))
    m.hook_add(UC_HOOK_CODE,hook)
    rows=[]
    for old, result, timer, flags, frame in itertools.product((0,1),(0,0x100),(-1,0,119,120,121,200),(0,0x10,0x800,0x810),(0,1,29,30,31)):
        m.mem_write(base,bytes(0x100000))
        put(0x4db550,hud);put(hud+0x17c,result);put(hud+0x184,timer);put(hud+0xcc,101)
        put(control+0x14,frame);put(control+0x80,flags);put(0x4db524,old)
        put(0x4db520,owner);put(owner+0x191e8,102);put(owner+0x191ec,103);put(0x4d9130,104)
        put(0x4db69c,base+0x3000);put(base+0x3030,7);put(0x4f58b8,0)
        callback_flags=[]
        for i,global_address in enumerate(managers):
            manager=base+0x4000+i*0x100;put(global_address,manager)
            for offset in (8,12,16):
                callback=manager+offset*4;put(manager+offset,callback);put(callback+4,0x40)
                if offset in ((12,16) if global_address==0x4db52c else (8,12)):
                    callback_flags.append(callback+4)
        put(stack,base);calls.clear()
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,control)
        m.emu_start(0x436769,0x436baa,count=10000)
        pc=m.reg_read(UC_X86_REG_EIP);names=[c['service'] for c in calls]
        gated=bool(result and timer<120 and not(flags&0x10))
        activation=bool(not gated and ((frame==0 and not old) or (frame==30 and flags&0x800)))
        assert pc==(0x436d18 if gated else 0x436baa),(old,result,timer,flags,frame,hex(pc))
        assert ('spawn_main' in names)==activation
        assert ('player_start' in names)==activation
        assert ('background_overlap' in names)==(not gated and frame==0 and bool(old))
        if activation:
            assert next(c['args'][0] for c in calls if c['service']=='spawn_main')==0x4be064
            assert all(get(p)==0x42 for p in callback_flags)
            assert get(owner+0x191ec)==0
        if not gated and frame==0 and old:
            assert get(control+0x80)&0x800
            assert calls[-1]==dict(service='interrupt',args=[101,1])
        if not gated and frame==30 and flags&0x800:
            assert not get(control+0x80)&0x800
            assert get(control+0x14)==0
        rows.append(dict(oldBackground=old,hudFlags=result,resultTimer=timer,controlFlags=flags,controlFrame=frame,gated=gated,activated=bool(activation),finalFlags=get(control+0x80),finalFrame=get(control+0x14),calls=calls.copy()))
    # Execute the whole control callback and actual445710/445810 wrappers.
    # Only the music command queue and the other called services are controlled.
    full_execution=True;music_rows=[]
    for stage,old,frame,flags,music_flags in itertools.product(range(1,8),(0,1),(0,29,30,31,299,300,301),(0,0x800),(0,0x10)):
        m.mem_write(control,bytes(0x100));put(control+0x14,frame);put(control+0x80,flags)
        put(hud+0x17c,0);put(0x4db524,base+0x8000 if old else 0)
        put(base+0x8000+0x4224,0);put(0x4db68c,base+0x30000)
        put(0x4db688,base+0x3000);put(base+0x3010,1)
        put(0x4f58a4,stage);put(0x4db69c,0x4d5988+stage*0xcc)
        put(0x4d916c,music_flags);put(0x4f58b8,0)
        put(owner+0x191ec,103);put(stack,base);calls.clear()
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,control)
        m.emu_start(0x436620,base,count=20000)
        assert m.reg_read(UC_X86_REG_EIP)==base
        assert m.reg_read(UC_X86_REG_EAX)==1
        commands=[c['args'] for c in calls if c['service']=='music_command']
        activation=bool((frame==0 and not old) or (frame==30 and flags&0x800))
        if activation:
            expected=([4 if music_flags else 3] if frame==30 else [])+([4] if music_flags else [])+[2]
            assert [c[0] for c in commands]==expected,(stage,old,frame,flags,music_flags,commands)
            assert all(c[1]==0 and c[2]==0x4be6fc for c in commands)
        else:assert not commands
        music_rows.append(dict(stage=stage,oldBackground=old,controlFrame=frame,controlFlags=flags,musicFlags=music_flags,commands=commands,finalFrame=get(control+0x14)))
    result=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,musicRows=music_rows,scope='Retail instructions436769..436baa and early return436d18: signed120-frame HUD result gate, control flag10 bypass, clock0 incoming STD/outgoing background handshake and flag800 clock30 activation, callback flag writes, native main-subroutine request, loading interrupts and controller clock reset. Additional392 cases execute whole436620 control callback and actual445710/445810 music wrappers for stages1..7 with clock0/29/30/31/299/300/301: no stage6 clock300 music command; actual queue command2 at activation and command3/4 during handoff. Other called services, timer stepping, manager/callback objects and music queue controlled; native workers, callback execution, resources, gameplay and actual audio/GPU state excluded.')
    (ROOT/'artifacts/th14/transition-control-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'PASS {len(rows)} retail result/background/control-clock gate cases and {len(music_rows)} whole-control music boundaries')

if __name__=='__main__':main()
