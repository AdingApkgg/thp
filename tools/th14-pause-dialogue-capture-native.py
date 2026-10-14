"""Prove the original GUI dialogue-owner writers and bind real MSG execution.

Runs only original publication/terminal-write instruction prefixes. The older
real-MSG evidence supplies complete constructor/update/cleanup observations;
it is read and hashed, never rerun or overwritten.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDI,UC_X86_REG_EIP,UC_X86_REG_ESI

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'tools/th14-loading-lifecycle-evidence-check.py'
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);args=parser.parse_args()
    output=Path(args.output).resolve();assert output.is_relative_to(ROOT/'artifacts/th14')
    spec=importlib.util.spec_from_file_location('pause_dialogue_image',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);image=helper.Image()
    original_path=ROOT/'artifacts/th14/dialogue-application-message-scene-text/scratch.json'
    real=json.loads(original_path.read_text(encoding='utf-8'))
    original_tool=ROOT/'tools/th14-dialogue-application-message-scene-text-native.py'
    assert real['executableSha256']==helper.EXPECTED_EXE_SHA and real['toolSha256']==SHA(original_tool)
    assert 'whole431a70' in real['scope'] and 'whole432400' in real['scope'] and '42e6f0' in real['scope']
    cases=[]
    for row in real['rows']:
        states=[r['status'] for r in row['frames']]
        assert states and states[-1]==1 and all(s==0 for s in states[:-1])
        cases.append(dict(input=row['input'],frames=len(states),nativeOwnerNonzeroUntilFinalFrame=True,
                          finalOwnerZero=True,statusExpression='int(get(GUI+0x194)==0)'))
    writes=[];uc=image.machine();gui,dialogue=0x600000,0x610000
    helper.word(uc,gui+0x194,0)
    def observe(machine,access,address,size,value,user):
        if address==gui+0x194:writes.append(dict(instruction=hex(machine.reg_read(UC_X86_REG_EIP)),bytes=size,value=value))
    uc.hook_add(UC_HOOK_MEM_WRITE,observe)
    uc.reg_write(UC_X86_REG_EDI,gui);uc.reg_write(UC_X86_REG_EAX,dialogue);uc.reg_write(UC_X86_REG_ESI,2)
    uc.emu_start(0x4321d6,0x4321de,count=20)
    assert struct.unpack('<I',uc.mem_read(gui+0x194,4))[0]==dialogue
    assert struct.unpack('<I',uc.mem_read(dialogue,4))[0]==2
    uc.reg_write(UC_X86_REG_EDI,gui);uc.emu_start(0x430df4,0x430dfe,count=20)
    assert struct.unpack('<I',uc.mem_read(gui+0x194,4))[0]==0
    assert writes==[dict(instruction='0x4321d6',bytes=4,value=dialogue),dict(instruction='0x430df4',bytes=4,value=0)]
    md=Cs(CS_ARCH_X86,CS_MODE_32);instructions=[]
    for address in (0x4321d1,0x4321d6,0x4321dc,0x430d6b,0x430d7b,0x430d80,0x430d82,0x430de6,0x430dec,0x430df4,0x448c86,0x448c8b,0x448c92,0x448cfa,0x448d59,0x448d6a):
        i=next(md.disasm(image.bytes(address,15),address,count=1));instructions.append(dict(address=hex(address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str))
    report=dict(nativeDialogueOwnerEvidencePassed=True,actualRetailProcessesStarted=0,hostOrGameCallShims=0,
                controlledWriterPrefixes=dict(publicationEntry='0x4321d6',publicationStop='0x4321de',terminalEntry='0x430df4',terminalStop='0x430dfe',
                                              declaredGUI=hex(gui),declaredConstructedDialogue=hex(dialogue),writes=writes,scope='Publication prefix begins after constructor return; terminal prefix begins after original destructor/free. No constructors or frees simulated in these prefixes.'),
                realMessageEvidence=dict(path=original_path.relative_to(ROOT).as_posix(),sha256=SHA(original_path),toolSha256=SHA(original_tool),cases=cases,frames=sum(r['frames'] for r in cases),scope=real['scope']),
                originalInstructions=instructions,executableSha256=helper.EXPECTED_EXE_SHA,helperSha256=SHA(HELPER),toolSha256=SHA(Path(__file__)),
                provenMeaning='GUI+194 stores the allocated live MSG dialogue owner after whole431a70 succeeds. GUI430d6b loads it; whole432400 zero return keeps it, nonzero return destroys/frees it then430df4 clears it. It is a pointer lifetime predicate, not a separately guessed bool.',
                scope='Read-only old complete real-MSG evidence plus new unchanged publication/terminal-write instruction prefixes; no original game process, graphics API execution, scheduler or complete Pause/framebuffer proof.')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(nativeDialogueOwnerEvidencePassed=True,realMsgCases=len(cases),realMsgFrames=report['realMessageEvidence']['frames'],writerPrefixes=2,hostShims=0)))


if __name__=='__main__':main()
