"""Actual 451430 collector; 404ca0/4061f0/math execute natively.
Area callbacks are recorded, with supplied returns. Bomb class is inactive.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,player,manager,resource,p,sizeptr,bomb,last,cb,stack=0x70000000,0x70001000,0x70020000,0x70021000,0x70022000,0x70022020,0x70022040,0x70022060,0x70023000,0x700ff000;m.mem_map(end,0x100000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]
 def floats(p,*v):m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
 calls=[]
 def callback(machine,a,length,user):
  area=m.reg_read(UC_X86_REG_ECX);j=(area-player-0xde18)//0xa4;calls.append(j);m.reg_write(UC_X86_REG_EAX,(get(area+0x84)-j-1)&0xffffffff)
 m.mem_write(cb,b'\xc2\x0c\x00');m.hook_add(UC_HOOK_CODE,callback,begin=cb,end=cb)
 rows=[]
 for n in range(12288):
  calls.clear();m.mem_write(player,bytes(0x19000));m.mem_write(manager,bytes(0x100));m.mem_write(stack-0x3000,bytes(0x3100))
  advanced=n//3%2;probe=n//6%2;argument=73;stamp=(0,1,7)[n//12%3];cap=(0,30,220)[n//36%3];rect=n//108%2;score=(0,999999998,999999999)[n//216%3]
  angle=(0.,.5,-1.25,3.1415927410125732)[n//648%4];sx,sy=((48.,32.),(192.,32.),(0.,0.))[n//2592%3];radius=(0.,4.,48.)[n%3]
  geometry=[bits(v) for v in (17.,123.,.1,sx,sy,radius,angle)];inputs=[advanced,probe,argument,stamp,cap,rect,score,*geometry]
  floats(p,17,123,.1);floats(sizeptr,sx,sy);put(bomb,77);floats(last,111,222,333);put(0x4db67c,player);put(0x4db52c,manager);put(player+0x688,resource);put(player+0x68c,10-advanced);put(player+0x690,10);put(resource+0x28,cap);put(0x4f5830,score)
  for j in range(3):
   a=player+0xde18+j*0xa4;flags=((2,3,7) if n<6144 else (0,1,5))[(n+j)%3];r=(0.,4.,16.,40.)[(n//3+j)%4];x,y=((17.,123.),(41.,123.),(17.,155.),(57.,155.),(217.,323.),(-23.,91.))[(n//12+j)%6];prev=8 if (n//72+j)%2 else 7;cur=8;period=(1,2,3)[(n//144+j)%3];damage=(19,250,-20)[j];total=(0,18,30)[(n//432+j)%3];maximum=(0,20,9999999)[(n//1296+j)%3];tag=(0,1,7)[(n//3888+j)%3];callback_id=(n//216+j)%2
   width,height=((0.,0.),(48.,16.),(32.,192.),(16.,16.))[(n//3+j)%4];area_angle=(0.,.5,-1.25,-1.5707963705062866)[(n//12+j)%4]
   values=[flags,bits(r),bits(area_angle),bits(width),bits(height),bits(x),bits(y),bits(.2+j),prev,cur,bits(8),damage,total,maximum,period,tag,callback_id,999]
   inputs.extend(v&0xffffffff for v in values)
   for off,v in zip((0x10,0x14,0x1c,0x24,0x28,0x2c,0x30,0x34,0x70,0x74,0x78,0x84,0x88,0x8c,0x90,0x94,0xa0,0x9c),values):put(a+off,cb if off==0xa0 and callback_id else v)
  args=[p,sizeptr if rect else 0,bits(radius),bomb,last,probe,argument,stamp];put(stack,end)
  for j,v in enumerate(args):put(stack+4+j*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM3,bits(angle));m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x451430,end,count=200000);assert m.reg_read(UC_X86_REG_EIP)==end
  result=[m.reg_read(UC_X86_REG_EAX),get(bomb),get(last),get(last+4),get(last+8),get(0x4f5830),sum(1<<j for j in calls)]
  for j in range(3):result.extend(get(player+0xde18+j*0xa4+off) for off in (0x10,0x88,0x84,0x94,0x9c))
  rows.append(dict(input=inputs,result=result,calls=calls[:]))
 out=ROOT/'artifacts/th14/shot-damage-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} damage collector cases.')
if __name__=='__main__':main()
