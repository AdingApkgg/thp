"""Complete445470 on nine retail sheets;445360 creation is a request boundary."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 ret,player,sht,sub,stack=0x70000000,0x70001000,0x70040000,0x70060000,0x700ff000;m.mem_map(ret,0x100000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 events=[]
 def hook(machine,a,size,user):
  sp=m.reg_read(UC_X86_REG_ESP);events.append([get(sp+4),get(sp+8)]);m.reg_write(UC_X86_REG_EAX,0)
 m.mem_write(0x445360,b'\xc2\x0c\x00');m.hook_add(UC_HOOK_CODE,hook,begin=0x445360,end=0x445360)
 for i,v in enumerate((100,230,390,590,840,1140)):put(0x4a583c+i*4,v)
 rows=[];resources={};mains=('pl00','pl02','pl03','pl01');seasons=('pl00sub','pl02sub','pl03sub','pl01sub','pl04sub')
 for character,season in itertools.product(range(4),range(5)):
  for dest,name in ((sht,mains[character]),(sub,seasons[season])):
   path=ROOT/f'artifacts/th16/options-corpus/{name}.sht';data=path.read_bytes();resources[path.name]=hashlib.sha256(data).hexdigest();m.mem_write(dest,data)
   groups=struct.unpack_from('<H',data,2)[0]
   for i in range(groups):put(dest+0x190+i*4,dest+0x1b8+struct.unpack_from('<I',data,0x190+i*4)[0])
  for power,points,focus,frame,long_frame in itertools.product((0,99,100,200,399,400),(0,100,230,390,590,840,1140),(0,1),(0,1,6,7,14,29),(0,1,29,59,119)):
   events.clear();put(player+0x2c788,sht);put(player+0x2c78c,sub);put(player+0x165c8,focus);put(0x4a57e4,power);put(0x4a57ec,100);put(0x4a5808,points)
   put(stack,ret);put(stack+4,frame);put(stack+8,long_frame);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,player);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.emu_start(0x445470,ret,count=100000);assert m.reg_read(UC_X86_REG_EIP)==ret
   rows.append(dict(character=character,season=season,power=power,points=points,focus=focus,frame=frame,longFrame=long_frame,events=events[:]))
 (ROOT/'artifacts/th16/shot-selection-native.json').write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),resources=resources,rows=rows),separators=(',',':'))+'\n',encoding='utf8');print(f'{len(rows)} native TH16 main/season shot selections')
if __name__=='__main__':main()
