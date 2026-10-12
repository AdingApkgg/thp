"""Retail TH14 bullet spawn/update with explicit animation and collision boundaries."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll')
    for _,base,size,raw,n in dll.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,dll.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0xa20000)
    manager,bullet,emitter,player,sprite,stack=base,base+0x9d0000,base+0x9d2000,base+0x9d3000,base+0x9d4000,base+0xa1f000
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
    spawned=[]
    def boundary(machine,address,size,user):
        sp=m.reg_read(UC_X86_REG_ESP)
        if address==0x40cc90:m.mem_write(m.reg_read(UC_X86_REG_ECX),bytes(0x5cc))
        if address==0x48f980:m.mem_write(get(sp+4),bytes([get(sp+8)&255])*get(sp+12))
        if address==0x421ef0:
            assert bytes(m.mem_read(get(sp+4),6))==b'Child\0'
            spawned.append(list(struct.unpack('<21I',m.mem_read(get(sp+8),84))))
        m.reg_write(UC_X86_REG_EAX,0)
    for address,cleanup in ((0x40cc90,0),(0x46f520,8),(0x46fe50,0),(0x416d70,4),(0x48f980,0),(0x421ef0,8)):
        m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    fields=[0x20,0x24,*range(0xbc0,0xbe8,4),0xbfc,0xc00,0xc04,0xc08,0xc20,0xc24,0x13ec,*range(0x13c0,0x13cc,4),*range(0x13d4,0x13e0,4),0xf40,0xf44,0xf48,0xf88,0xf8c,0xf90,0xf9c,0xfa0,0xfb0,0xfb4,0xfb8,0xfbc,0xfd0,0xfd4,0xfd8,0xfe4,0xfe8,0xff8,0xffc,0x1000,0x1004,0x10a8,0x10ac,0x10b0,0x12e8,0x12ec,0x12f0]
    fields += [0x1210,0x1214,0x1218,0x1224,0x1228,0x1238,0x123c,0x1240,0x1244,0x1074,0x1078,0x107c,0x1080,0x1084,0x1094,0x1098,0x10a0]
    fields += [0x1018,0x101c,0x1020,0x102c,0x1030,0x104c,0x1050,0x1054,0x1058,0x105c,0x12b4,0x12b8,0x12bc,0x12c0,0x12c4]
    fields += [0x138c,0x1390,0x1394,0x1398,0x139c,0x13a0,0x13a4,0x13a8,0x13b4,0x13b8,0x13bc]
    put(0x4b12f0,0x101bafc4)
    fields += [0x1124,0x1128,0x112c,0x1258,0x125c,0x1260,0x128c]
    def state():return [get(bullet+o) for o in fields]+[get(0x4db510),get(0x4db514),int.from_bytes(m.mem_read(bullet+0xc0e,2),'little')]
    def call(address,*args):
        put(stack,base+0xa10000)
        for n,value in enumerate(args):put(stack+4+n*4,value)
        m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager if address==0x417660 else bullet)
        try:m.emu_start(address,base+0xa10000,count=200000)
        except Exception as error:raise RuntimeError(f'entry={address:x} pc={m.reg_read(UC_X86_REG_EIP):x}') from error
        assert m.reg_read(UC_X86_REG_EIP)==base+0xa10000
        return m.reg_read(UC_X86_REG_EAX)
    rows=[]
    for type in range(43):
        for mode in range(138):
            n=type*4+mode;rate=(.5,1.,1.25)[n%3];color=(0,3,7,15)[n%4]
            m.mem_write(bullet,bytes(0x5000));m.mem_write(manager+0x60,bytes(0x30));put(0x4db530,manager);put(0x4db67c,player);put(manager+0x70,bullet)
            spawned.clear();m.mem_write(emitter+0x800,b'Child\0')
            put(0x4db510,1234);put(0x4db514,0)
            m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
            position=((-12.25,70.5),(185.,440.),(-210.,50.),(200.,300.),(20.,-90.),(25.,453.),(0.,200.))[type%7]
            floats(0x4d8f58,rate);put(emitter,type);put(emitter+4,color);floats(emitter+8,*position,0,1.25,.375,2.75,1.125,0)
            m.mem_write(emitter+0x364,struct.pack('<hhh',3,2,1));put(emitter+0x36c,0x23);put(emitter+0x374,38)
            if mode in (1,2):put(emitter+0x48,2);put(emitter+0x38,1 if mode==1 else 0)
            if mode in (2,3):
                at=emitter+0x28+(0x2c if mode==2 else 0);put(at+0x20,1);put(at+0x24,1)
            if mode in (4,5):
                if mode==5:put(emitter+0x28+0x20,1)
                at=emitter+0x28+(0x2c if mode==5 else 0);floats(at,-.01,-99999.,0.,0.);put(at+0x10,60);put(at+0x20,4);put(at+0x24,int(mode==5))
            if mode>=6:
                def entry(index,op,a,b,duration,concurrent=0):
                    at=emitter+0x28+index*0x2c;floats(at,a,b,0.,0.);put(at+0x10,duration);put(at+0x20,op);put(at+0x24,concurrent)
                if mode==6:entry(0,8,-.03,.013,30)
                if mode==7:
                    entry(0,1,0.,0.,0);entry(1,4,-.01,-99999.,20,1);entry(2,8,-.03,.013,30,1)
                if mode==8:entry(0,4,-.01,-99999.,1);entry(1,8,-.03,.013,7)
                if mode==9:entry(0,8,-.03,.013,1);entry(1,4,-.01,-99999.,7)
            if mode==10:put(emitter+0x48,0x80);put(emitter+0x38,9)
            if mode==11:
                put(emitter+0x48,1);put(emitter+0x74,0x80);put(emitter+0x64,9)
            if mode==12:
                put(emitter+0x48,0x10000);put(emitter+0x38,2);entry(1,8,99.,99.,60);entry(2,8,-.03,.013,30)
            if mode==13:put(emitter+0x48,0x2000000);put(emitter+0x38,3)
            if 14<=mode<24:
                opcode=0x80000000 if mode<19 else 0x4000000;variant=(mode-14)%5
                entry(0,opcode,0.,0.,(-1,0,1,7,7)[variant]);entry(1,8,-.03,.013,30,int(variant==4))
            if mode==24:entry(0,0x200000,5.,-99999.,30)
            if mode==25:
                entry(0,1,0.,0.,0);entry(1,4,-.01,-99999.,20,1);entry(2,0x200000,5.,.4,30,1);entry(3,8,-.03,.013,40,1)
            if mode==26:entry(0,0x80000000,0.,0.,7);entry(1,0x200000,5.,990.,30)
            if mode==27:entry(0,0x200000,5.,-99999.,1);entry(1,8,-.03,.013,7)
            if mode>=28:
                def bounce(index,flags,limit=2,concurrent=0):
                    entry(index,0x40,-99999.,256.,limit,concurrent);put(emitter+0x28+index*0x2c+0x14,flags);floats(emitter+0x28+index*0x2c+8,320.)
                if mode==28:bounce(0,15)
                if mode==29:bounce(0,47)
                if mode==30:bounce(0,15);entry(1,8,-.03,.013,30,1)
                if mode==31:bounce(0,47,0);entry(1,0x200000,5.,-99999.,7)
                if mode==32:entry(0,0x4000000,0.,0.,7);bounce(1,31,1);entry(2,8,-.03,.013,30)
            if 33<=mode<37:
                index=int(mode>=35)
                if index:entry(0,0x80000000,0.,0.,7)
                entry(index,0x200,0.,0.,(type+19)%43);put(emitter+0x28+index*0x2c+0x14,color|(0x8000 if mode%2==0 else 0))
            if 37<=mode<48:
                def step(index,kind,concurrent=0,duration=7,limit=2):
                    entry(index,0x10,.4,3.,duration,concurrent);at=emitter+0x28+index*0x2c;put(at+0x14,limit);put(at+0x18,kind);put(at+0x1c,19)
                if mode<44:step(0,mode-37)
                if mode==44:entry(0,0x800000,0.,0.,0);step(1,2)
                if mode==45:entry(0,0x800000,0.,0.,0);step(1,3)
                if mode==46:step(0,1,0,1,1);entry(1,0x200000,5.,-99999.,7)
                if mode==47:step(0,0);entry(1,4,-.01,-99999.,20,1);entry(2,8,-.03,.013,30,1);bounce(3,15,2,1)
            if 48<=mode<83:
                kind=mode-48 if mode<80 else 0;duration=7 if mode<80 else (-1,0,1)[mode-80]
                entry(0,0x400000,2.5,1.,duration);put(emitter+0x28+0x14,kind);entry(1,8,-.03,.013,30,int(mode%2==0))
            if mode>=83:
                def wrap(index,limit=2,flags=15,concurrent=0):entry(index,0x1000,0.,0.,limit,concurrent);put(emitter+0x28+index*0x2c+0x14,flags)
                if mode==83:wrap(0)
                if mode==84:wrap(0,0)
                if mode==85:wrap(0,2,5);entry(1,4,-.01,-99999.,15,1)
                if mode==86:entry(0,0x80000000,0.,0.,7);wrap(1)
                if mode==87:entry(0,0x400000,2.5,1.,7);wrap(1,2,15,1)
            if mode>=88:
                def hold(index,count=7,early=0):entry(index,0x100,0.,0.,count);put(emitter+0x28+index*0x2c+0x14,early)
                if mode==88:hold(0)
                if mode==89:hold(0,7,1)
                if mode==90:hold(0,19,1);entry(1,4,-.01,-99999.,15)
                if mode==91:hold(0,0)
                if mode==92:entry(0,0x80000000,0.,0.,7);hold(1,19,1)
                if mode==93:hold(0,19,1);wrap(1,2,15)
            if mode==94:entry(0,0x40000,.4,2.5,0)
            if mode==95:entry(0,0x40000,999.,-999.,0)
            if mode==96:entry(0,0x80000,.4,1.,7)
            if mode==97:entry(0,0x80000,.4,1.,7);entry(1,8,-.03,.013,30,1)
            if 98<=mode<130:entry(0,0x20000,22.5,-40.,7);put(emitter+0x28+0x14,(mode-98)|(0x100 if type%2 else 0))
            if mode==130:entry(0,0x20000,22.5,-40.,0)
            if mode==131:entry(0,0x20000,22.5,-40.,1);put(emitter+0x28+0x14,0x100)
            if mode==132:entry(0,0x20000,22.5,-40.,7);entry(1,8,-.03,.013,30,1)
            if mode==133:entry(0,0x80000000,0.,0.,7);entry(1,0x20000,22.5,-40.,7)
            if mode>=134:
                index=int(mode!=134)
                if mode==135:entry(0,0x80000000,0.,0.,7)
                if mode==136:entry(0,4,-.01,-99999.,7)
                if mode==137:entry(0,0x20000,22.5,-40.,7)
                entry(index,0x1000000,.125,-2.5,-99,int(mode==136));at=emitter+0x28+index*44;floats(at+8,3.25,-999.);put(at+0x14,250);put(at+0x18,-1000);put(at+0x1c,31415);put(at+0x28,emitter+0x800)
            spawn_status=call(0x417660,emitter,1,0,0);before=state();before_spawned=spawned[:];frames=[]
            put(bullet+0x54,sprite);floats(sprite+0x34,12,20);put(bullet+0x24,27+type)
            for frame in range(64):
                # Reapply the same controlled sprite boundary as the WASM fixture.
                # An appearance switch clears this pointer during the current update.
                put(bullet+0x54,sprite);put(bullet+0x4d4,int(frame>=6));status=call(0x416700)
                frames.append(dict(status=status,state=state(),spawned=spawned[:]))
                if status:break
                # Manager lifetime tick follows the single-bullet update.
                timer=bullet+0x13c0;current=get(timer+4);fraction=struct.unpack('<f',m.mem_read(timer+8,4))[0];fraction=struct.unpack('<f',struct.pack('<f',fraction+rate))[0]
                put(timer,current);put(timer+4,int(fraction));floats(timer+8,fraction)
            rows.append(dict(type=type,color=color,mode=mode,rate=rate,spawnStatus=spawn_status,spawn=before,spawned=before_spawned,frames=frames))
    out=ROOT/'artifacts/th14/bullet-state-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),fields=fields,normalizerDllSha256=hashlib.sha256(dll.data).hexdigest(),normalizerAddress="0x101bafc4",cases=rows),separators=(',',':'))+'\n',encoding='utf-8')
    print(f'{len(rows)} TH14 bullet lifecycle timelines, {sum(len(r["frames"]) for r in rows)} frame states.')
if __name__=='__main__':main()
