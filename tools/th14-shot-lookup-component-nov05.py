"""Compare read-only lookup against actual retail47f0a0 in owned x86 memory."""
from pathlib import Path
import hashlib, importlib, json, struct, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-native-nov05'
sys.path.insert(0,str(R/'tools'))
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
module=importlib.import_module('th14-shot-lifetime-readonly-nov05')
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,offset,n in image.sections:
    first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first)
    m.mem_write(base,image.data[offset:offset+n])
manager,external,stack,ret=0x71000000,0x73000000,0x74001000,0x74001f00
m.mem_map(manager,0x1000000);m.mem_map(external,0x10000);m.mem_map(stack-0x1000,0x2000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v))
rows=[]


def compare(handle,case):
    put(stack,ret);put(stack+4,handle)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
    m.emu_start(0x47f0a0,ret,count=10000)
    assert m.reg_read(UC_X86_REG_EIP)==ret
    actual=module.find_vm(lambda p,n:bytes(m.mem_read(p,n)),manager,handle)
    assert actual==m.reg_read(UC_X86_REG_EAX),case
    rows.append(dict(case=case,equal=True))


for slot in [0,1,255,4095,8190,8191]:
    for live in [False,True]:
        for matches in [False,True]:
            handle=(9<<13)|slot
            if slot!=8191:
                base=manager+slot*0x5e4
                m.mem_write(base+0x6b8,bytes([int(live)]))
                put(base+0x61c,handle if matches else handle+8192)
            else:
                put(manager+0xfe8208,external+0x570 if live else 0)
                put(manager+0xfe8210,0);put(external+0x570,external)
                put(external+0x574,0);put(external+0x540,handle if matches else handle+8192)
            compare(handle,dict(slot=slot,live=live,matches=matches))
compare(0,'null handle')
for first_matches in [False,True]:
    for second_matches in [False,True]:
        handle=(10<<13)|8191;second=external+0x1000
        put(manager+0xfe8208,external+0x570);put(manager+0xfe8210,second+0x570)
        for address,match in [(external,first_matches),(second,second_matches)]:
            put(address+0x570,address);put(address+0x574,0)
            put(address+0x540,handle if match else handle+8192)
        compare(handle,dict(ordinaryMatch=first_matches,overlayMatch=second_matches))
sha=lambda data:hashlib.sha256(data).hexdigest()
report=dict(passed=True,componentCases=len(rows),rows=rows,retailLookupEntry='0x47f0a0',
    poolAndExternalListsCompared=True,originalProcessNotYetRun=True,
    executableSha256=sha(image.data),lookupInstructionSha256=sha(image.read(0x47f0a0,0x93)),
    moduleSha256=sha((R/'tools/th14-shot-lifetime-readonly-nov05.py').read_bytes()),
    toolSha256=sha(Path(__file__).read_bytes()),completeGame=False)
(H/'lookup-component.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='rows'}))
