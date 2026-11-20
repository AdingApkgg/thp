"""Read port-written files with own4028e0 and465840 native machine code.

CRT allocation/copy/free are controlled boundaries. The native dictionary
starts at its zero-filled startup state for each independent file.
"""
import hashlib,importlib,json,struct,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x800000);src,dst,stack=base+0x1000,base+0x80000,base+0x3ff000;heap=[base+0x500000]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);value=0
  if address==0x485540:
   n=get(sp+4);value=heap[0];heap[0]+=(n+15)&~15;m.mem_write(value,bytes(n))
  elif address==0x487620:
   value=get(sp+4);m.mem_write(value,bytes(m.mem_read(get(sp+8),get(sp+12))))
  m.reg_write(UC_X86_REG_EAX,value);m.reg_write(UC_X86_REG_ESP,sp+4);m.reg_write(UC_X86_REG_EIP,get(sp))
 for a in (0x485540,0x487620,0x4855d2):m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def run(address,ecx,edx,args):
  put(stack,base)
  for i,v in enumerate(args):put(stack+4+i*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_EDX,edx);m.emu_start(address,base,count=50000000)
  assert m.reg_read(UC_X86_REG_EIP)==base


 key=sys.argv[1];assert key in ('before','after')
 home=ROOT/'artifacts/th14/current-concurrent-mixer-nov14/spell-browser-persistence';directory=home/key
 spec=json.loads((home/'inputs.json').read_bytes())[key]
 assert hashlib.sha256(img.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 data=Path(spec['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==spec['sha256']
 expected=(directory/'score-observed.bin').read_bytes()
 packed,unpacked=struct.unpack_from('<II',data,16)
 assert packed+24==len(data)and unpacked==len(expected)==149076
 m.mem_write(src,data[24:]);m.mem_write(0x4f36c8,bytes(8192));m.mem_write(dst,bytes(unpacked+32))
 run(0x4028e0,src,packed,(0xac,0x35,0x10,packed));run(0x465840,src,packed,(dst,unpacked))
 decoded=bytes(m.mem_read(dst,unpacked));assert decoded==expected
 (directory/'native-decoded.bin').write_bytes(decoded)
 report=dict(passed=True,actualRetailDecryptAndLzss=True,originalInstructionBytesPatched=0,allocatorCopyAndFreeDeclared=True,
  encodedBytes=len(data),decodedBytes=len(decoded),allDecodedBytesEqualToFreshApplicationLoadedRecords=True,
  dictionaryZeroStartup=True,warmNativeDictionaryAccepted=False,originalWholeGameUiSaveAccepted=False,
  nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),encodedSha256=hashlib.sha256(data).hexdigest(),decodedSha256=hashlib.sha256(decoded).hexdigest(),
  toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),completeGame=False)
 (directory/'native-codec-qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
