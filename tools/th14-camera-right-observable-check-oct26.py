"""Test cached-right influence at original perspective recomputation."""
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
cases=[
 ('easy','retail-reimub-easy-camera-phases-hardware-oct25','stage-item-retirement-oct25/old-easy-resource-player-full-oct26'),
 ('lunatic','retail-reimub-lunatic-timeline-clear-hardware-oct25','stage-item-retirement-oct25/timeline-clear-full'),
 ('reimua-easy','retail-reimua-easy-timeline-clear-hardware-oct25','stage-item-retirement-oct25/reimua-easy-full'),
]
results=[];bindings={}
for name,native,model in cases:
 home=ROOT/'artifacts/th14'/native;portable=ROOT/'artifacts/th14'/model
 camera_path=home/'world-camera.raw';camera=camera_path.read_bytes();p_path=portable/'portable-camera.u32';p=p_path.read_bytes();count=len(p)//100;assert len(camera)==count*0x124
 different=[n for n in range(count)if camera[n*0x124+0x30:n*0x124+0x3c]!=p[n*100+48:n*100+60]];assert different
 candidates=sorted(set([different[0],different[-1],*[different[i]for i in range(0,len(different),max(1,len(different)//8))]]))
 bindings[camera_path.relative_to(ROOT).as_posix()]=sha(camera);bindings[p_path.relative_to(ROOT).as_posix()]=sha(p)
 for index in candidates:
  original=camera[index*0x124:(index+1)*0x124];changed=bytearray(original);changed[0x30:0x3c]=p[index*100+48:index*100+60]
  assert changed!=original
  a=perspective(original);b=perspective(bytes(changed));assert a==b,(name,index)
  positive=bytearray(original);fov=struct.unpack_from('<f',original,0x54)[0];struct.pack_into('<f',positive,0x54,fov*.875)
  c=perspective(bytes(positive));assert a!=c
  results.append(dict(case=name,callback=index+1,changedOnlyCachedRight=True,recomputedRightViewProjectionAndDeviceTransformsByteIdentical=True,fovPositiveControlChanged=True,outputSha256=sha(a[0]+a[1]+b''.join(data for _,data in a[2]))))
result=dict(verifiedOriginalInstructionComponent=True,cases=results,caseCount=len(results),originalExecutableSha256=sha(image.data),d3dxSha256=sha(dll.data),allCachedRightChangesErasedAtPerspective=True,allFovPositiveControlsChanged=True,bindings=bindings,toolSha256=sha(Path(__file__).read_bytes()),scope='Original446400 and real32 D3DX instructions with recorded camera inputs; only device SetTransform is a sink. Tests cached-right influence at this recomputation boundary, not every game draw caller, actual HAL/WebGL pixels, lifecycle or whole-game equivalence.',nativeProcessOrGpuRun=False,rawCameraDifferencesStillRetained=True,completeGame=False,nativeEquivalent=False)
(OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['caseCount','allCachedRightChangesErasedAtPerspective','allFovPositiveControlsChanged']}))
