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
 directory=ROOT/'artifacts/th14/browser-focused-growth-oct14';rows=[]
 ns={};exec(compile((ROOT/'tools/th-replay-container.py').read_text(encoding='utf8').partition('if __name__')[0],'container','exec'),ns)
 for name in ('browser-normal-recording',):
  p=directory/(name+'.rpy');data=p.read_bytes();assert data[:6]==b't13r\x02\x00';packed,unpacked=struct.unpack_from('<II',data,0x1c)
  declared=struct.unpack_from('<I',data,0xc)[0];assert declared==0x24+packed and declared<=len(data)
  assert src+packed<dst and dst+unpacked+32<base+0x500000;heap[0]=base+0x500000;m.mem_write(src,data[0x24:declared]);m.mem_write(0x4f36c8,bytes(8192));m.mem_write(dst,bytes(unpacked+32))
  run(0x4028e0,src,packed,(0x5c,0xe1,0x400,packed));run(0x4028e0,src,packed,(0x7d,0x3a,0x100,packed));run(0x465840,src,packed,(dst,unpacked))
  decoded=bytes(m.mem_read(dst,unpacked));assert decoded==ns['decode_with'](data,packed,unpacked,ns['TH13'])
  count,character,subtype,difficulty=struct.unpack_from('<4I',decoded,0x78);assert 1<=count<=7 and character<=2 and subtype<=1 and difficulty<=4
  stages=[];offset=0x94
  for index in range(count):
   stage,seed=struct.unpack_from('<HH',decoded,offset);frames,payload=struct.unpack_from('<II',decoded,offset+4);assert 1<=stage<=7 and frames*6<=payload
   stages.append(dict(stage=stage,seed=seed,frames=frames,inputBytes=frames*6,payloadBytes=payload,headerSha256=hashlib.sha256(decoded[offset:offset+0xdc]).hexdigest()))
   offset+=0xdc+payload
  assert offset==len(decoded)
  meta_path=directory/(name+'-source.json');meta=json.loads(meta_path.read_text());assert meta['sha256']==hashlib.sha256(data).hexdigest()
  meta.update(status='BROWSER_SAVE_RELOAD_NATIVE_CODEC_VERIFIED',declaredContainerBytes=declared,trailingBytes=len(data)-declared,trailingSha256=hashlib.sha256(data[declared:]).hexdigest(),decodedSha256=hashlib.sha256(decoded).hexdigest(),stageCount=count,character=character,subtype=subtype,difficulty=difficulty,stages=stages,actualNativeCodecVerified=True,nativeExecutableSha256=hashlib.sha256(img.data).hexdigest(),nativeCodecObserverSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
  (directory/(name+'-decoded.bin')).write_bytes(decoded);meta_path.write_text(json.dumps(meta,indent=2)+'\n');rows.append(meta)
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,files=len(rows),rows=rows,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Actual original4028e0 two-pass decryption and465840 LZSS decoding for the ordinary browser-saved and reloaded recording, independently compared with the byte-codec mirror. Every original suffix retained. Parsed selection comes from file bytes rather than web label. No playback or completion/equivalence claim.')
 (ROOT/'docs/porting/th14-browser-saved-replay-native-codec-oct14.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,selections=[dict(character=r['character'],subtype=r['subtype'],difficulty=r['difficulty'],stages=[s['stage'] for s in r['stages']]) for r in rows])))
if __name__=='__main__':main()
