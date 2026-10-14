"""Read original Supervisor flag writers and execute WindowProc/worker predicates.

No Native process, window, D3D service, whole loader or cancellation adapter is
run. Unknown 0x100 writer/meaning remains unknown, not a guessed lifecycle bit.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'tools/th14-loading-lifecycle-evidence-check.py'
OUTPUT=ROOT/'docs/porting/th14-loader-supervisor-flags-verified-oct14.json'
FLAGS=0x4d9684
STACK,RETURN=0x7ff000,0x710000


def main():
    spec=importlib.util.spec_from_file_location('original_image',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    image=helper.Image();md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    def bind(path):
        data=path.read_bytes()
        return dict(path=path.relative_to(ROOT).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    def unit(address,count):
        data=image.bytes(address,count)
        return dict(address=hex(address),bytes=count,hex=data.hex(),sha256=hashlib.sha256(data).hexdigest(),
                    instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str) for i in md.disasm(data,address)])
    def put(uc,address,value):uc.mem_write(address,struct.pack('<I',value&0xffffffff))
    def get(uc,address):return struct.unpack('<I',uc.mem_read(address,4))[0]
    def machine():
        uc=image.machine();put(uc,STACK,RETURN);uc.reg_write(UC_X86_REG_ESP,STACK);return uc
    def run(uc,entry,stops):
        visited=[]
        def stop(guest,address,size,unused):
            if address in stops:visited.append(address);guest.emu_stop()
        handle=uc.hook_add(UC_HOOK_CODE,stop);uc.emu_start(entry,0,count=200);uc.hook_del(handle)
        assert len(visited)==1 and uc.reg_read(UC_X86_REG_EIP)==visited[0]
        return visited[0]

    # Scan every raw .text occurrence, then accept only a decoded instruction
    # containing that exact absolute memory operand. This does not resolve
    # computed aliases, overlapping/block writes or dynamic guest modifications.
    section=next(s for s in image.sections if s['rva']==0x1000)
    raw=image.data[section['raw']:section['raw']+section['rawSize']]
    base=image.base+section['rva'];instructions={};raw_occurrences={}
    for wanted in range(FLAGS,FLAGS+4):
        needle=struct.pack('<I',wanted);at=0;hits=[]
        while (at:=raw.find(needle,at))>=0:hits.append(base+at);at+=4
        raw_occurrences[hex(wanted)]=[hex(a) for a in hits]
        for hit in hits:
            for start in range(hit-11,hit+1):
                ins=next(md.disasm(image.bytes(start,15),start,count=1),None)
                if ins and ins.address<=hit and ins.address+ins.size>=hit+4:
                    operands=[o for o in ins.operands if o.type==X86_OP_MEM and o.mem.disp==wanted and not o.mem.base and not o.mem.index]
                    if operands:instructions[ins.address]=(ins,any(o.access&2 for o in operands))
    refs=[dict(address=hex(a),mnemonic=ins.mnemonic,operands=ins.op_str,hex=bytes(ins.bytes).hex(),
               writes=bool(writes)) for a,(ins,writes) in sorted(instructions.items())]
    assert len(refs)==50 and all(not raw_occurrences[hex(a)] for a in range(FLAGS+1,FLAGS+4))
    assert next(r for r in refs if r['address']=='0x469fbc')['writes']

    table=list(struct.unpack('<5I',image.bytes(0x46a114,20)))
    message_map=list(image.bytes(0x46a128,24))
    assert table==[0x469f15,0x469fac,0x469ee4,0x469eef,0x46a100]
    assert table[message_map[0x10-5]]==0x469fac
    assert table[message_map[5-5]]==0x469f15
    assert image.bytes(0x46af3c,7)==bytes.fromhex('c745d8b09e4600')
    assert image.imports()[0x4b1208]['function']=='RegisterClassA'
    assert image.imports()[0x4b1264]['function']=='DefWindowProcA'
    dispatch=[]
    for message in range(5,0x1d):
        uc=machine()
        for offset,value in ((4,0),(8,message),(12,0),(16,0)):put(uc,STACK+offset,value)
        reached=run(uc,0x469eb0,set(table))
        assert reached==table[message_map[message-5]]
        dispatch.append(dict(message=hex(message),target=hex(reached)))

    close=[]
    inputs=[0,1,0x10,0x40,0x80,0x100,0x180,0x2000,0x4240,0xffffffff]
    for flags in inputs:
        uc=machine();put(uc,FLAGS,flags)
        for offset,value in ((4,0),(8,0x10),(12,0),(16,0)):put(uc,STACK+offset,value)
        assert run(uc,0x469eb0,{RETURN})==RETURN
        expected=(flags&~0x100)|0x80
        assert get(uc,FLAGS)==expected&0xffffffff
        assert bytes(uc.mem_read(0x469eb0,0x3a))==image.bytes(0x469eb0,0x3a)
        assert bytes(uc.mem_read(0x469fac,0x1f))==image.bytes(0x469fac,0x1f)
        close.append(dict(before=hex(flags),after=hex(get(uc,FLAGS)),originalCodeUnmodified=True))

    reset=[]
    for flags in inputs:
        uc=machine();put(uc,FLAGS,flags)
        assert run(uc,0x469520,{0x46952a})==0x46952a
        assert get(uc,FLAGS)==flags&~0x180
        reset.append(dict(before=hex(flags),after=hex(get(uc,FLAGS))))
    wait=[]
    for flags in [0,0x10,0x40,0x80,0x100,0x180,0x2000,0x4240,0xffffffff]:
        uc=machine();put(uc,FLAGS,flags)
        reached=run(uc,0x435ae0,{0x435af0,0x435f6f})
        assert (reached==0x435f6f)==bool(flags&0x180)
        wait.append(dict(flags=hex(flags),aborts=bool(flags&0x180),reached=hex(reached)))

    report=dict(schema='th14-loader-supervisor-flags-evidence-v1',diagnosticEvidenceVerified=True,
                productionChanged=False,productionVerified=False,nativeEquivalent=False,completeGame=False,
                executableSha256=helper.EXPECTED_EXE_SHA,supervisor='0x4d8f60',flagsAddress=hex(FLAGS),flagsOffset='0x724',
                sourceBindings=[bind(HELPER),bind(Path(__file__))],absoluteReferenceByteScan=dict(
                    rawOccurrences=raw_occurrences,instructions=refs,
                    scope='Every original .text byte scanned for four absolute flag-byte addresses, decoded exact absolute memory operands only. Does not exclude computed aliases, overlapping writes, initialization copies or dynamic writers.'),
                windowProcedure=dict(entry='0x469eb0',registeredOriginalPointerStore='0x46af3c',registerClassCall='0x46af5e',
                    tableAddress='0x46a114',tableHex=image.bytes(0x46a114,20).hex(),mapAddress='0x46a128',mapHex=image.bytes(0x46a128,24).hex(),dispatchCases=dispatch),
                originalWindowCloseCases=close,originalInitializationClearCases=reset,originalWaitMaskCases=wait,
                originalUnits=[unit(a,n) for a,n in ((0x46af3c,40),(0x469eb0,0x34),(0x469fac,0x1f),
                    (0x469f15,0x3a),(0x469520,10),(0x435acf,0x40),(0x469aec,0x2d),
                    (0x46c134,0x3b),(0x46c264,0x3b))],
                officialMessageDefinitions=[dict(name='WM_CLOSE',value='0x10',source='https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-close'),
                    dict(name='WM_SIZE',value='0x5',source='https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-size')],
                conclusions=dict(
                    bit80='Actual registered WindowProc WM_CLOSE branch sets0x80 and clears0x100; ten full unmodified WindowProc cases execute that branch without host services.',
                    bit100='Checked by wait-mask and explicitly cleared by WM_CLOSE/initialization. No positive-setting absolute writer was identified in this bounded original .text scan; meaning remains unknown.',
                    deviceAndResize='WM_SIZE table targets469f15 and uses separate window-state4f7a54. The inspected device/reset continuation469b12 sets Supervisor0x10. Neither inspected path establishes0x80/0x100 as resize or device-lost bits.',
                    portMapping='An actual SDL/native window-quit event could supply a host-close signal analogous to observed0x80, subject to adapter verification. return_to_title/restart/reset should cancel their own resources explicitly; this evidence does not justify labeling them Native WM_CLOSE or assigning0x100.',
                    zeroFlags='A declared normal-open-window unit may pass0, but a real adapter must expose actual lifecycle state if claiming this predicate is integrated; this report does not verify such an adapter.'),
                scope='53 bounded unmodified original cases:24 WindowProc message dispatches,10 full WM_CLOSE executions,10 initialization bit clears and9 worker wait branches, plus source byte/disassembly/caller registration proof. No Native window messages, threads, D3D loss/reset, actual SDL cancel path, complete worker or whole-game equivalence executed. Unknown bit0x100 remains unclassified.')
    assert len(dispatch)+len(close)+len(reset)+len(wait)==53
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=OUTPUT.relative_to(ROOT).as_posix(),originalCases=53,
                         absoluteReferences=len(refs),bit80='WM_CLOSE',bit100='unknown',nativeEquivalent=False)))


if __name__=='__main__':main()
