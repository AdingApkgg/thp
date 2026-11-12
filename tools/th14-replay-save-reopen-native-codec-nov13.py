"""Read port-written files with own4028e0 and465840 native machine code.

CRT allocation/copy/free are controlled boundaries. The native dictionary
starts at its zero-filled startup state for each independent file.
"""
import hashlib,importlib,json,struct
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

 directory=ROOT/'artifacts/th14/replay-save-reopen-nov13';proof=json.loads((directory/'session-result.json').read_bytes());rows=[]
 assert proof['cases']==60 and proof['actualSessionSaveAndReplayOpen']
 assert hashlib.sha256(img.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 for case in proof['rows']:
  p=directory/'files'/(case['name']+'.rpy');data=p.read_bytes();expected=(directory/'files'/(case['name']+'.decoded')).read_bytes()
  assert hashlib.sha256(data).hexdigest()==case['fileSha256'] and hashlib.sha256(expected).hexdigest()==case['decodedSha256']
  assert data[:6]==b't13r\x02\x00'.decode('unicode_escape').encode('latin1')
  packed,unpacked=struct.unpack_from('<II',data,0x1c);declared=struct.unpack_from('<I',data,0xc)[0]
  assert declared==len(data)==0x24+packed and unpacked==len(expected)
  assert src+packed<dst and dst+unpacked+32<base+0x500000
  heap[0]=base+0x500000;m.mem_write(src,data[0x24:]);m.mem_write(0x4f36c8,bytes(8192));m.mem_write(dst,bytes(unpacked+32))
  run(0x4028e0,src,packed,(0x5c,0xe1,0x400,packed));run(0x4028e0,src,packed,(0x7d,0x3a,0x100,packed));run(0x465840,src,packed,(dst,unpacked))
  decoded=bytes(m.mem_read(dst,unpacked));assert decoded==expected,case['name']
  count,character,subtype,difficulty=struct.unpack_from('<4I',decoded,0x78)
  assert (character,subtype,difficulty)==(case['selection']//2,case['selection']%2,case['difficulty'])
  two=not case['practice'] and difficulty<4;assert count==(2 if two else 1)
  offset=0x94;stages=[]
  for ordinal in range(count):
   stage,seed=struct.unpack_from('<HH',decoded,offset);frames,payload=struct.unpack_from('<II',decoded,offset+4)
   assert stage==(2 if ordinal else 5 if case['practice'] else 7 if difficulty==4 else 1)
   assert struct.unpack_from('<I',decoded,offset+0xd8)[0]==(0 if ordinal else 1)
   assert struct.unpack_from('<ii',decoded,offset+0xc)==((3456,50001)if ordinal else(-1234,51199))
   real_frames=17 if ordinal else 33;last=ordinal==count-1
   assert frames==real_frames+int(last)
   inputs=decoded[offset+0xdc:offset+0xdc+frames*6]
   for n in range(real_frames):
    held=(0x11,0x20,0)[n%3];previous=(0x11,0x20,0)[(n-1)%3]if n else 0
    assert struct.unpack_from('<3H',inputs,n*6)==(held,held&~previous,previous&~held)
   if last:assert inputs[-6:]==bytes([255])*6
   stages.append(dict(stage=stage,frames=frames,payloadBytes=payload));offset+=0xdc+payload
  assert offset==len(decoded)
  rows.append(dict(name=case['name'],encodedBytes=len(data),decodedBytes=len(decoded),decodedSha256=hashlib.sha256(decoded).hexdigest(),stages=stages))
 report=dict(passed=True,cases=len(rows),rows=rows,actualRetailTwoDecryptPassesAndLzss=True,
  originalInstructionBytesPatched=0,allocatorCopyAndFreeAreDeclaredServices=True,
  dictionaryZeroStartupPerFile=True,warmNativeDictionaryLifetimeAccepted=False,
  completeDecodedBytesEqual=True,headerFlagsCoordinatesAndAllInputEdgesChecked=True,
  syntheticMetadataAndInputs=True,originalWholeReplayLoaderOrGameplayAccepted=False,
  browserDownloadOrOsSaveAccepted=False,completeGame=False,
  nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  sessionResultSha256=hashlib.sha256((directory/'session-result.json').read_bytes()).hexdigest())
 out=directory/'native-codec-qualified.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,cases=len(rows),completeDecodedBytesEqual=True,completeGame=False)))
if __name__=='__main__':main()
