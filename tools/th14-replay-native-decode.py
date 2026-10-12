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
 base=0x70000000;m.mem_map(base,0x400000);src,dst,stack=base+0x1000,base+0x80000,base+0x3ff000;heap=[base+0x100000]
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
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_EDX,edx);m.emu_start(address,base,count=10000000)
  assert m.reg_read(UC_X86_REG_EIP)==base
 directory=ROOT/'artifacts/th14/replay-writer-check';proof=json.loads((ROOT/'artifacts/th14/replay-writer-native.json').read_text(encoding='utf8'));rows=[]
 ns={};exec(compile((ROOT/'tools/th-replay-container.py').read_text(encoding='utf8').partition('if __name__')[0],'container','exec'),ns)
 for p in sorted(directory.glob('*.rpy')):
  data=p.read_bytes();assert data[:6]==b't13r\x02\x00';packed,unpacked=struct.unpack_from('<II',data,0x1c);assert struct.unpack_from('<I',data,0xc)[0]==0x24+packed
  heap[0]=base+0x100000;m.mem_write(src,data[0x24:0x24+packed]);m.mem_write(0x4f36c8,bytes(8192));m.mem_write(dst,bytes(unpacked+32))
  run(0x4028e0,src,packed,(0x5c,0xe1,0x400,packed));run(0x4028e0,src,packed,(0x7d,0x3a,0x100,packed));run(0x465840,src,packed,(dst,unpacked))
  decoded=bytes(m.mem_read(dst,unpacked))
  expected=bytes.fromhex(proof['cases'][int(p.stem.split('-')[1])]['decoded']) if p.stem.startswith('case-') else ns['decode_with'](data,packed,unpacked,ns['TH13'])
  assert decoded==expected,p.name
  rows.append(dict(file=p.name,packed=packed,unpacked=unpacked,sha256=hashlib.sha256(data).hexdigest()))
 report=dict(passed=True,files=len(rows),rows=rows,nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),scope='Full own4028e0 two decryption passes and465840 decompression read port-written TH14 recorder files. CRT allocation/copy/free and fresh-process zero dictionary are controlled. Native container parser, configuration validation, native playback lifecycle and canonical native compressed bytes are excluded.')
 (ROOT/'docs/porting/th14-replay-native-decode-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(f'PASS {len(rows)} port-written files read by native TH14 decryptor/decompressor')
if __name__=='__main__':main()
