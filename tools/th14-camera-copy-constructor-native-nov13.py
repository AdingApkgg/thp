"""Execute the original camera copy/default-reset block on retained real poses."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn import x86_const as X
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-copy-constructor-nov13';H.mkdir()
P=R/'artifacts/th14/option-refresh-oracle-nov13/current-replay/native-helper-math'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
proof=load(P/'verified.json');assert proof['serviceExited']and proof['actualOriginalHelperCases']==602
inputs=(P/'inputs.u32').read_bytes();outputs=(P/'outputs.u32').read_bytes()
assert hashlib.sha256(inputs).hexdigest()==proof['inputsSha256']
assert hashlib.sha256(outputs).hexdigest()==proof['outputsSha256']
sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert hashlib.sha256(image.data).hexdigest()==proof['originalExecutableSha256']
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in image.sections:
 first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
stage,stack=0x70000000,0x70010000;m.mem_map(stage,0x12000)
rows=[]
for pose_index in [0,161,300]:
 before=inputs[pose_index*600:pose_index*600+300]
 assert inputs[pose_index*600+300:pose_index*600+600]==before
 for mode in [0,1]:
  after=outputs[(pose_index*2+mode)*300:(pose_index*2+mode+1)*300]
  for after_math in [0,1]:
   source=after if after_math else before
   m.mem_write(0x4d9514,source);m.mem_write(stage,b'\xcd'*0x43a0)
   for reg,val in [(X.UC_X86_REG_EBP,stack+0x1000),(X.UC_X86_REG_ESP,stack+0xf00),
                   (X.UC_X86_REG_EBX,stage),(X.UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,val)
   m.emu_start(0x40d412,0x40d502,count=2000);assert m.reg_read(X.UC_X86_REG_EIP)==0x40d502
   initialized=bytes(m.mem_read(stage+0x4274,300))
   assert initialized[96:224]==source[96:224]
   rows.append(dict(poseIndex=pose_index,poseCallback=30528+pose_index,mode=mode,
                    captureAfterMath=after_math,inputWords=list(struct.unpack('<75I',before)),
                    worldAfterMathWords=list(struct.unpack('<75I',after)),
                    sourceCapturedWords=list(struct.unpack('<75I',source)),
                    stageInitializedWords=list(struct.unpack('<75I',initialized))))
report=dict(actualRetailCameraCopyAndReset=True,retailBlock=['40d412','40d502'],
 actual75WordRepRead='40d445',cases=len(rows),rows=rows,originalInstructionBytesPatched=0,
 cachedMatricesPreservedByOriginalConstructor=True,physicalCopyTimestampProven=False,
 declaredServices='No replacement callees inside this original block',
 originalFullConstructorAndRegistrationAccepted=False,newGameOrGpuOrAudioStarted=False,
 executableSha256=hashlib.sha256(image.data).hexdigest(),blockSha256=hashlib.sha256(image.read(0x40d412,0xf0)).hexdigest(),
 completeGame=False,bindings={p.relative_to(R).as_posix():sha(p)for p in [P/'verified.json',P/'inputs.u32',P/'outputs.u32',Path(__file__)]})
(H/'native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(cases=len(rows),cachedMatricesPreserved=True)))
