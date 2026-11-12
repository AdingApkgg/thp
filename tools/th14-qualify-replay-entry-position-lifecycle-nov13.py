"""Reject the clear-only candidate against the later retail recording write."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/replay-entry-position-nov13'
assert not (O/'lifecycle-qualified.json').exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(p.read_bytes())
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,raw,n in im.sections:
 p=va&~4095;m.mem_map(p,((va+size+4095)&~4095)-p);m.mem_write(va,im.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x10000);player=B+0x1000
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
report=load(O/'result.json');native=load(O/'native.json');cases=[]
for row in native['rows']:
 initial=row['initial'];x,y=row['input']
 before=bytes([0xa5])*0x100;m.mem_write(B,before);put(B+0xc,x);put(B+0x10,y)
 put(0x4d9658,initial);m.reg_write(UC_X86_REG_EDX,B)
 m.emu_start(0x4547cc,0x4547e3,count=10);assert m.reg_read(UC_X86_REG_EIP)==0x4547e3
 intermediate=list(struct.unpack('<ii',m.mem_read(B+0xc,8)))
 assert intermediate==row['output']
 put(0x4db67c,player);put(player+0x5ec,x);put(player+0x5f0,y)
 m.reg_write(UC_X86_REG_ESI,B)
 m.emu_start(0x455f58,0x455f70,count=10);assert m.reg_read(UC_X86_REG_EIP)==0x455f70
 after=bytes(m.mem_read(B,0x100));expected=bytearray(before);struct.pack_into('<ii',expected,0xc,x,y)
 assert after==expected
 cases.append(dict(initial=initial,input=[x,y],constructorCoordinates=intermediate,
                   recordingActivationCoordinates=list(struct.unpack_from('<ii',after,0xc))))
results={}
for mode in ['baseline','candidate']:
 rows=report['results'][mode]['rows']
 different=0
 for row in rows:
  expected=next(x['recordingActivationCoordinates']for x in cases if x['initial']==row['initial']and x['input']==row['input'])
  different+=row['actual']!=expected
 results[mode]=dict(cases=len(rows),different=different)
assert results['baseline']==dict(cases=480,different=0)
assert results['candidate']==dict(cases=480,different=240)
output=dict(originalInstructionBytesPatched=0,noDeclaredServices=True,retailPositionFlowCases=cases,
 sourceBitProducersAndFullRecorderFunctionNotReexecuted=True,
 constructorClearEntry='4547cc',recordingActivationCopyEntry='455f58',
 previousClearOnlyTestInsufficientForRecordingEquivalence=True,
 clearOnlyCandidateRejected=True,baselineCurrentCoordinatesRetained=True,
 actualRetainedSessionHeadersCompared=True,results=results,
 productionChanged=False,completeGame=False,
 bindings={p.relative_to(R).as_posix():sha(p.read_bytes())for p in [Path(__file__),O/'native.json',O/'result.json',O/'baseline-headers.bin',O/'candidate-headers.bin']},
 codeBindings={hex(a):sha(im.read(a,n))for a,n in [(0x4547cc,0x17),(0x455f58,0x18)]})
(O/'lifecycle-qualified.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(currentBaselineDifferences=0,clearOnlyCandidateDifferences=240,candidateRejected=True,productionChanged=False)))
