"""Execute both retail REP copies with independent producer/consumer contexts."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_EFLAGS
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/scene-camera-read-job-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()
sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert image.read(0x40dae7,2)==image.read(0x40d445,2)==b'\xf3\xa5'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,address,size,offset,count in image.sections:
 first=address&~4095;m.mem_map(first,((address+size+4095)&~4095)-first);m.mem_write(address,image.data[offset:offset+count])
base=0x70000000;m.mem_map(base,0x10000);incoming,world,destination=base+0x1000,base+0x2000,base+0x3000
def context(pc,source,target):
 for reg,value in [(UC_X86_REG_ESI,source),(UC_X86_REG_EDI,target),(UC_X86_REG_ECX,75),(UC_X86_REG_EIP,pc),(UC_X86_REG_EFLAGS,2)]:m.reg_write(reg,value)
 return m.context_save()
def words(count):
 for _ in range(count):
  pc=m.reg_read(UC_X86_REG_EIP);remaining=m.reg_read(UC_X86_REG_ECX);assert remaining>0
  m.emu_start(pc,pc+2,count=1);assert m.reg_read(UC_X86_REG_ECX)==remaining-1
def execute(old,new,publish_prefix,read_prefix):
 assert len(old)==len(new)==300;m.mem_write(incoming,new);m.mem_write(world,old);m.mem_write(destination,bytes(300))
 publisher=context(0x40dae7,incoming,world);reader=context(0x40d445,world,destination)
 m.context_restore(publisher);words(publish_prefix);publisher=m.context_save()
 m.context_restore(reader);words(read_prefix);reader=m.context_save()
 m.context_restore(publisher);words(75-publish_prefix)
 m.context_restore(reader);words(75-read_prefix)
 return bytes(m.mem_read(destination,300))
old=struct.pack('<75I',*[0x3f000000+i for i in range(75)]);new=struct.pack('<75I',*[0x40000000+i for i in range(75)]);rows=[]
for published in [0,1,12,13,14,15,24,75]:
 for copied in [0,1,12,13,14,15,24,75]:
  result=execute(old,new,published,copied);rows.append(dict(publisherPrefix=published,readerPrefix=copied,resultHex=result.hex()))
n=R/'artifacts/th14/full-camera-replay-cursor-nov04/full-run/native';report=json.loads((n/'report.json').read_bytes());assert report['callbacks']==122285 and not report['error'] and not report['debugErrors']
load=lambda name:[json.loads(line)for line in(n/name).read_bytes().splitlines()]
before=next(row for row in load('scene-camera-copy-events.jsonl')if row['stage']==5 and row['event']=='scene-camera-copy-before');after=next(row for row in load('scene-camera-copy-events.jsonl')if row['stage']==5 and row['event']=='scene-camera-copy-after');read=next(row for row in load('worker-camera-source-read-events.jsonl')if row['stage']==5)
observed_old=bytes.fromhex(before['worldCameraHexAtWorkerEvent']);observed_new=bytes.fromhex(read['worldCameraHex']);expected=bytes.fromhex(after['copiedCameraHex']);actual=execute(observed_old,observed_new,13,15);assert actual==expected
proof=dict(verifiedRetailTwoRepInterleavings=True,syntheticSchedules=len(rows),syntheticOldHex=old.hex(),syntheticNewHex=new.hex(),rows=rows,
 stage5=dict(publisherPrefix=13,readerPrefix=15,oldHex=observed_old.hex(),newHex=observed_new.hex(),copiedHex=actual.hex(),actualCapturedCopiedSha256=SHA(expected),
  prefix13Observed=True,readerPauseAfter15AndPublisherResumeInferred=True,exactOriginalScheduleRecovered=False),
 nativeExecutableSha256=SHA(image.data),nativeReportSha256=SHA((n/'report.json').read_bytes()),nativeOriginalCallbacks=report['callbacks'],
 originalGameStartedByThisComponent=False,originalStateValuesProvidedToGameSession=False,completeGame=False,nativeEquivalent=False,toolSha256=SHA(Path(__file__).read_bytes()))
out=H/'native.json';assert not out.exists();out.write_bytes((json.dumps(proof,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in proof.items()if k not in ['syntheticOldHex','syntheticNewHex','rows','stage5']}))
