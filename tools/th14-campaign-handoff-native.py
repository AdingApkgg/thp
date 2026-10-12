"""Execute the exact retail combo tail/factory and all following inactive item ticks.

Input is the preserved live campaign trace, not generated expected gameplay.
ANM/resource/popup/audio deliveries are controlled; score, combo, allocation,
polar math, delay, movement, timers and pool reset execute retail instructions.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x70000000
ITEMS, BULLETS, PLAYER, GAME, BOMB, HEADER, STACK = [BASE+n for n in
    (0, 0xe00000, 0x1800000, 0x1820000, 0x1830000, 0x1840000, 0x18ff000)]
STOP = BASE+0x18fe000
STRIDE = 0xc18

def main():
    path = ROOT/'artifacts/th14/campaign-handoff/rows.json'
    trace_bytes = path.read_bytes()
    trace = json.loads(trace_bytes)
    before = next(r for r in trace['records'] if r['frame'] == 11810)
    birth = next(r for r in trace['records'] if r['frame'] == 11811)
    img, _, _ = importlib.import_module('th-anm-handlers').handlers(14)
    m = Uc(UC_ARCH_X86, UC_MODE_32)
    for _, b, size, raw, n in img.sections:
        start = b & ~4095
        m.mem_map(start, ((b+size+4095)&~4095)-start)
        m.mem_write(b, img.data[raw:raw+n])
    m.mem_map(BASE, 0x1900000)
    def put(p,v): m.mem_write(p, struct.pack('<I',v&0xffffffff))
    def get(p): return struct.unpack('<I',m.mem_read(p,4))[0]
    def bits(v): return struct.unpack('<I',struct.pack('<f',v))[0]
    events = []
    def boundary(uc,a,size,user):
        sp = m.reg_read(UC_X86_REG_ESP)
        if a == 0x48f980:
            m.mem_write(get(sp+4),bytes(get(sp+12)))
            m.reg_write(UC_X86_REG_EAX,get(sp+4))
        elif a == 0x40af00:
            vm = get(sp+4)
            m.mem_write(vm,bytes(0x5cc));put(vm+0x18,1)
            m.mem_write(vm+0x4aa,struct.pack('<h',get(sp+8)))
        elif a == 0x47f140: assert get(sp+4) == 0
        elif a == 0x47ed10: m.reg_write(UC_X86_REG_EAX,0)
        elif a == 0x4397b0:
            p=get(sp+8);events.append(dict(kind='spawn',type=get(sp+4),position=[get(p+n) for n in (0,4,8)],delay=get(sp+24)))
        elif a == 0x458000:
            events.append(dict(kind='popup',amount=get(sp+8),color=get(sp+12),multiplier=m.reg_read(UC_X86_REG_XMM3)&0xffffffff))
    for a, cleanup in ((0x48f980,0),(0x40af00,8),(0x46fe50,0),
            (0x46e470,4),(0x47f140,8),(0x47ed10,28),(0x46e3d0,8),(0x458000,12)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    # Observe the full original item factory; do not replace it.
    m.hook_add(UC_HOOK_CODE,boundary,begin=0x4397b0,end=0x4397b0)
    def call(a):
        put(STACK,STOP);m.reg_write(UC_X86_REG_ESP,STACK)
        m.reg_write(UC_X86_REG_ECX,ITEMS)
        m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0)
        m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
        m.emu_start(a,STOP,count=500000)
        assert m.reg_read(UC_X86_REG_EIP)==STOP
    call(0x41d8c0)
    for p,v in ((0x4db660,ITEMS),(0x4db530,BULLETS),(0x4db67c,PLAYER),
        (0x4db550,GAME),(0x4db52c,BOMB),(0x4db53c,GAME+0x800),
        (0x4d8f58,bits(1)),(0x4f5830,before['score']),
        (0x4f5878,before['combo'][0]),(0x4f5880,before['combo'][1]),
        (0x4f5884,before['combo'][2]),(0x4f5894,before['combo'][6]),
        (PLAYER+0x5e4,bits(400)),(PLAYER+0x684,1),(PLAYER+0x688,HEADER),
        (HEADER+8,bits(8))): put(p,v)
    for n,v in enumerate(before['combo'][3:6]): put(0x4f5888+4*n,v)
    for offset in (0x1835c,0x18374,0x1838c):
        m.mem_write(PLAYER+offset,struct.pack('<5f',1,1,0,-1,-1))
    m.reg_write(UC_X86_REG_ESP,STACK-0x100)
    m.reg_write(UC_X86_REG_XMM4,0);m.reg_write(UC_X86_REG_XMM5,bits(2))
    m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x438dad,0x43907b,count=10000)
    assert m.reg_read(UC_X86_REG_EIP)==0x43907b
    assert get(0x4f5830)==birth['score'], (get(0x4f5830),birth['score'])
    assert [get(p) for p in (0x4f5878,0x4f5880,0x4f5884)]==birth['combo'][:3]
    assert get(0x4f5894)==birth['combo'][6]
    def pool():
        result=[3]
        for n in range(4696):
            p=ITEMS+0x14+n*STRIDE
            if not get(p+0xbf0):continue
            result += [n]+[get(p+o) for o in (0xbf0,0xbf4,0xbf8,0xba8,0xbfc,0xc00,
                0xbac,0xbb0,0xbb4,0xbb8,0xbbc,0xbc0,0xbc8,0xbcc,0xbd0)]
        return result
    compared=[]
    for row in trace['records']:
        if not 11811<=row['frame']<=11954:continue
        if row['frame']!=11811:call(0x438550)
        assert pool()==row['pools'][3],f"frame {row['frame']} native item state"
        compared.append(row['frame'])
    assert len(compared)==144
    # The activation path resets again, which removes this transient item.
    call(0x41d8c0)
    activated=next(r for r in trace['records'] if r['frame']==11955)
    replay_activated=next(r for r in trace['replays'] if r['frame']==11955)
    assert activated['active'] and replay_activated['active']
    assert pool()==activated['pools'][3]==replay_activated['pools'][3]
    report=dict(passed=True,completeGame=False,nativeEquivalent=False,
        nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),
        traceSha256=hashlib.sha256(trace_bytes).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        frameBefore=before['frame'],inputCombo=before['combo'],inputScore=before['score'],
        settledScore=birth['score'],scoreDelta=birth['score']-before['score'],
        events=events,itemFramesCompared=compared,activationFrame=11955,
        scope='Exact recorded Reimu A Normal stage1-to-stage2 inactive combo input; actual retail438dad..43907b calls full4397b0 factory, then143 full438550 ticks compare every explicit item word. Retail41d8c0 reset yields the observed activation empty pool; reset timing is established separately by activation disassembly. Resource/ANM/popup/audio delivery boundaries are controlled. Does not prove full native campaign, visuals, inactive callbacks as a whole, or the other handoffs.')
    out=ROOT/'docs/porting/th14-campaign-handoff-native-verified-oct11.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f"PASS: exact native score +{report['scoreDelta']}; full native factory;144 inactive item states; activation reset.")

if __name__=='__main__': main()
