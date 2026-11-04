"""Execute original perspective publication phases and worker copies on synthetic cameras."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();OUT=args.output.resolve()
assert OUT.is_relative_to(ROOT/'artifacts/th14');OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'tools'));Image=importlib.import_module('th12-pe').Image
sha=lambda b:hashlib.sha256(b).hexdigest()
image=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for source in [image,dll]:
 for _,address,size,raw,count in source.sections:
  page=address&~4095;m.mem_map(page,((address+size+4095)&~4095)-page);m.mem_write(address,source.data[raw:raw+count])
BASE,STACK,RETURN,CAMERA,DEVICE,TABLE=0x70000000,0x700ff000,0x700fe000,0x70001000,0x70002000,0x70003000
m.mem_map(BASE,0x100000);m.mem_map(0,4096)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
word=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
matrices=[]
def matrix_sink(machine,pc,size,data):
 sp=machine.reg_read(UC_X86_REG_ESP);matrices.append((word(sp+8),bytes(m.mem_read(word(sp+12),64))));machine.reg_write(UC_X86_REG_EAX,0)
m.mem_write(RETURN+0x100,b'\xc2\x0c\x00');m.hook_add(UC_HOOK_CODE,matrix_sink,begin=RETURN+0x100,end=RETURN+0x100)
put(DEVICE,TABLE);put(TABLE+0xb0,RETURN+0x100);put(0x4d8f68,DEVICE);put(0x4f56cc,0)
def run(entry,args=()):
 m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),RETURN,*args));m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,0)
 m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
 m.emu_start(entry,RETURN,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
# Pin the same real D3DX baseline/CPU dispatch bootstrap as the existing oracle.
m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,[0x101ca068])
pe=struct.unpack_from('<I',dll.data,0x3c)[0];directory=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
functions,names,ordinals=[dll.image_base+dll.u32(directory+o)for o in (28,32,36)];exports={}
for n in range(dll.u32(directory+24)):
 name=dll.read(dll.image_base+dll.u32(names+n*4),128).split(b'\0')[0].decode();ordinal=struct.unpack('<H',dll.read(ordinals+n*2,2))[0];exports[name]=dll.image_base+dll.u32(functions+ordinal*4)
for slot,name in [(0x4b12ec,'D3DXMatrixLookAtLH'),(0x4b12e8,'D3DXMatrixPerspectiveFovLH'),(0x4b12b8,'D3DXVec3Normalize')]:put(slot,exports[name])
def perspective(raw):
 m.mem_write(CAMERA,raw+bytes(0x12c-len(raw)));matrices.clear();run(0x446400,[CAMERA])
 assert [kind for kind,_ in matrices]==[2,3]
 return bytes(m.mem_read(CAMERA+0x30,12)),bytes(m.mem_read(CAMERA+0x58,128)),list(matrices)

# Capture exact main instruction boundaries; replay each snapshot through the
# original worker REP. Component inputs and cuts are synthetic, not live clocks.
WORLD,SCENE=0x4d9514,0x70010000
boundaries=[(0,0x446426),(1,0x4464a4),(2,0x446517),(3,0x446594),(4,0x4465a0),(5,0x4465a6)]
captured={}
def checkpoint(machine,pc,size,user):
 for point,address in boundaries:
  if pc==address:captured[point]=bytes(m.mem_read(WORLD,300))
m.hook_add(UC_HOOK_CODE,checkpoint,begin=0x446400,end=0x4465a6)
profiles=[((0.,0.,1.),(0.,1.,0.)),((2.,3.,4.),(0.,1.,0.)),((.25,-.75,1.5),(.1,1.,.2)),((0.,0.,0.),(0.,1.,0.))]
rows=[]
for profile,(direction,up)in enumerate(profiles):
 initial=bytearray(300)
 for offset,values in [(0,(12.5,-3.25,-600.)),(12,(0.,300.,600.)),(24,up),(36,direction),(48,(9.,8.,7.)),(60,(1.,2.,3.)),(72,(.5,-.5,.25))]:struct.pack_into('<3f',initial,offset,*values)
 struct.pack_into('<f',initial,84,.5235987901687622);struct.pack_into('<II',initial,88,0x12345678,0xabcdef01)
 struct.pack_into('<4I2f',initial,224,32,16,384,448,0.,1.)
 struct.pack_into('<I2f3f',initial,248,3,.25,-.5,.125,.25,.5)
 struct.pack_into('<6fI',initial,272,1000.,5000.,160.,170.,180.,255.,0xffb4aaa0)
 captured.clear();m.mem_write(WORLD,bytes(initial));matrices.clear();run(0x446400,[WORLD]);assert len(captured)==6 and [kind for kind,_ in matrices]==[2,3]
 for point,pc in boundaries:
  snapshot=captured[point];m.mem_write(WORLD,snapshot);m.mem_write(SCENE+0x4274,bytes([0xcc])*300);m.reg_write(UC_X86_REG_EBX,SCENE);m.reg_write(UC_X86_REG_EFLAGS,2)
  m.emu_start(0x40d435,0x40d447,count=100);copied=bytes(m.mem_read(SCENE+0x4274,300));assert copied==snapshot
  mapped=b''.join(copied[a:a+n]for a,n in[(0,72),(84,4),(96,204),(72,12)])
  rows.append(dict(profile=profile,point=point,mainPc=pc,nativeInputHex=bytes(initial).hex(),nativeCopiedCameraHex=copied.hex(),mappedCppHex=mapped.hex(),mappedCppSha256=sha(mapped),rightBits=list(struct.unpack_from('<3I',copied,48))))
result=dict(verifiedOriginalPerspectiveBoundariesAndWorkerCopy=True,profiles=len(profiles),mainPerspectiveExecutions=len(profiles),workerCopyExecutions=len(rows),mainBoundaryPcs=[pc for _,pc in boundaries],rows=rows,nativeExeSha256=sha(image.data),nativeD3dxSha256=sha(dll.data),syntheticInputsAndSchedule=True,matrixInternalStoresNotObserved=True,unmappedNativeWordIndices=[22,23],physicalAudioDevicesOpened=0,liveOriginalProcess=False,oldOriginalScheduleRecovered=False,oldFailureClosed=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
(OUT/'verified.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='rows'}),flush=True)
