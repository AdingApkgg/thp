"""Full472030 VM91/92 setup and eight4171c0 consumers, including command wait."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 base,code,stack,ret,wait=0x70000000,0x70010000,0x700ff000,0x700fe000,0x700fd000;m.mem_map(base,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def instruction(op,args,refs=0,time=0):return struct.pack('<iHHHBBI',time,op,16+len(args)*4,refs,255,len(args),0)+struct.pack('<'+'I'*len(args),*[v&0xffffffff for v in args])
 m.mem_write(wait,b'\xb8\xff\xff\xff\xff\xc3');cases=[]
 for n in range(1024):
  op=91+n//256%2;index=n//32%8;mode=n%32;duration=(-1,0,1,3,30)[n//3%5];rate=(0,.25,.5,.99,1,1.01,1.5,2)[n//7%8];held=n>=512;frame_base=(0,32)[n//11%2]
  args=[index,bits(512),duration,mode,bits(-3.25),bits(23.625)]
  if op==92:args+=[bits(2.5),bits(-7.25)]
  first=instruction(op,args,2);stream=first
  if not held and n%4==0:
   again=args[:];again[2]=5;again[4]=bits(7.125);again[5]=bits(-12.25);stream+=instruction(op,again,2,6)
  stream+=instruction(99 if held else 0,[],time=0 if held else 2147483647)
  m.mem_write(base,bytes(0x7000));m.mem_write(code,bytes(16)+stream);put(base+0x100c,128);put(base+0x1010,frame_base);put(base+0x1020,255);put(base+0x1018,base+0x2000);put(base+0x2000,base+0x6000);put(base+0x6000,wait);put(base+0x2000+0x11f8,base+0x4000);put(base+0x4000+0x8c,base+0x5000);put(base+0x5000+4,code)
  put(0x490eb0,0x4a5788);put(0x4a5788,bits(rate));timeline=[]
  for frame in range(48):
   put(stack,ret);m.reg_write(UC_X86_REG_ECX,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,bits(rate));m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.emu_start(0x472030,ret,count=20000);assert m.reg_read(UC_X86_REG_EIP)==ret
   timeline.append(dict(result=m.reg_read(UC_X86_REG_EAX),time=get(base),offset=get(base+8),top=get(base+0x100c),target=get(base+12+frame_base+512),slots=[get(base+0x1024+j*0x30+k*4) for j in range(8) for k in range(12)]))
  cases.append(dict(input=[rate,frame_base],code=stream.hex(),timeline=timeline))
 (ROOT/'artifacts/th16/ecl-scalar-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(cases)} own VM91/92/wait timelines / {len(cases)*48} frames')
if __name__=='__main__':main()
