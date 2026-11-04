"""Execute original camera prefixes with all camera words including the native render dimensions."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
 image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 assert image.read(0x40dae7,2)==image.read(0x40d445,2)==b'\xf3\xa5'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in image.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
 base,owner,scene,world,stack=0x70000000,0x70001000,0x70010000,0x4d9514,0x7003f000;m.mem_map(base,0x40000)
 old=bytearray(struct.pack('<75I',*[0x3f000000+i for i in range(75)]));new=bytearray(struct.pack('<75I',*[0x40000000+i for i in range(75)]));struct.pack_into('<I',old,0x30,0xbf800000);struct.pack_into('<I',new,0x30,0)
 cut=0;stopped=False
 def hook(machine,pc,size,user):
  nonlocal stopped
  if pc==0x40dae7 and cut<75 and not stopped and machine.reg_read(UC_X86_REG_ECX)==75-cut:stopped=True;machine.emu_stop()
 m.hook_add(UC_HOOK_CODE,hook,begin=0x40dae7,end=0x40dae7);rows=[]
 for cut in range(76):
  stopped=False;m.mem_write(world,bytes(old));m.mem_write(owner+0x4274,bytes(new));m.mem_write(scene+0x4274,bytes([0xcc])*300);m.reg_write(UC_X86_REG_ESI,owner);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EFLAGS,2)
  m.emu_start(0x40dad7,0x40dae9,count=200);assert m.reg_read(UC_X86_REG_EIP)==(0x40dae7 if cut<75 else 0x40dae9),(cut,hex(m.reg_read(UC_X86_REG_EIP)),m.reg_read(UC_X86_REG_ECX),stopped)
  prefix=bytes(new[:cut*4]+old[cut*4:]);assert bytes(m.mem_read(world,300))==prefix
  reader_context=m.context_save();reference_bits=[]
  for begin,end in [(0x46f921,0x46f931),(0x46f935,0x46f945),(0x46f949,0x46f959),(0x46f95d,0x46f965),(0x46f969,0x46f971),(0x46f975,0x46f97d)]:
   assert image.read(begin,4)==bytes.fromhex('f30f1005')
   m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(begin,end,count=10)
   assert m.reg_read(UC_X86_REG_EIP)==end;reference_bits.append(m.reg_read(UC_X86_REG_XMM0)&0xffffffff)
  m.context_restore(reader_context)
  main=m.context_save();m.reg_write(UC_X86_REG_EBX,scene);m.emu_start(0x40d435,0x40d447,count=100);assert m.reg_read(UC_X86_REG_EIP)==0x40d447 and bytes(m.mem_read(scene+0x4274,300))==prefix;m.context_restore(main)
  if cut<75:m.emu_start(0x40dae7,0x40dae9,count=200)
  assert m.reg_read(UC_X86_REG_EIP)==0x40dae9 and bytes(m.mem_read(world,300))==bytes(new)
  rows.append(dict(mappedSemanticCppSha256=sha(b''.join(prefix[a:a+n]for a,n in [(0,72),(84,4),(96,204),(72,12),(88,8)])),copiedMainDwordsAtWorkerRead=cut,controllerPublicationEventNotReached=cut<75,workerCopiedRightX=struct.unpack_from('<I',prefix,0x30)[0],workerCameraSha256=sha(prefix),workerMappedCameraSha256=sha(prefix),cameraReferenceBits=reference_bits))
 result=dict(namedFieldMapping=True,unmappedNativeByteOffsets=[],all75CameraWordsMapped=True,verifiedOriginalCameraPublicationWordPrefix=True,originalAnmCameraReadsExecutedAtEveryPrefix=True,referenceReadBlockExecutions=76*6,syntheticEntryAtKnownReadBlocks=True,cases=76,rows=rows,firstNewRightXBeforePublicationDwords=13,mainRepPc=0x40dae7,workerRepPc=0x40d445,publicationEventPc=0x40dae9,syntheticCamerasAndCpuSchedule=True,originalInstructionsModified=False,liveOriginalProcess=False,oldExactProducerRecovered=False,nativeStateProvidedToEngine=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
 out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
if __name__=='__main__':main()
