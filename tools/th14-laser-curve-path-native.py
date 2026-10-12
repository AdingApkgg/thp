"""Retail curve initialization, ETEX 4/8, sampling and strip vertex generation.
ANM binding/ticking and sound are explicit boundaries; geometry/math are native.
"""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main(inherited=False):
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 end,obj,request,manager,heap,stack=0x70000000,0x70001000,0x70004000,0x70005000,0x70010000,0x700ff000
 m.mem_map(end,0x100000);cursor=heap
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def words(p,n):return list(struct.unpack('<'+'I'*n,m.mem_read(p,4*n)))
 def bits(f):return struct.unpack('<I',struct.pack('<f',f))[0]
 def boundary(machine,a,size,user):
  nonlocal cursor
  sp=m.reg_read(UC_X86_REG_ESP)
  if a in (0x485540,0x4854af):
   n=get(sp+4);assert n<0x10000;m.mem_write(cursor,bytes(n));m.reg_write(UC_X86_REG_EAX,cursor);cursor+=(n+15)&~15
  else:m.reg_write(UC_X86_REG_EAX,0)
 for a,cleanup in ((0x485540,0),(0x4854af,0),(0x40cc90,0),(0x46f520,8),(0x40af00,8),(0x46fe50,0),(0x46e470,4)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def registers():
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
 def call(a,args=()):
  registers();m.mem_write(stack-0x2000,bytes(0x2100));put(stack,end)
  for i,v in enumerate(args):put(stack+4+i*4,v)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.emu_start(a,end,count=2000000);assert m.reg_read(UC_X86_REG_EIP)==end,hex(m.reg_read(UC_X86_REG_EIP))
 def nodes():
  p=obj+0x14b4;result=[]
  while p:
   row=words(p,15);result.append([0,0,*row[2:]]);p=row[0];assert len(result)<=37
  return result
 def samples():return [words(get(obj+0x14ac)+j*32,8) for j in range(get(obj+0x5e0))]
 def mesh():
  call_end=0x441dd3;registers();m.mem_write(stack-0x2000,bytes(0x2100));put(stack,end)
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,obj)
  m.emu_start(0x4418e0,call_end,count=2000000);assert m.reg_read(UC_X86_REG_EIP)==call_end
  return [words(get(obj+0x14b0)+j*28,7) for j in range(get(obj+0x5e0)*2)]
 real=json.loads((ROOT/'artifacts/th14/st04mbs-first-curve-request.json').read_text())['request']
 cases=[]
 requests=[real]
 for variant in range(12):
  r=[0]*213;r[0:6]=list(map(bits,(23.75,-17.25,3.5,(-3.15,-.125,200.)[variant%3],(0.,14.,23.5)[variant%3],(.125,4.,-2.)[variant%3])))
  r[8]=(1,2,7,120)[variant%4];r[9]=bits((-10.,0.,13.5)[variant%3]);r[0x344//4]=0xffffffff;r[0x348//4]=0xffffffff;r[0x350//4]=bits((0.,.5,7.25)[variant%3])
  for j in range(3):
   p=11+j*11;r[p]=bits((-.06333333,.1,.13333334)[j]);r[p+1]=bits((-999.,.001454441,.08144869655)[j]);r[p+4]=(0,7,30)[j];r[p+5]=(0,7,30)[j];r[p+8]=4 if variant%2 else 8;r[p+9]=1
  requests.append(r)
 for index,r in enumerate(requests):
  cursor=heap;m.mem_write(obj,bytes(0x3000));m.mem_write(request,struct.pack('<213I',*r));put(0x4db664,manager);put(manager+0x5f4,0)
  put(0x4d8f58,bits(1));put(0x4f7a88,224);put(0x4f7a74,16)
  for a in (0x4f7afc,0x4f7b00,0x4f7b04):put(a,0)
  call(0x4401d0,(request,));initial=samples();initial_nodes=nodes();copied=words(obj+0x5c0,213)
  call(0x441e40);generated=nodes();inherited_nodes=[]
  if inherited:
   inherited_nodes=generated;source=end+0x8000
   for j,row in enumerate(generated):
    clone=row[:];clone[0]=source+(j+1)*60 if j+1<len(generated) else 0;clone[1]=source+(j-1)*60 if j else 0;m.mem_write(source+j*60,struct.pack('<15I',*clone))
   cursor=heap;m.mem_write(obj,bytes(0x3000));clone_request=r[:];clone_request[0x34c//4]=source;m.mem_write(request,struct.pack('<213I',*clone_request))
   call(0x4401d0,(request,));initial=samples();initial_nodes=nodes();copied=words(obj+0x5c0,213);generated=nodes()
  put(obj+0xcd0,bits(.125));put(obj+0xce0,bits(.875))
  frames=[]
  for time in (0.,.125,.5,1.,7.,7.5,29.75,30.,59.,60.,60.5,89.,90.,119.,120.25,209.,210.,250.):
   put(obj+0x48,bits(time));registers();m.mem_write(stack-0x2000,bytes(0x2100));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ESI,obj)
   m.emu_start(0x440a7d,0x440b98,count=2000000);assert m.reg_read(UC_X86_REG_EIP)==0x440b98
   frames.append(dict(time=bits(time),samples=samples(),mesh=mesh()))
  recorded=r[:]
  if inherited:recorded[0x34c//4]=1
  cases.append(dict(request=recorded,inheritedNodes=inherited_nodes,initial=initial,initialNodes=initial_nodes,copied=copied,nodes=generated,transformIndex=get(obj+0x594),frames=frames))
 out=ROOT/('artifacts/th14/laser-curve-inherited-native.json' if inherited else 'artifacts/th14/laser-curve-path-native.json');out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),cases=cases),indent=2)+'\n',encoding='utf-8')
 print(f'{len(cases)} retail initializations / ETEX sequences, {sum(len(r["frames"]) for r in cases)} sampled and tessellated frames.')
if __name__=='__main__':main()
