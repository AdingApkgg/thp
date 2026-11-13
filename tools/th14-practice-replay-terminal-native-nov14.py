"""Retail terminal dispatch for a supplied short replay, plus countdown cases.

Controlled linked callbacks, decoded replay input, ANM factories/capture and
audio delivery. No original game process or real enemy score is claimed.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, struct, sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/tmp/th14-analysis-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--decoded',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
O=args.output.resolve()
assert O.is_relative_to(R/'artifacts/th14') and not O.exists(); O.mkdir(parents=True)
sys.path.insert(0,str(R/'tools'))
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,raw,n in im.sections:
    page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,im.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x100000)
outer,replay,menu,control,game,front,header,inputs,rates,stack,stop,tail=[B+n for n in (0x1000,0x3000,0x5000,0x6000,0x7000,0x8000,0x9000,0xa000,0x20000,0xf0000,0xff000,0xff100)]
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
events=[]
services={0x448bf0:0,0x44c1a0:12,0x47f140:8,0x46ef90:12}
def hook(uc,pc,size,data):
    if pc not in services and pc!=tail:return
    sp=uc.reg_read(UC_X86_REG_ESP);result=1
    if pc==tail:
        events.append(dict(kind='later-callback',owner=uc.reg_read(UC_X86_REG_ECX),flags=get(control+0x80),cursor=get(replay+40*stage_number+0xdc)))
    elif pc==0x44c1a0:
        dest=get(sp+4);script=get(sp+8);assert script==131
        put(dest,123);result=dest;events.append(dict(kind='menu-factory',script=script))
    elif pc==0x448bf0:events.append(dict(kind='capture-boundary'))
    uc.reg_write(UC_X86_REG_EAX,result);uc.reg_write(UC_X86_REG_ESP,sp+4+services.get(pc,0));uc.reg_write(UC_X86_REG_EIP,get(sp))
m.hook_add(UC_HOOK_CODE,hook)
def call(entry,owner=0,args=()):
    put(stack,stop)
    for i,v in enumerate(args):put(stack+4+i*4,v)
    m.reg_write(UC_X86_REG_ECX,owner);m.reg_write(UC_X86_REG_ESP,stack)
    m.emu_start(entry,stop,count=100000)
    assert m.reg_read(UC_X86_REG_EIP)==stop,hex(m.reg_read(UC_X86_REG_EIP))
    return m.reg_read(UC_X86_REG_EAX)
raw=args.decoded.read_bytes()
assert len(raw)>=0x170 and struct.unpack_from('<I',raw,0x78)[0]>=1
stage_number=struct.unpack_from('<H',raw,0x94)[0]
frames,payload=struct.unpack_from('<II',raw,0x98)
assert 1<=stage_number<=7 and 1<=frames<=0x1000 and payload>=frames*6+(frames+29)//30
assert len(raw)>=0x170+payload
terminal_frame=frames-1
assert raw[0x170+terminal_frame*6:0x170+frames*6]==b'\xff'*6
rows=[]
for terminal in (True,False):
 for initial_flags in (0,2,0x10):
  for enabled in (False,True):
    m.mem_write(B,bytes(0xef000));m.mem_write(0x4d6878,bytes(0x240));m.mem_write(0x4f95dc,bytes(0x720));m.mem_write(0x4f5815,b'\0')
    for p,v in [(0x4db51c,outer),(0x4db558,control),(0x4db678,menu),(0x4db550,game),(game+0x2a4,front),(control+0x80,initial_flags),(0x4d8f58,0x3f800000),(replay+0x218,stage_number),(replay+0x210,terminal_frame)]:put(p,v)
    m.mem_write(header,raw[0x94:0x170]);m.mem_write(inputs,raw[0x170:0x170+frames*6])
    m.mem_write(rates,raw[0x170+frames*6:0x170+payload])
    if not terminal:m.mem_write(inputs+terminal_frame*6,bytes(6))
    sheet=replay+40*stage_number
    for off,v in [(0xd8,header),(0xcc,inputs+terminal_frame*6),(0xd4,rates),(0xdc,terminal_frame)]:put(sheet+off,v)
    for i,(priority,body,owner,on) in enumerate([(12,0x455e50,replay,True),(18,tail,B+0xd000,enabled),(21,tail,B+0xe000,enabled)]):
        node=B+0x10000+i*0x100
        for off,v in [(0,priority),(4,3 if on else 1),(8,body),(0x14,node),(0x24,owner)]:put(node+off,v)
        call(0x401120,args=(node,priority))
    events.clear();result=call(0x401280,outer)
    tails=[e for e in events if e['kind']=='later-callback']
    assert len(tails)==(2 if enabled else 0),events
    assert get(sheet+0xdc)==(terminal_frame if terminal else frames), dict(terminal=terminal,enabled=enabled,cursor=get(sheet+0xdc),events=events,mainReturn=result)
    assert get(control+0x80)==(initial_flags|0x10 if terminal else initial_flags)
    assert get(menu+4)==(2 if terminal else 0)
    assert len([e for e in events if e['kind']=='menu-factory'])==int(terminal)
    rows.append(dict(terminal=terminal,initialControlFlags=initial_flags,laterCallbacksEnabled=enabled,mainReturn=result,replayCursor=get(sheet+0xdc),menuState=get(menu+4),finalControlFlags=get(control+0x80),events=list(events)))
phase_rows=[]
entity,spell,special,manager=[B+n for n in (0x30000,0x38000,0x39000,0x3a000)]
for remaining in (1,59,60,61,767,768,769,6000,6001):
    elapsed=10800-remaining
    m.mem_write(entity,bytes(0x6000))
    put(0x4db550,game);put(0x4db534,spell);put(0x4db52c,special);put(0x4db544,manager)
    put(entity+0x5164,200);put(entity+0x5244,0x800000)
    for n in range(8):
        for off,value in enumerate((-1,-1,0x100+n,0x200+n)):put(entity+0x525c+n*16+off*4,value)
    put(entity+0x525c,100);put(entity+0x5260,10800)
    for off,value in ((0x14ac,elapsed-1),(0x14b0,elapsed),(0x14b4,struct.unpack('<I',struct.pack('<f',elapsed))[0]),(0x14b8,0x4d8f58),(0x14bc,1)):
        put(entity+off,value)
    put(game+0x19c,777);put(game+0x1a0,888);put(spell+0x7c,0);put(spell+0x28,59);put(spell+0x80,999)
    put(special+0x40,0);put(manager+0x18,123)
    inputs_row=[200,elapsed,0x800000,0,59,0,1]+[get(entity+0x525c+4*n) for n in range(32)]
    result=call(0x42bf70,entity)
    output=[result,get(entity+0x5164),get(entity+0x516c),get(entity+0x5174),get(entity+0x5244),
            *[get(entity+off) if off!=0x14b8 else int(get(entity+off)!=0) for off in range(0x14ac,0x14c0,4)],
            get(game+0x19c),get(game+0x1a0),get(spell+0x7c),get(spell+0x80),get(manager+0x18),
            *[get(entity+0x525c+16*n) for n in range(8)]]
    expected=[min(remaining//60,99),99 if remaining//60>99 else remaining%60*100//60]
    assert output[10:12]==expected,(remaining,output)
    phase_rows.append(dict(remaining=remaining,inputs=inputs_row,result=output))
report=dict(passed=True,cases=len(rows),rows=rows,countdownCases=phase_rows,
    countdownInputsAreControlled=True,actualScreenshotCountdownStateAccepted=False,
    originalTimedPhaseEntry='42bf70',stage=stage_number,frames=frames,terminalFrame=terminal_frame,originalExecutableSha256=sha(im.data),toolSha256=sha(Path(__file__).read_bytes()),decodedInputSha256=sha(raw),
    executedOriginalBodies=['401120 callback insertion','401280 complete update traversal','455e50 Replay wrapper','455180 complete input reader','448ef0 complete replay-end entry','4373b0 sound-pause with null interfaces'],
    controlledBoundaries=['448bf0 capture','44c1a0 ANM factory','47f140 ANM interrupt','46ef90 audio request','later callback bodies return 1'],
    instructionBytesPatched=0,laterCallbacksContinueAfterTerminalMarker=True,actualEnemyOrPlayerScoreCompared=False,originalProcessPlaybackAccepted=False,newAudioDeviceStarted=False,productionChanged=False,completeGame=False)
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ('rows','countdownCases')}))
