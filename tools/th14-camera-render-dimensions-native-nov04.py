"""Observe render-dimension stores in original camera reset code.

Only the dimension data flow is tested. Screen-matrix math is skipped at its
unmodified function entry; neither full camera reset nor pixels are accepted.
"""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
Image=importlib.import_module('th12-pe').Image
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.mkdir(parents=True)
 image=Image('H:/Games/th/14/th14.exe');assert SHA(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 assert image.read(0x4463fb,3)==b'\xc2\x04\x00'
 u=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,count in image.sections:
  first=base&~4095;u.mem_map(first,((base+size+4095)&~4095)-first);u.mem_write(base,image.data[raw:raw+count])
 stop=0x70000000;stack=stop+0x2000;owner=0x71000000
 u.mem_map(stop,0x4000);u.mem_map(owner,0x2000)
 read_word=lambda address:struct.unpack('<I',u.mem_read(address,4))[0]
 cameras=[0x230,0x35c,0x488,0x5b4];writes=[];screen=[]
 def code(uc,pc,size,_):
  if pc==0x446250:
   sp=uc.reg_read(UC_X86_REG_ESP);camera=read_word(sp+4)
   assert camera-owner in cameras
   screen.append(dict(cameraOffset=camera-owner,dimensions=list(struct.unpack('<II',uc.mem_read(camera+0x58,8)))))
   # The original screen function returns with RET4. No instruction bytes change.
   uc.reg_write(UC_X86_REG_EIP,read_word(sp));uc.reg_write(UC_X86_REG_ESP,sp+8)
 def write(uc,access,address,size,value,_):
  if size==4 and address-owner in [offset+word for offset in cameras for word in (0x58,0x5c)]:
   writes.append(dict(pc=uc.reg_read(UC_X86_REG_EIP),cameraOffset=(address-owner)//4*4,wordValue=value&0xffffffff))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 rows=[]
 for entry in (0x4465e0,0x446920):
  for width,height,flags in [(640,480,0),(960,720,4),(1280,960,8),(641,479,0)]:
   writes.clear();screen.clear();u.mem_write(owner,b'\xa5'*0x2000)
   u.mem_write(0x4f7a64,struct.pack('<II',width,height));u.mem_write(0x4f7a6c,struct.pack('<f',width/640))
   u.mem_write(0x4f7a54,bytes([flags]));u.mem_write(stack,struct.pack('<I',stop));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,owner)
   u.emu_start(entry,stop,count=200000);assert u.reg_read(UC_X86_REG_EIP)==stop
   actual=[list(struct.unpack('<II',u.mem_read(owner+offset+0x58,8)))for offset in cameras]
   assert actual==[[width,height]]*4 and len(screen)==4 and all(row['dimensions']==[width,height]for row in screen)
   assert len(writes)==8
   rows.append(dict(entry=entry,width=width,height=height,flags=flags,scale=width/640,cameraOffsets=cameras,dimensionWords=actual,screenMathCallsSkipped=list(screen),originalDimensionWrites=list(writes)))
 result=dict(verifiedOriginalRenderDimensionDataFlow=True,profiles=len(rows),cameraInstances=len(rows)*4,dimensionWords=len(rows)*8,
  nativeDimensionByteOffsets=[0x58,0x5c],nativeDimensionWordIndices=[22,23],sourceGlobalAddresses=[0x4f7a64,0x4f7a68],
  rows=rows,screenMatrixMathSkipped=True,fullCameraResetAccepted=False,syntheticInputs=True,instructionBytesPatched=0,
  originalProcessesLaunched=False,physicalAudioDevicesOpened=0,productionCoreChanged=False,completeGame=False,nativeEquivalent=False,
  nativeExeSha256=SHA(image.data),toolSha256=SHA(Path(__file__).read_bytes()))
 (out/'native.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({key:value for key,value in result.items()if key!='rows'}))


if __name__=='__main__':main()
