"""Retail loading create/finish wrappers; ANM creation and handle lookup controlled."""
import importlib,json,struct,hashlib
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,*_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  p=b&~4095;m.mem_map(p,((b+size+4095)&~4095)-p);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x40000);owner=base+0x1000;resource=base+0x20000;vm=base+0x21000;stack=base+0x3f000;calls=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x47ed10:
   assert uc.reg_read(UC_X86_REG_ECX)==resource
   p=get(sp+12);calls.append(dict(script=get(sp+8),position=list(struct.unpack('<3I',m.mem_read(p,12))),rotation=get(sp+16),layer=get(sp+20),flags=get(sp+24),output=get(sp+28)))
   put(get(sp+4),79);uc.reg_write(UC_X86_REG_EAX,get(sp+4));pop=28
  elif a==0x47f140:calls.append(dict(handle=get(sp+4),label=get(sp+8)));pop=8
  else:return
  uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+pop)
 for a in (0x47ed10,0x47f140):m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 rows=[]
 for handle in (0,79):
  for x in (-2.25,0,480,16777216):
   for y in (-8.25,0,392):
    m.mem_write(base,bytes(0x3e000));put(0x4db520,owner);put(owner+0x191e4,resource);put(owner+0x191ec,handle);calls.clear();put(stack,base)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_XMM1,struct.unpack('<I',struct.pack('<f',x))[0]);m.reg_write(UC_X86_REG_XMM2,struct.unpack('<I',struct.pack('<f',y))[0]);m.emu_start(0x420d20,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
    rows.append(dict(initialHandle=handle,x=x,y=y,finalHandle=get(owner+0x191ec),calls=calls[:]))
 finishes=[]
 for handle in (0,79,0xffffffff):
  put(owner+0x191ec,handle);calls.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x420ca0,base,count=10000);assert m.reg_read(UC_X86_REG_EIP)==base
  finishes.append(dict(handle=handle,finalHandle=get(owner+0x191ec),calls=calls[:]))
 # The original script17 has no sprite binding of its own. Child factory
 # calls are observed while the complete retail interpreter advances it.
 canonical=bytearray.fromhex(json.loads((ROOT/'docs/porting/th14-startup-session-observed-oct11.json').read_text())['scripts']['2:17'])
 inverse={28686:306,28932:307,28928:304,28934:313,51:403,90:501,92:503,4:200,64:5,1:1};at=0
 while at+8<=len(canonical):
  op,length=struct.unpack_from('<hH',canonical,at)
  if op==-1:break
  struct.pack_into('<h',canonical,at,inverse[op]);at+=length
 code=base+0x22000;child_calls=[]
 def child_hook(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP);child_calls.append([get(sp+8),get(sp+16)]);put(get(sp+4),99)
  uc.reg_write(UC_X86_REG_EAX,get(sp+4));uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+20)
 m.hook_add(UC_HOOK_CODE,child_hook,begin=0x47ee90,end=0x47ee90);m.mem_write(0x4854a0,b'\xc3')
 timelines=[]
 for duration in (0,1,2,5,9,44,134,180):
  m.mem_write(vm,bytes(0x700));m.mem_write(code,bytes(canonical));put(0x4d8f58,0x3f800000);m.mem_write(0x4f5815,b'\0')
  for o,v in [(0x18,7),(0x1c,0x200),(0x28,code),(0x30,resource),(0x38,code),(0x548,0xffffffff),(0x554,0x4d8f58),(0x558,1),(0x55c,0xffffffff),(0x568,0x4d8f58),(0x56c,1),(0x580,vm),(0x534,0xffffffff)]:put(vm+o,v)
  for o in (0x60,0x64):put(vm+o,0x3f800000)
  frames=[];child_calls.clear();put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm);m.emu_start(0x46fe50,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
  for frame in range(1,duration+21):
   if frame==duration+1:put(vm+0x4a0,1)
   put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,vm);m.emu_start(0x46fe50,base,count=100000);assert m.reg_read(UC_X86_REG_EIP)==base
   status=m.reg_read(UC_X86_REG_EAX);frames.append(dict(frame=frame,status=status,timer=get(vm+0x54c),calls=child_calls[:]))
   if status:break
  timelines.append(dict(duration=duration,frames=frames))
 result=dict(passed=True,executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,finishes=finishes,timelines=timelines,scope='Whole420d20 loading creation and420ca0 completion wrappers, resource factory and interrupt delivery controlled. Whole46fe50 interpreter advances original ascii script17 with controlled child factory, observing complete request timelines and deferred exit. Script opcodes restored from the production loader translation of the original archive. Actual loading duration, GPU and child ANM state excluded; factory output pointer is a controlled argument.')
 (ROOT/'artifacts/th14/loading-native.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} retail loading creation and {len(finishes)} finish observations')
if __name__=='__main__':main()
