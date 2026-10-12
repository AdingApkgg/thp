"""Own TH16 535/536, including actual argument and local destination resolvers."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000)
 data,owner,context,files,table,code,stack,bp= [0x70000000+n for n in (0x1000,0x8000,0xa000,0xc000,0xe000,0x10000,0x30000,0x38000)]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 put(data+0x44b8,owner);put(owner+12,context);put(context+4,0);put(context+8,0);put(context+0x1018,owner);put(owner+0x11f8,files);put(files+0x8c,table);put(table+4,code);put(context+0x1010,32)
 rows=[]
 for op in (535,536):
  for difficulty in (-2147483648,-1,0,1,2,3,4,7):
   for refs in (1,11,31):
    for destination in (0,64,68,256,512):
     values=[0x80000000,0x7fffffff,0x12345678,0xffffffff] if op==535 else [bits(-0.),bits(1.25),bits(-7.5),bits(16777216.)]
     initial=[0x55aa0000+i for i in range(192)]
     for i,v in enumerate(values):initial[(32+64+i*4)//4]=v
     args=[destination if op==535 else bits(destination)]+[(64+i*4 if op==535 else bits(64+i*4)) if refs&(1<<(i+1)) else v for i,v in enumerate(values)]
     instruction=struct.pack('<iHHHBBI',0,op,36,refs,255,5,0)+struct.pack('<5I',*args)
     m.mem_write(context+12,struct.pack('<192I',*initial));m.mem_write(code,bytes(16)+instruction);put(0x4a57b4,difficulty)
     m.reg_write(UC_X86_REG_EDI,data);m.reg_write(UC_X86_REG_EBP,bp);m.reg_write(UC_X86_REG_ESP,stack)
     m.emu_start(0x420711 if op==535 else 0x42079e,0x422a9b,count=2000)
     rows.append(dict(op=op,difficulty=difficulty,instruction=instruction.hex(),initial=initial,output=list(struct.unpack('<192I',m.mem_read(context+12,768)))))
 out=ROOT/'artifacts/th16/difficulty-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),separators=(',',':'))+'\n',encoding='utf-8');print(f'{len(rows)} native TH16 difficulty assignments')
if __name__=='__main__':main()
