"""Execute the original TH16 velocity gate and complete 4630f0 body."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x20000);vm=0x70001000;stack=0x7001e000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 rates=(0,.125,.5,1,1.5,2,-.25);positions=(0.,-0.,3.1415927410125732,-3.1415927410125732,128.,-256.,1024.,-.375)
 speeds=(0.,-0.,.125,-.25,3.25,-17.75,1024.,-1024.);rows=[]
 for rate_index,rate in enumerate(rates):
  floats(0x4a5788,[rate])
  for sample in range(8):
   values=[positions[(sample+i)%8] for i in range(7)]
   for mask in range(128):
    velocities=[speeds[(sample+i)%8] if mask&(1<<i) else 0. for i in range(7)]
    for enabled in (0,1):
     m.mem_write(vm,bytes(0x700));put(vm+0x530,3);put(vm+0x534,enabled<<24)
     floats(vm+0x38,values[:3]);floats(vm+0x50,values[3:5]);floats(vm+0x78,values[5:]);floats(vm+0x44,velocities[:3]);floats(vm+0x60,velocities[3:5]);floats(vm+0x3c8,velocities[5:])
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBX,vm);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
     m.emu_start(0x462a06,0x462a19,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x462a19
     rows.append([rate_index,sample,mask,enabled,*[get(vm+o) for o in (0x38,0x3c,0x40,0x50,0x54,0x78,0x7c,0x530)]])
 out=ROOT/'artifacts/th16/velocity-native.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),scope='Retail gate462a06..462a19 and complete4630f0 execute with finite positions/velocities and seven rates, all128 enabled channel masks. Rotation bounded wrapping, separately rounded SSE multiplication/addition, scale dirty flags, UV period2/single adjustment and zero-speed retention are compared bitwise. No script dispatch, effective-rate selection, interpolation, camera, geometry, GPU or full gameplay claim.',rates=rates,positions=positions,speeds=speeds,rows=rows),separators=(',',':'))+'\n');print(len(rows),'native TH16 velocity cases')
if __name__=='__main__':main()
