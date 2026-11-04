"""Read-only bounded disassembly to locate the main update-entry boundary."""
from pathlib import Path
import hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(__file__).resolve().parents[1];exe=Path('H:/Games/th/14/th14.exe');raw=exe.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
pe=struct.unpack_from('<I',raw,0x3c)[0];count=struct.unpack_from('<H',raw,pe+6)[0];optional=struct.unpack_from('<H',raw,pe+20)[0]
sections=[]
for n in range(count):
    at=pe+24+optional+n*40;name=raw[at:at+8].rstrip(b'\0').decode();size,rva,physical,offset=struct.unpack_from('<IIII',raw,at+8)
    sections.append(dict(name=name,size=size,rva=rva,physical=physical,offset=offset))
def read(address,size):
    for section in sections:
        delta=address-0x400000-section['rva']
        if 0<=delta and delta+size<=section['physical']:return raw[section['offset']+delta:section['offset']+delta+size]
    raise ValueError(hex(address))
md=Cs(CS_ARCH_X86,CS_MODE_32);rows={}
for address,size in [(0x4447b0,0x58),(0x444890,0xb0),(0x444660,0x150),(0x47d720,0x88),(0x403300,0xa0),(0x44dbd0,0x38),(0x436bd0,0x50),(0x47e2a0,0xf0)]:
    instructions=[dict(pc=ins.address,mnemonic=ins.mnemonic,operands=ins.op_str)for ins in md.disasm(read(address,size),address)]
    rows[hex(address)]=instructions
# .text contains data. Linear disassembly can stop early or lose alignment,
# so raw E8/immediate matches are candidates only, not proven call edges.
text=next(x for x in sections if x['name']=='.text');code=raw[text['offset']:text['offset']+text['physical']];base=0x400000+text['rva']
targets={x:[]for x in [0x4447b0,0x444890,0x47d720,0x44dbd0]};literals={x:[]for x in targets}
for n in range(len(code)-5):
    if code[n]==0xe8:
        destination=base+n+5+struct.unpack_from('<i',code,n+1)[0]
        if destination in targets:targets[destination].append(base+n)
    word=struct.unpack_from('<I',code,n)[0]
    if word in literals:literals[word].append(base+n)
assert any(row['pc']==0x4448cd and row['mnemonic']=='call'and row['operands']=='0x47d720'for row in rows['0x444890'])
out=R/'artifacts/th14/frame-entry-audit-retry1-nov05';out.mkdir(exist_ok=False)
report=dict(executableSha256=hashlib.sha256(raw).hexdigest(),candidateDirectCallReferences={hex(k):[hex(v)for v in values]for k,values in targets.items()},
    candidateLiteralReferences={hex(k):[hex(v)for v in values]for k,values in literals.items()},candidateReferencesAreNotAcceptedInstructionBoundaries=True,
    boundedInstructions=rows,originalProcessLaunched=False,readOnly=True,physicalFrameEntryProven=False,completeGame=False)
(out/'static-report.json').write_text(json.dumps(report,indent=2)+'\n')
for key in ['0x444890','0x47e2a0']:
    print(key)
    for row in rows[key]:print(f"{row['pc']:08x} {row['mnemonic']:8s} {row['operands']}")
print(json.dumps({k:report[k]for k in ['candidateDirectCallReferences','candidateLiteralReferences']}))
