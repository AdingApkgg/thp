"""Whole original40f2f0 layer state with real culling/D3DX, invisible VMs."""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/th14/stage-layer-state';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 Image=importlib.import_module('th12-pe').Image;image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for img in (image,dll):
  for _,b,size,raw,n in img.sections:
   first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
 base=0x70000000;stop=base;stack=base+0xff000;stage=base+0x1000;directory=base+0x6000;instances=base+0x7000;vms=base+0x8000;sprite=base+0xa000;device=base+0xb000;table=base+0xc000;manager=0x71000000;camera=0x4d9514
 m.mem_map(base,0x100000);m.mem_map(manager,0x1000000)
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];floats=lambda p,v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v));values=lambda p,n:list(struct.unpack('<'+'f'*n,m.mem_read(p,n*4)))
 def run(entry,args=(),ecx=0):
  m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),stop,*args));m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.emu_start(entry,stop,count=200000);assert m.reg_read(UC_X86_REG_EIP)==stop
 m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0];functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)];exports={}
 for i in range(dll.u32(export+24)):
  name=dll.cstring(dll.image_base+dll.u32(names+i*4),128);ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
 for slot,name in [(0x4b12d0,'D3DXMatrixTranslation'),(0x4b12f4,'D3DXVec3ProjectArray'),(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize')]:put(slot,exports[name])
 events=[];states={};draws=[];draw_states=[]
 def observe(uc,a,n,u):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==stop+0x100:key,value=get(sp+8),get(sp+12);states[key]=value;events.append([key,value])
  elif a==0x478f60:
   index=(get(sp+4)-vms)//0x5cc;draws.append(index);draw_states.append([index,states[14],states[28]])
 for offset,address,cleanup in [(0xe4,stop+0x100,12),(0xb0,stop+0x110,12),(0xbc,stop+0x120,8)]:put(table+offset,address);m.mem_write(address,b'\xc2'+struct.pack('<H',cleanup));m.hook_add(UC_HOOK_CODE,observe,begin=address,end=address)
 m.mem_write(0x475eb0,b'\xc3');m.mem_write(0x4854a0,b'\xc3');m.hook_add(UC_HOOK_CODE,observe,begin=0x478f60,end=0x478f60)
 put(device,table);put(0x4d8f68,device);put(0x4f56cc,manager);put(0x4f7a70,32);put(0x4f7a74,16);rows=[]
 for layer,mode,initial_depth,initial_fog,mask in itertools.product(range(12),(0,4,8,23,24,31),range(2),range(2),(0,1,2,3,8,9,10,11,16,17,18,19)):
  m.mem_write(stage,bytes(0x4500));m.mem_write(camera,bytes(0x12c));floats(camera,[0,0,-600,0,0,1,0,1,0,0,0,1]);floats(camera+0x54,[.5235987901687622]);m.mem_write(camera+0xe0,struct.pack('<4I2f',116,4,408,472,0,1));put(stage+0x14,directory);put(stage+0x18,instances);put(stage+0x208,vms);floats(stage+0x308c,[9610000]);floats(sprite+0x34,[48,32]);m.mem_write(vms,bytes(4*0x5cc))
  for i in range(4):
   obj=base+0xd000+i*0x100;put(directory+i*4,obj);m.mem_write(obj,bytes(0x100));m.mem_write(obj,struct.pack('<hBB6f',i,layer if i!=2 else (layer+1)%12,1,0,0,1000,64,64,64));m.mem_write(obj+0x1c,struct.pack('<4h5f',1 if i==3 or mask&8 else 0,28,i,i,3.25,-7.5,2.75,64,96));m.mem_write(obj+0x38,b'\xff\xff');m.mem_write(instances+i*16,struct.pack('<2h3f',i,2,20000 if i==1 and not mask&16 else 0,0,0));vm=vms+i*0x5cc;put(vm+0x18,(mode<<25)|(0x2000 if mask&(1<<(i%2)) else 0));put(vm+0x2c,sprite);floats(vm+0x60,[1,1]);floats(vm+0x59c,[11,13,17])
  m.mem_write(instances+64,b'\xff\xff');put(0x4d9964,initial_depth);put(0x4d9960,initial_fog);events.clear();draws.clear();draw_states.clear();states.clear();states.update({14:initial_depth,28:initial_fog});run(0x40f2f0,(layer,),stage)
  rows.append(dict(input=[layer,mode,initial_depth,initial_fog,mask],status=m.reg_read(UC_X86_REG_EAX),counts=[get(stage+0x4218),get(stage+0x421c),get(stage+0x4220)],objects=[m.mem_read(base+0xd000+i*0x100+3,1)[0] for i in range(4)],instances=[struct.unpack('<h',m.mem_read(instances+i*16+2,2))[0] for i in range(4)],vms=[values(vms+i*0x5cc+0x59c,3)+values(vms+i*0x5cc+0x60,2)+[int(bool(get(vms+i*0x5cc+0x18)&8))] for i in range(4)],finalDepth=states[14],finalFog=states[28],drawCalls=draws.copy(),drawStates=draw_states.copy(),stateEvents=events.copy()))
 report=dict(passed=True,completeGame=False,nativeEquivalent=False,executableSha256=sha(image.data),dllSha256=sha(dll.data),functionSha256=sha(image.read(0x40f2f0,0x316)),rows=rows,toolSha256=sha(Path(__file__).read_bytes()),scope='Whole original40f2f0 layer traversal including actual4107b0 with all eight standalone slots empty, actual40ebc0 and pinned32 D3DX, original478f60 early invisible rejection. Four synthetic objects/instances exercise layer filtering, distance culling, skipped primitive type, empty/single/two primitive submissions, mode>=4 position/size preparation, depth masks and fog transitions. Draw-boundary state and final layer state both observed. Only COM calls, flush and stack cookie are controlled; no visible ANM geometry/GPU/full stage/world proof.')
 (OUT/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8');print('PASS original whole layer',len(rows))
if __name__=='__main__':main()
