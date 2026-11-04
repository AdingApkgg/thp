"""Exercise actual retail cursor/EOF paths, with controlled replay memory in x86."""
from pathlib import Path
import argparse,hashlib,importlib,importlib.util,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 image,*_=importlib.import_module('th-anm-handlers').handlers(14)
 assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 path=R/'tools/th14-replay-cursor-readonly-nov04.py';spec=importlib.util.spec_from_file_location('cursor',path);cursor=importlib.util.module_from_spec(spec);spec.loader.exec_module(cursor)
 assert cursor.STRIDE==56
 machine=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,address,size,offset,count in image.sections:
  first=address&~4095;machine.mem_map(first,((address+size+4095)&~4095)-first);machine.mem_write(address,image.data[offset:offset+count])
 base=0x70000000;machine.mem_map(base,0x100000)
 manager,header,inputs,fps,stack=base+0x1000,base+0x3000,base+0x4000,base+0x5000,base+0xff000
 put=lambda address,value:machine.mem_write(address,struct.pack('<I',value&0xffffffff))
 read=lambda address,size:bytes(machine.mem_read(address,size))
 traces=[]
 def observe(uc,pc,size,data):
  if pc in (0x4551f3,0x45521b,0x4552cd,0x4552f4,0x4552fb,0x448ef0):traces.append(pc)
  if pc==0x448ef0:uc.emu_stop() # Actual handler entry, whose game/OS state is not staged.
 machine.hook_add(UC_HOOK_CODE,observe)
 rows=[]
 cases=[('valid-first',0,2,False),('valid-last',1,2,False),('at-declared-end',2,2,False),('past-declared-end',3,2,False),('terminal-marker',0,2,True)]
 for name,position,frames,marker in cases:
  machine.mem_write(manager,bytes(0x320));machine.mem_write(0x4d6878,bytes(0x240));put(0x4db558,1);put(0x4db688,manager);put(0x4d6a90,0)
  put(manager+0x10,1);put(manager+0x218,6);put(manager+0x210,91)
  slot=manager+6*40;machine.mem_write(header,struct.pack('<HHII',6,12345,frames,frames*6))
  for offset,value in [(0xd8,header),(0xcc,inputs),(0xd4,fps),(0xdc,position)]:put(slot+offset,value)
  machine.mem_write(inputs,b'\xff'*6 if marker else struct.pack('<3H',521,0,0));machine.mem_write(fps,b'\x3c\x3d');put(stack,base)
  before=cursor.snapshot(read);observed_before=struct.unpack('<14I',before)
  assert observed_before[1:12]==(manager,1,6,header,inputs,fps,position,91,frames,(12345<<16)|6,frames*6)
  assert observed_before[0]==(31 if position<frames else 15)
  memory_before=read(manager,0x320);assert cursor.snapshot(read)==before and read(manager,0x320)==memory_before
  traces.clear();machine.reg_write(UC_X86_REG_ESP,stack);machine.reg_write(UC_X86_REG_ECX,manager);machine.emu_start(0x455180,base,count=10000)
  assert machine.reg_read(UC_X86_REG_EIP)==(0x448ef0 if marker else base)
  after=struct.unpack('<14I',cursor.snapshot(read));assert after[7:9]==((position,91)if marker else(position+1,92))
  if marker:
   assert 0x45521b in traces and 0x4552cd not in traces and after[5:7]==(inputs,fps)
  elif position>=frames:
   assert 0x4552cd in traces and 0x45521b not in traces and after[5:7]==(inputs,fps)
  else:
   assert 0x4552cd not in traces and 0x45521b not in traces and after[5]==inputs+6
  rows.append(dict(case=name,beforeCursor=position,afterCursor=after[7],declaredFrames=frames,observedBranchPcs=list(traces),inputPointerAdvanced=after[5]-inputs,fpsPointerAdvanced=after[6]-fps))
 return dict(verifiedActualNativeReaderBranches=True,cases=rows,cursorStride=cursor.STRIDE,readOnlyHelperSha256=SHA(path.read_bytes()),nativeExecutableSha256=SHA(image.data),toolSha256=SHA(Path(__file__).read_bytes()),
  cursorGreaterThanFramesRequiresExhaustionOnlyUnderVerifiedInitialization=True,terminalMarkerCallsHandlerBeforeCursorIncrement=True,terminalMarkerHandlerNotExecuted=True,
  controlledMemoryOnly=True,originalPlaybackEofObserved=False,originalGameStarted=False,completeGame=False,nativeEquivalent=False)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')
 result=verify();encoded=(json.dumps(result,indent=2)+'\n').encode()
 if a.check:assert out.read_bytes()==encoded
 else:assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(encoded)
 print(json.dumps(result))


if __name__=='__main__':main()
