"""Execute retail 440f60 / 441430, including x87 polar, floor, sqrt and atan2.
No game-engine helper is replaced. Each result is five raw float32 words.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,node,output,previous,stack=0x70000000,0x70001000,0x70002000,0x70003000,0x7001f000
 m.mem_map(end,0x20000)
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
 rows=[]
 times=(-2.75,-1.,0.,.125,.5,1.,1.25,2.75,7.,30.,60.125,120.)
 for mode in (0,1,2,3):
  for variant in range(16):
   values=[0,0,bits((-3.,0.,2.25)[variant%3]),bits(999999),mode]
   values += list(map(bits,((.125,-.75,1.)[variant%3],(-.5,.25,-0.)[variant%3],(-0.,.125,2.)[variant%3],23.75,-17.25,3.5)))
   values += list(map(bits,((-200.,-3.141592741,-.087266460061,.5,200.)[variant%5],(-1.,0.,.125,4.)[variant%4],(-.06333333,0.,.1,.13333334)[variant%4],(-999.,-990.,-.02,.001454441,.08144869655,200.)[variant%6])))
   prev=list(map(bits,(12.5,-30.75,-2.25,(-4.,.125,5.5)[variant%3],(-100.,-.087266460061,3.15)[variant%3])))
   for tail in (0,1):
    for t in times:
     m.mem_write(node,struct.pack('<15I',*values));m.mem_write(previous,struct.pack('<5I',*prev));m.mem_write(output,struct.pack('<5f',100,-100,7,123,-123))
     m.mem_write(stack-0x1000,bytes(0x1100));put(stack,end)
     args=[output,output+12,output+16]
     args += [previous,prev[3],prev[4],bits(t)] if tail else [bits(t)]
     for j,v in enumerate(args):put(stack+4+j*4,v)
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,node)
     m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     try:m.emu_start(0x441430 if tail else 0x440f60,end,count=200000)
     except Exception as e:raise RuntimeError(f'mode {mode} variant {variant} tail {tail} time {t} pc {m.reg_read(UC_X86_REG_EIP):x}') from e
     assert m.reg_read(UC_X86_REG_EIP)==end
     rows.append(dict(node=values,previous=prev,time=bits(t),tail=tail,result=words(output,5),valid=int(mode<3)))
 out=ROOT/'artifacts/th14/laser-curve-native.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows),indent=2)+'\n',encoding='utf-8')
 print(f'{len(rows)} retail curve head/tail cases, no substituted math helpers.')
if __name__=='__main__':main()
