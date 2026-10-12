"""Execute retail timeGetTime result stores; the clock input is explicit."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
 # Verify the IAT slot within its own terminated import-thunk array.
 pe=struct.unpack_from('<I',img.data,0x3c)[0];rva=struct.unpack_from('<I',img.data,pe+0x18+104)[0];p=img.image_base+rva;provider=None
 while True:
  oft,_,_,name,ft=struct.unpack('<5I',img.read(p,20))
  if not name:break
  index=0
  while True:
   entry=img.u32(img.image_base+(oft or ft)+index*4)
   if not entry:break
   if img.image_base+ft+index*4==0x4b12a0:provider=[img.read(img.image_base+name,64).split(b'\0')[0].decode(),img.read(img.image_base+entry+2,80).split(b'\0')[0].decode()]
   index+=1
  p+=20
 assert provider==['WINMM.dll','timeGetTime'];rows=[]
 for ticks in (0,1,65535,65536,65537,904,13971,27513,0x7fffffff,0x80000000,0xffff0000,0xffffffff):
  for calls in (0,97,0xffffff80):
   m.mem_write(0x4db508,struct.pack('<HHIHHI',0xbeef,0x4321,calls,0xabcd,0x1234,calls^0x80000000));m.reg_write(UC_X86_REG_EAX,ticks);m.emu_start(0x444a1f,0x444a30,count=20)
   rows.append(dict(ticks=ticks,calls=calls,clock=struct.unpack('<I',m.mem_read(0x4d9688,4))[0],words=list(struct.unpack('<4I',m.mem_read(0x4db508,16)))))
 out=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),provider=provider,rows=rows,scope='Exact retail444a1f..444a2a clock and both seed stores with explicit32-bit clock inputs; proves low16 wrapping and unchanged reserved/call words. Real Windows uptime and browser clock origins are excluded.')
 (ROOT/'artifacts/th14/clock-native.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail clock seed stores')
if __name__=='__main__':main()
