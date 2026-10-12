"""Execute retail456050 allocation/restore and455ed0 recording activation.

Allocation, input/FPS storage and raw keyboard reset are controlled services;
all stage header stores and the28-word snapshot copy execute original code.
"""
import hashlib, importlib, itertools, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
    img=importlib.import_module('th-anm-handlers').handlers(14)[0]
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,base,size,raw,n in img.sections:
        start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
    base=0x70000000;m.mem_map(base,0x100000)
    manager,record,player,inputs,fps,stack=base+0x1000,base+0x2000,base+0x10000,base+0x40000,base+0x50000,base+0xff000
    def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
    def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
    calls=[]
    def hook(uc,a,n,u):
        if a not in (0x4854af,0x48f980,0x456630,0x4564e0,0x456170):return
        sp=uc.reg_read(UC_X86_REG_ESP);result=0;pop=0
        if a==0x4854af:assert get(sp+4)==0xdc;result=record
        elif a==0x48f980:
            dest,value,size=get(sp+4),get(sp+8),get(sp+12);assert size==0xdc;m.mem_write(dest,bytes([value&255])*size);result=dest
        elif a==0x456630:result=inputs;pop=4
        elif a==0x4564e0:result=fps;pop=4
        calls.append(hex(a));uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_ESP,sp+4+pop);uc.reg_write(UC_X86_REG_EIP,get(sp))
    m.hook_add(UC_HOOK_CODE,hook)
    def run(address):
        put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(address,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
    rows=[]
    for stage,seed in itertools.product(range(2,7),(0,0x9630,0xffff)):
        m.mem_write(manager,bytes(0x320));put(0x4db688,manager);put(0x4db67c,player);put(0x4f58a4,stage);put(0x4d9658,0)
        before=[(stage*0x197731+i*0x10204081)&0xffffffff for i in range(28)]
        activated=[(v+14404+i*97)&0xffffffff for i,v in enumerate(before)]
        m.mem_write(0x4f5828,struct.pack('<28I',*before));put(0x4db510,seed);put(0x4db508,0xabcd);put(0x4db514,97);put(0x4db50c,123)
        calls.clear();run(0x456050)
        assert get(manager+stage*4+0x20)==record
        assert bytes(m.mem_read(record+0x14,0x70))==bytes(0x70),'record allocation does not snapshot globals'
        assert get(0x4db514)==0 and get(0x4db50c)==123
        # This mutation represents the live handoff interval, not a simulation
        # of its combat callbacks.455ed0 itself chooses the later snapshot.
        m.mem_write(0x4f5828,struct.pack('<28I',*activated));put(player+0x5ec,-4096+stage*128);put(player+0x5f0,51200-stage*128);put(player+0x184b0,stage%2)
        run(0x455ed0);header=bytes(m.mem_read(record,0xdc))
        assert header[0x14:0x84]==struct.pack('<28I',*activated)
        assert get(manager+0x218)==stage and get(manager+0x210)==0
        put(manager+0x10,1);put(manager+stage*40+0xd8,record);m.mem_write(0x4f5828,struct.pack('<28I',*before));run(0x456050)
        restored=[get(0x4f5828+i*4) for i in range(28)];assert restored==activated
        rows.append(dict(stage=stage,seed=seed,beforeGlobals=before,activationGlobals=activated,restoredBeforeWait=restored,header=header.hex(),controlledCalls=calls.copy()))
    proof=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,scope='Whole retail456050 record allocation and playback restore plus455ed0 recording activation. Original28-word/position/weapon/header stores execute; allocator/memset/input/FPS storage and keyboard reset controlled. Synthetic globals differ across a controlled handoff boundary: allocation leaves snapshot zero, activation copies later values, playback restores those values before the wait. Does not simulate the native handoff callbacks or prove complete recorder/replay, combat or rendering equivalence.')
    (ROOT/'artifacts/th14/replay-start-native.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(f'PASS {len(rows)} native recording allocation/activation/playback snapshot routes')
if __name__=='__main__':main()
