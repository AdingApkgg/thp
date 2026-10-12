"""Decode the actual campaign with retail code, restore stage2, then tick items.

This complements the live handoff proof; it does not infer native replay state
from live/recorded equality. CRT and resource/audio/ANM delivery are controlled.
"""
import hashlib, importlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[1]
BASE=0x70000000
ITEMS,BULLETS,PLAYER,GAME,BOMB,SHEET,STACK=[BASE+n for n in
    (0,0xe00000,0x1800000,0x1820000,0x1830000,0x1840000,0x18ff000)]
STOP=BASE+0x18fe000
SRC,DST,MANAGER,HEADER,HEAP=[BASE+n for n in
    (0x1900000,0x1a00000,0x1b00000,0x1b01000,0x1c00000)]

def main():
    trace_path='artifacts/th14/campaign-handoffs-all-oct11/rows.json'
    replay_path='artifacts/th14/campaign-replay/reimu-a-normal-pools-oct11/campaign.rpy'
    trace_bytes=(ROOT/trace_path).read_bytes();trace=json.loads(trace_bytes)
    target_stage=int(__import__('sys').argv[1]);assert 2<=target_stage<=6
    group=next(g for g in trace['groups'] if g['stage']==target_stage)
    start_frame=group['transitionFrame']
    trace={kind:[dict(r,pools=[[],[],[],r.get('items',[])]) for r in group[kind]] for kind in ('records','replays')}

    data=(ROOT/replay_path).read_bytes();assert data[:6]==b't13r\x02\x00'
    packed,unpacked=struct.unpack_from('<II',data,0x1c)
    assert 0x24+packed==len(data) and unpacked<0x100000
    img=importlib.import_module('th-anm-handlers').handlers(14)[0]
    m=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,b,size,raw,n in img.sections:
        start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start)
        m.mem_write(b,img.data[raw:raw+n])
    m.mem_map(BASE,0x2400000)
    put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
    get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
    bits=lambda v:struct.unpack('<I',struct.pack('<f',v))[0]
    heap=[HEAP];events=[]
    def boundary(uc,a,size,u):
        sp=m.reg_read(UC_X86_REG_ESP);result=0
        if a==0x485540:
            n=get(sp+4);result=heap[0];heap[0]+=(n+15)&~15
            assert heap[0]<BASE+0x2400000;m.mem_write(result,bytes(n))
        elif a==0x487620:
            result=get(sp+4);m.mem_write(result,bytes(m.mem_read(get(sp+8),get(sp+12))))
        elif a==0x48f980:
            result=get(sp+4);m.mem_write(result,bytes([get(sp+8)&255])*get(sp+12))
        elif a==0x40af00:
            vm=get(sp+4);m.mem_write(vm,bytes(0x5cc));put(vm+0x18,1)
            m.mem_write(vm+0x4aa,struct.pack('<h',get(sp+8)))
        elif a==0x4397b0:events.append(dict(kind='spawn',type=get(sp+4)))
        elif a==0x458000:events.append(dict(kind='popup',amount=get(sp+8)))
        if a in (0x485540,0x487620,0x4855d2):
            uc.reg_write(UC_X86_REG_EAX,result)
            uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EIP,get(sp))
    for a in (0x485540,0x487620,0x4855d2):m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    for a,pop in ((0x48f980,0),(0x40af00,8),(0x46fe50,0),(0x46e470,4),
                  (0x47f140,8),(0x47ed10,28),(0x46e3d0,8),(0x458000,12)):
        m.mem_write(a,b'\xc2'+struct.pack('<H',pop) if pop else b'\xc3')
        m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
    m.hook_add(UC_HOOK_CODE,boundary,begin=0x4397b0,end=0x4397b0)
    def call(a,ecx=ITEMS,edx=0,args=(),count=500000):
        put(STACK,STOP)
        for i,v in enumerate(args):put(STACK+4+i*4,v)
        m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,ecx)
        m.reg_write(UC_X86_REG_EDX,edx);m.reg_write(UC_X86_REG_FPCW,0x37f)
        m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
        m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(a,STOP,count=count)
        assert m.reg_read(UC_X86_REG_EIP)==STOP,hex(m.reg_read(UC_X86_REG_EIP))
    m.mem_write(SRC,data[0x24:]);m.mem_write(0x4f36c8,bytes(8192))
    call(0x4028e0,SRC,packed,(0x5c,0xe1,0x400,packed),10000000)
    call(0x4028e0,SRC,packed,(0x7d,0x3a,0x100,packed),10000000)
    call(0x465840,SRC,packed,(DST,unpacked),100000000)
    decoded=bytes(m.mem_read(DST,unpacked));headers={};offset=0x94
    while offset<len(decoded):
        stage=struct.unpack_from('<H',decoded,offset)[0]
        payload=struct.unpack_from('<I',decoded,offset+8)[0]
        assert 1<=stage<=6 and stage not in headers
        headers[stage]=decoded[offset:offset+0xdc];offset+=0xdc+payload
    assert offset==len(decoded) and sorted(headers)==list(range(1,7))
    before=next(r for r in trace['records'] if r['frame']==start_frame+6)
    first=next(r for r in trace['replays'] if not r['active'])
    # Retail cleanup4363e4 resets items before existing-controller435f32 calls456050.
    call(0x41d8c0)
    for p,v in ((0x4db660,ITEMS),(0x4db530,BULLETS),(0x4db67c,PLAYER),
        (0x4db550,GAME),(0x4db52c,BOMB),(0x4db53c,GAME+0x800),
        (0x4d8f58,bits(1)),(0x4f5830,before['score']),
        (0x4f5878,before['combo'][0]),(0x4f5880,before['combo'][1]),
        (0x4f5884,before['combo'][2]),(0x4f5894,before['combo'][6]),
        (PLAYER+0x5e4,bits(400)),(PLAYER+0x684,1),(PLAYER+0x688,SHEET),
        (SHEET+8,bits(8))):put(p,v)
    for n,v in enumerate(before['combo'][3:6]):put(0x4f5888+4*n,v)
    for offset in (0x1835c,0x18374,0x1838c):
        m.mem_write(PLAYER+offset,struct.pack('<5f',1,1,0,-1,-1))
    m.mem_write(HEADER,headers[target_stage]);put(MANAGER+0x10,1)
    put(MANAGER+target_stage*40+0xd8,HEADER);put(0x4db688,MANAGER);put(0x4f58a4,target_stage)
    put(0x4db50c,123);put(0x4db514,97)
    # Execute the existing-controller branch itself, including its intact456050 call.
    service=BASE+0x1b02000
    put(0x4db69c,service);put(service+4,service+0x1000);put(0x4f58b8,2)
    for address in (0x40d8a0,0x42eb30):m.mem_write(address,b'\xb8\x01\x00\x00\x00\xc3')
    put(STACK,STOP);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_EBX,GAME)
    m.emu_start(0x435ed0,0x435f50,count=10000)
    assert m.reg_read(UC_X86_REG_EIP)==0x435f50
    assert bytes(m.mem_read(0x4f5828,0x70))==headers[target_stage][0x14:0x84]
    restored_snapshot=bytes(m.mem_read(0x4f5828,0x70))
    header_path=f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-header.bin'
    (ROOT/header_path).write_bytes(headers[target_stage])
    restored_score=get(0x4f5830)
    assert restored_score==first['score'] # Zero score lead is valid when this handoff has no combo settlement.
    def pool():
        result=[3]
        for n in range(4696):
            p=ITEMS+0x14+n*0xc18
            if get(p+0xbf0):result += [n]+[get(p+o) for o in
                (0xbf0,0xbf4,0xbf8,0xba8,0xbfc,0xc00,0xbac,0xbb0,0xbb4,
                 0xbb8,0xbbc,0xbc0,0xbc8,0xbcc,0xbd0)]
        return result
    combo_addresses=(0x4f5878,0x4f5880,0x4f5884,0x4f5888,0x4f588c,0x4f5890,0x4f5894)
    compared=[]
    for row in trace['replays']:
        if row['active']:continue
        call(0x438550)
        assert get(0x4f5830)==row['score'],row['frame']
        assert [get(p) for p in combo_addresses]==row['combo'],row['frame']
        assert pool()==row['pools'][3],row['frame']
        compared.append(row['frame'])
    assert compared and len(compared)==151 and not events,(len(compared),events)
    report=dict(passed=True,completeGame=False,nativeEquivalent=False,
        nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),
        replayPath=replay_path,replaySha256=hashlib.sha256(data).hexdigest(),
        decodedBytes=len(decoded),decodedSha256=hashlib.sha256(decoded).hexdigest(),
        controlFlags=2,restoredSnapshotHex=restored_snapshot.hex(),stageHeaderPath=header_path,stage=target_stage,stageHeaderSha256=hashlib.sha256(headers[target_stage]).hexdigest(),
        tracePath=trace_path,traceSha256=hashlib.sha256(trace_bytes).hexdigest(),
        liveBeforeScore=before['score'],restoredReplayScore=restored_score,
        comparedFrames=compared,events=events,
        toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Actual saved six-stage diagnostic campaign fully decoded by retail4028e0/465840. Original435ed0..435f50 existing-controller branch calls complete456050 and restores selected actual stage header, then151 complete438550 ticks match every explicit item word, score and seven combo words of the production inactive replay trace. Cleanup-before-restore order follows original4363e4 disassembly; unrelated whole native lifecycle not executed. CRT allocation/copy/free/memset,40d8a0/42eb30 world/HUD setup and ANM/resource/popup/audio boundaries controlled. This confirms the first handoff difference is expected snapshot timing, not whole combat, native survival or GPU equality. Source campaign uses diagnostic invulnerability; this native callback test injects no gameplay invulnerability.')
    (ROOT/f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-restore-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(f'PASS native actual stage{target_stage} restore {before["score"]}→{restored_score}; {len(compared)} replay item/combo/score ticks; no spawn')

if __name__=='__main__':main()
