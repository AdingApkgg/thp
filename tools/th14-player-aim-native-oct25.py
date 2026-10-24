"""Original42b230 getters -9989/-9956/-9955 and full44ee00, finite inputs.

The only generated instructions store the returned x87 value outside the
original image. No original instruction bytes or math service are replaced.
"""
import hashlib,importlib,json,random,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(im.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in im.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,im.data[raw:raw+n])
 base,enemy,player,stack,store,output=0x70000000,0x70001000,0x70009000,0x7001f000,0x7001e000,0x7001d000;m.mem_map(base,0x20000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
 put(0x4db67c,player);m.mem_write(store,b'\xd9\x1d'+struct.pack('<I',output));inputs=[]
 for x,y in [(0.,0.),(-0.,0.),(0.,-0.),(-0.,-0.),(1.,1.),(-192.,32.),(192.,432.),(.01,-.01),(1e-30,-1e-30)]:
  for dx,dy in [(0,0),(.01,0),(-.01,0),(0,.01),(0,-.01),(.01,.01),(-.01,-.01)]:inputs.append([x,y,f32(x+dx),f32(y+dy)])
 rng=random.Random(14002625)
 for i in range(512):
  x,y=[f32(rng.uniform(-512,512))for _ in range(2)];px,py=(x,y)if i%8==0 else[f32(rng.uniform(-512,512))for _ in range(2)];inputs.append([x,y,px,py])
 h=ROOT/'artifacts/th14/player-aim-oct25/unit';h.mkdir(parents=True,exist_ok=True);input_raw=(json.dumps(inputs,separators=(',',':'))+'\n').encode();(h/'inputs.json').write_bytes(input_raw);rows=[]
 for case,values in enumerate(inputs):
  x,y,px,py=values
  for offset in [0x1234,0x1278,0x12bc]:floats(enemy+offset,x,y,0)
  floats(player+0x5e0,px,py,0)
  for id in [-9989,-9956,-9955]:
   put(stack,store);put(stack+4,id);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.emu_start(0x42b230,store,count=100000);assert m.reg_read(UC_X86_REG_EIP)==store;m.emu_start(store,store+6,count=1)
   rows.append(dict(case=case,id=id,values=values,result=struct.unpack('<I',m.mem_read(output,4))[0]))
 report=dict(executableSha256=hashlib.sha256(im.data).hexdigest(),toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),inputSha256=hashlib.sha256(input_raw).hexdigest(),originalInstructionBytesPatched=0,mathServiceStubs=[],rows=rows,scope=__doc__.strip(),completeGame=False,nativeEquivalent=False);(h/'native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(cases=len(rows),inputPositions=len(inputs),originalInstructionBytesPatched=0)))
if __name__=='__main__':main()
