"""Execute retail callback 1 (42c8a0); linked active-bullet inputs are controlled."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,enemy,manager,nodes,bullets,stack=0x70000000,0x70001000,0x70010000,0x70020000,0x70030000,0x700ff000;m.mem_map(end,0x1000000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 rows=[];put(0x4db530,manager)
 for variant in range(32):
  for count in range(9):
   m.mem_write(enemy,bytes(0x4200));m.mem_write(nodes,bytes(0x1000));m.mem_write(stack-0x1000,bytes(0x1100));x,y=12.25,-80.5
   radius=(-1.,0.,1.,3.5,20.,200.,float('inf'),float('nan'))[variant%8]
   initial=[bits(x),bits(y),bits(radius),0x12345678,bits(-12.5),bits(48.75)];put(enemy+0x44,initial[0]);put(enemy+0x48,initial[1]);put(enemy+0x2a8,initial[2]);put(enemy+0x28c,initial[3]);put(enemy+0x29c,initial[4]);put(enemy+0x2a0,initial[5])
   put(manager+0x80,nodes if count else 0)
   for j in range(count):
    row=[(variant+j)%5,bits(x+(-20.,-1.,0.,1.,3.5,20.,-3.5,1.)[j]),bits(y+(-20.,0.,0.,0.,0.,0.,0.,0.)[j])];initial.extend(row)
    p=bullets+j*0x1000;put(nodes+j*8,p);put(nodes+j*8+4,nodes+(j+1)*8 if j+1<count else 0);put(p+0xbe8,row[0]);put(p+0xbc0,row[1]);put(p+0xbc4,row[2])
   put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
   m.emu_start(0x42c8a0,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
   rows.append(dict(input=initial,count=count,result=[get(enemy+0x28c),get(enemy+0x29c),get(enemy+0x2a0)]))
 visual=[];vm=end+0x60000;callback=end+0x90000;deliveries=[];put(0x4d9128,vm);m.mem_write(callback,b'\xc3')
 def deliver(machine,address,size,user):
  assert m.reg_read(UC_X86_REG_ECX)==vm
  deliveries.append([m.reg_read(UC_X86_REG_EDX),get(vm+0x4a0)]);put(vm+0x4a0,0x12345678)
 m.hook_add(UC_HOOK_CODE,deliver,begin=callback,end=callback)
 for value in (-2147483648,-65536,-32776,-8,-7,-6,-1,0,1,32761,65529,65530,2147483641,2147483647):
  for present in (0,1):
   for prior in (0,42,0xffffffff):
    deliveries.clear();m.mem_write(enemy,bytes(0x4200));m.mem_write(vm,bytes(0x600));put(enemy+0x28c,value);put(vm+0x4a0,prior);put(vm+0x5c4,callback if present else 0)
    put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.emu_start(0x42c990,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
    visual.append(dict(value=value,present=present,prior=prior,result=get(vm+0x4a0),returned=m.reg_read(UC_X86_REG_EAX),deliveries=deliveries[:]))
 damage=[];owner=end+0xa0000;present=0;returns=[];calls=[]
 def damage_boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x47f0a0:
   assert get(sp+4)==37;m.reg_write(UC_X86_REG_EAX,vm if present else 0)
  else:
   p,box=get(sp+4),get(sp+8)
   assert get(sp+16)!=0 and [get(sp+j) for j in (20,24)]==[0,0]
   assert get(sp+28)==owner and get(sp+32)==0x76543210
   calls.append([get(p+j) for j in (0,4,8)]+[int(bool(box))]+([get(box),get(box+4)] if box else [0,0])+[get(sp+12),m.reg_read(UC_X86_REG_XMM3)&0xffffffff])
   m.reg_write(UC_X86_REG_EAX,returns[len(calls)-1]&0xffffffff)
 for address,cleanup in ((0x47f0a0,4),(0x451430,32)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,damage_boundary,begin=address,end=address)
 m.mem_write(0x4854a0,b'\xc3')
 for present in (0,1):
  for x in (-16777216.,-0.,12.25,16777216.):
   for scale in ((0.,0.),(-1.,1.),(.125,2.5),(float('inf'),float('nan'))):
    for angle in (-3.1415927410125732,0.,1.5707963705062866):
     for returns in ((0,0),(17,29),(2147483647,17),(-2147483648,-1)):
      calls.clear();m.mem_write(enemy,bytes(0x4200));m.mem_write(vm,bytes(0x600))
      inputs=[bits(x),bits(-80.5),bits(3.25),bits(scale[0]),bits(scale[1]),bits(angle)]
      for offset,value in zip((0x44,0x48,0x4c),inputs):put(enemy+offset,value)
      for offset,value in zip((0x60,0x64,0x50),inputs[3:]):put(vm+offset,value)
      put(enemy+0x128,37);put(enemy+0x40ec,owner);put(owner+0x11e4,0x76543210)
      initial=(0,71,-2147483648,2147483647)[len(damage)%4]
      put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_EDX,initial&0xffffffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
      m.emu_start(0x42c9c0,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
      damage.append(dict(present=present,input=inputs,initial=initial,returns=list(returns),calls=calls[:],result=m.reg_read(UC_X86_REG_EAX),animation=get(enemy+0x128)))
 setters=[];selected=0
 def read_index(machine,address,size,user):
  assert get(m.reg_read(UC_X86_REG_ESP)+4)==0;m.reg_write(UC_X86_REG_EAX,selected)
 m.mem_write(0x42c1d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,read_index,begin=0x42c1d0,end=0x42c1d0)
 for prior in (0,1,0x42c9c0,0xffffffff):
  for selected in (0,1):
   put(enemy+0x4114,prior);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(0x42762f,0x429c28,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x429c28
   result=get(enemy+0x4114);assert result in (0,0x42c9c0)
   setters.append(dict(prior=prior,index=selected,result=int(bool(result))))
 scale_callbacks=[];scale_requests=[]
 def scale_boundary(machine,address,size,user):scale_requests.append(m.reg_read(UC_X86_REG_XMM1)&0xffffffff)
 m.mem_write(0x4504c0,b'\xc3');m.hook_add(UC_HOOK_CODE,scale_boundary,begin=0x4504c0,end=0x4504c0)
 for index,entry in ((3,0x42cae0),(4,0x42caf0)):
  for value in (-float('inf'),-10.,-0.,0.,.5,1.,1.0000001192092896,2.,8.,float('inf'),float('nan')):
   scale_requests.clear();put(enemy+0x29c,bits(value));put(stack,end);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_ESP,stack)
   m.emu_start(entry,end,count=1000);assert m.reg_read(UC_X86_REG_EIP)==end
   scale_callbacks.append(dict(index=index,value=bits(value),requests=scale_requests[:],result=m.reg_read(UC_X86_REG_EAX)))
 freeze=[];sounds=[];player=end+0xb0000;put(0x4db67c,player)
 def sound_boundary(machine,address,size,user):
  sounds.append([get(m.reg_read(UC_X86_REG_ESP)+4),m.reg_read(UC_X86_REG_XMM2)&0xffffffff])
 m.mem_write(0x46e470,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,sound_boundary,begin=0x46e470,end=0x46e470)
 offsets=(0xbe8,0xc18,0xc20,0xc04,0xc0e,0xbc0,0xbc4)
 for variant in range(96):
  for count in range(9):
   sounds.clear();m.mem_write(enemy,bytes(0x4200));m.mem_write(nodes,bytes(0x1000))
   inner,outer=(-1.,0.,1.,3.5,20.,200.,float('inf'),float('nan'))[variant%8],(0.,1.,20.,float('inf'),float('nan'),-3.5)[variant%6]
   initial=[bits(12.25),bits(-80.5),bits(inner),bits(outer)];put(player+0x5e0,initial[0]);put(player+0x5e4,initial[1]);put(enemy+0x29c,initial[2]);put(enemy+0x2a0,initial[3]);put(manager+0x80,nodes if count else 0)
   for j in range(count):
    row=[(variant+j)%5,(0,2147483647,-2147483648,-1)[(variant+j)%4]&0xffffffff,(variant+j)%18,(0,1,0x100,0xffffffff)[(variant+j)%4],4,bits(12.25+(-20.,-1.,0.,1.,3.5,20.,float('nan'),float('inf'))[j]),bits(-80.5)]
    initial.extend(row);p=bullets+j*0x1000;m.mem_write(p,bytes(0x1000));put(nodes+j*8,p);put(nodes+j*8+4,nodes+(j+1)*8 if j+1<count else 0)
    for offset,value in zip(offsets,row):put(p+offset,value)
   frames=[]
   for tick in range(3):
    sounds.clear();put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.emu_start(0x42cb00,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end
    frames.append(dict(result=m.reg_read(UC_X86_REG_EAX),states=[[get(bullets+j*0x1000+o) if o!=0xc0e else int.from_bytes(m.mem_read(bullets+j*0x1000+o,2),'little') for o in offsets] for j in range(count)],sounds=sounds[:]))
   freeze.append(dict(input=initial,count=count,frames=frames))
 tags=[]
 for index in (0,5,14):
  for tag in (-2147483648,-1,0,1,2,2147483647):
   for active in (0,1,0x100,0x8000):
    for concurrent in (0,1):
     m.mem_write(bullets,bytes(0x2000));put(bullets+0xbe8,0x12345678);put(bullets+0xc20,index);put(bullets+0xc04,active)
     put(bullets+0xc28+index*0x2c+0x10,tag);put(bullets+0xc28+index*0x2c+0x20,0x8000);put(bullets+0xc28+index*0x2c+0x24,concurrent)
     put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,bullets)
     m.emu_start(0x418140,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
     tags.append(dict(index=index,tag=tag,active=active,concurrent=concurrent,result=[get(bullets+o) for o in (0xbe8,0xc20,0xc04)]))
 accelerations=[]
 for seed in (0,1,0x9630,0xffff,0x1234,0xabcd):
  for calls in (0,0xfffffffe):
   for count in range(9):
    m.mem_write(manager+0x9bf6c0,bytes(8));put(manager+0x80,nodes if count else 0);m.mem_write(0x4db510,struct.pack('<HHI',seed,0,calls));m.mem_write(0x4db508,struct.pack('<HHI',0x789a,0,17))
    for j in range(count):
     bullet=bullets+j*0x1000;m.mem_write(bullet,bytes(0x1000));put(nodes+j*8,bullet);put(nodes+j*8+4,nodes+(j+1)*8 if j+1<count else 0)
     for n in range(11):put(bullet+0xc54+n*4,0x12340000+j*0x100+n)
     put(bullet+0xc20,7);put(bullet+0xc04,0x100);m.mem_write(bullet+0xc0e,struct.pack('<H',4))
    put(stack,end);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(0x42cc70,end,count=10000);assert m.reg_read(UC_X86_REG_EIP)==end
    assert bytes(m.mem_read(0x4db508,8))==struct.pack('<HHI',0x789a,0,17)
    for j in range(count):assert get(bullets+j*0x1000+0xc20)==7 and get(bullets+j*0x1000+0xc04)==0x100
    accelerations.append(dict(seed=seed,calls=calls,count=count,result=[[get(bullets+j*0x1000+0xc54+n*4) for n in range(11)] for j in range(count)],rng=[get(0x4db510)&0xffff,get(0x4db514)]))
 out=ROOT/'artifacts/th14/enemy-callback-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=rows,visual=visual,damage=damage,damageSetters=setters,scaleCallbacks=scale_callbacks,freeze=freeze,tags=tags,accelerations=accelerations),indent=2)+'\n',encoding='utf-8');print(f'{len(rows)} nearest-bullet cases; {len(visual)} screen-copy interrupt cases; {len(damage)} damage geometry cases; {len(freeze)} freeze timelines; {len(tags)} script-tag cases.')
if __name__=='__main__':main()
