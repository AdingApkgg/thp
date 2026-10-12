"""Execute TH16's original ANM draw-registration constructor fragment."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,t,d=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x30000);stack,manager=0x7002e000,0x70001000
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 cursor=[0x70005000];rows=[]
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address in (0x4749ac,0x401730):
   p=cursor[0];cursor[0]+=128;m.mem_write(p,bytes(128));
   if address==0x4749ac:assert get(sp+4)==40
   else:m.mem_write(p+8,struct.pack('<I',get(sp+4)))
   m.reg_write(UC_X86_REG_EAX,p)
  else:
   node,priority=get(sp+4),get(sp+8);assert get(node+0x24) in (manager,0x4c10d0);rows.append(dict(priority=priority,callback=hex(get(node+8))))
 for addr,cleanup in ((0x4749ac,0),(0x401730,4),(0x4013b0,8)):
  m.mem_write(addr,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=addr,end=addr)
 m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack+256);m.reg_write(UC_X86_REG_EBX,manager)
 m.emu_start(0x46a769,0x46b741,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x46b741;assert len(rows)==39
 # Each wrapper's own first literal push is its layer when it calls 46e750.
 from capstone import Cs,CS_ARCH_X86,CS_MODE_32
 cs=Cs(CS_ARCH_X86,CS_MODE_32)
 for r in rows:
  ins=list(cs.disasm(img.read(int(r['callback'],16),16),int(r['callback'],16)))
  if ins[0].mnemonic=='push' and ins[1].mnemonic=='call' and ins[1].op_str=='0x46e750':r['layer']=int(ins[0].op_str,0)
  else:r['layer']=None
 # Execute every wrapper, with camera/device/draw operations recorded at boundaries.
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 events=[]
 def wrapper_boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x46e750:events.append(['layer',get(sp+4),get(0x4c17bc)]);m.reg_write(UC_X86_REG_EAX,1)
  elif address in (0x43c710,0x43c780):events.append(['camera' if address==0x43c710 else 'cameraPrepare',hex(get(sp+4))])
  elif address==0x7001a000:events.append(['viewport',hex(get(sp+8))])
  elif address==0x7001a010:events.append(['state',get(sp+8),get(sp+12)])
  else:events.append(['flush'])
 for addr,cleanup in ((0x46e750,4),(0x43c710,4),(0x43c780,4),(0x465a80,0),(0x7001a000,8),(0x7001a010,12)):
  m.mem_write(addr,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,wrapper_boundary,begin=addr,end=addr)
 put(0x4c10d8,0x70018000);put(0x70018000,0x70019000);put(0x70019000+0xbc,0x7001a000);put(0x70019000+0xe4,0x7001a010);put(0x4c0f48,manager)
 wrappers=[]
 for row in rows:
  for dirty in (0,1):
   put(stack,0x70000000);put(0x4c17b8,0x4c1560);put(0x4c17bc,2);put(0x4c1adc,dirty);put(0x4c1ae0,dirty);put(manager+0xd0,123);put(manager+0xd4,456);events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
   m.emu_start(int(row['callback'],16),0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
   layers=[e[1] for e in events if e[0]=='layer'];assert len(layers)==1
   if row['layer'] is None:row['layer']=layers[0]
   else:assert row['layer']==layers[0]
   wrappers.append(dict(callback=row['callback'],dirty=dirty,events=list(events),camera=get(0x4c17bc),offset=[get(manager+0xd0),get(manager+0xd4)]))
 # Other known constructor groups: Supervisor/compositor and Stage.
 anm_rows=rows.copy();groups={}
 for group,entry,end,expected in (('compositor',0x43ba8a,0x43bbac,10),('stage',0x4098e9,0x409925,2),('ascii',0x407d3f,0x407d9c,3),('player',0x4410b2,0x4410d0,1),('bullets',0x411a94,0x411ab2,1),('spell',0x41771f,0x41773d,1)):
  rows.clear();m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EBP,stack+256);m.reg_write(UC_X86_REG_EBX,manager);m.reg_write(UC_X86_REG_EDI,manager);m.emu_start(entry,end,count=100000);assert m.reg_read(UC_X86_REG_EIP)==end;assert len(rows)==expected;groups[group]=rows.copy()
 # Camera reset executes all stores/copies. Matrix preparation is a controlled
 # boundary: only viewport, mode, offsets and reset call order are observations.
 camera_rows=[]
 for width,height in ((640,480),(960,720),(1280,960)):
  put(0x4d9d2c,width);put(0x4d9d30,height);m.mem_write(0x4d9d34,struct.pack('<f',width/640));put(0x4d9d1c,0);events.clear()
  put(stack,0x70000000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,0x4c10d0);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x43cb10,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
  camera_rows.append(dict(width=width,height=height,cameras=[dict(viewport=list(struct.unpack('<4I2f',m.mem_read(p+0xe0,24))),mode=get(p+0xf8),offset=list(struct.unpack('<2I',m.mem_read(p+0xfc,8)))) for p in (0x4c1560,0x4c1308,0x4c1434,0x4c168c)],prepare=[e[1] for e in events if e[0]=='cameraPrepare']))
 # Composite callbacks draw four distinct embedded VMs; only A draws layer34.
 def copy_boundary(machine,address,size,user):events.append(['copy',get(m.reg_read(UC_X86_REG_ESP)+4)])
 m.mem_write(0x468490,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,copy_boundary,begin=0x468490,end=0x468490)
 put(0x4c127c,1);put(0x4a6eec,0);put(0x4a6ee8,0)
 for i in range(4):put(0x4c128c+4*i,0x70020000+i*0x1000)
 composite_rows=[]
 for callback in (0x43d2f0,0x43d4a0,0x43d640,0x43d7c0):
  put(stack,0x70000000);put(0x4c1ae0,1);events.clear();m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(callback,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
  composite_rows.append(dict(callback=hex(callback),events=list(events)))
 # Stage foreground's camera/state/layer prefix, before fog geometry drawing.
 m.mem_write(0x43c940,b'\xc2\x04\x00');put(manager+0x66c4,0);events.clear();put(stack,0x70000000);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager)
 m.emu_start(0x40a410,0x40a578,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x40a578
 foreground=list(events);assert [e[1] for e in foreground if e[0]=='layer']==[32,33]
 # Original resolution-specific copy binding fragment, with binder/update as
 # sinks; slots and filter flag changes are observations, not script execution.
 bindings=[]
 def bind_boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x407b20:events.append(['bind',(get(sp+4)-0x70020000)//0x1000,get(sp+8)])
  else:events.append(['update',(m.reg_read(UC_X86_REG_ECX)-0x70020000)//0x1000])
 for address,cleanup in ((0x407b20,8),(0x45f980,0)):
  m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,bind_boundary,begin=address,end=address)
 for width in (640,960,1280):
  put(0x4d9d2c,width);m.mem_write(0x4d9d34,struct.pack('<f',width/640));events.clear()
  for i in range(4):put(0x70020000+i*0x1000+0x530,0);put(0x70020000+i*0x1000+0x534,0xffffffff)
  m.mem_write(stack,struct.pack('<3I',0,0,0x70000000));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,0x4c10d0)
  m.emu_start(0x43d9dc,0x70000000,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x70000000
  bindings.append(dict(width=width,events=list(events),flags2=[get(0x70020000+i*0x1000+0x534) for i in range(4)]))
 rows=anm_rows
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),completeGame=False,scope='Original ANM, Supervisor, Stage, ASCII, player, bullet and spell constructor fragments execute 57 draw registrations. Node allocation/chain insertion are sinks. All39 ANM wrappers execute with camera preparation/application, viewport, state, flush and layer drawing at recorded boundaries; 78 cases include clean/dirty caches. Camera reset43cb10 executes viewport/mode/offset stores at three resolutions with matrix preparation controlled. Four compositor callbacks execute embedded-VM selection and A layer34; Stage foreground40a410..40a578 executes layer32/33 prefix. Copy binding43d9dc..43dc0f/22 selects four slots and filter at three resolutions with binder/update controlled. Matrices, full resource/script binding, stage geometry, other managers, device/GPU and full gameplay are excluded.',registrations=rows,wrapperCases=wrappers,otherRegistrationGroups=groups,cameraResetCases=camera_rows,compositeCases=composite_rows,foregroundPrefix=foreground,copyBindingCases=bindings)
 (ROOT/'docs/porting/th16-anm-draw-registrations.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
