"""Spatial diagnostic of retained particle states; never an acceptance mask."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12';O=H/'geometry-current';assert not O.exists();O.mkdir();bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
N=R/'artifacts/th14/current-startup-prefix-nov10/native';C=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state/application/current';P=R/'artifacts/th14/current-first-present-vm303-nov12';native=load(N/'live-vms-before-readback.json');canonical=load(P/'native-canonical.json');fields=canonical['fields'];field={s:i for i,s in enumerate(fields)};rawcpp=read(C/'target-live-vms.u32');words=struct.unpack('<'+'I'*(len(rawcpp)//4),rawcpp);assert words[:6]==(1,1,1,76,1,303);cpp=[list(words[i:i+303])for i in range(6,len(words),303)]
nr=load(N/'report.json');cr=load(C/'report.json');uv=load(C/'uv-repaint.json');assert nr['childExited']and cr['terminal']and cr['closed']and uv['counterfactualOnly']and uv['restoredPixelsExact']
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(im.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 first=va&~4095;m.mem_map(first,((va+size+4095)&~4095)-first);m.mem_write(va,im.data[off:off+n])
B=0x70000000;FRAME=B+0xfd000;STACK=B+0xff000;m.mem_map(B,0x100000);m.mem_map(0x74000000,0x100000);m.mem_write(0x4854a0,b'\xc3');put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda b,o:struct.unpack_from('<I',b,o)[0]
for p,v in [(0x4f7a64,640),(0x4f7a68,480),(0x4f7a6c,0x3f800000),(0x4f7a80,320),(0x4f7a84,16),(0x4f7a88,320),(0x4f7a8c,16)]:put(p,v)
# Captured Native addresses remain literal. CPP proxies use declared storage;
# only measured geometry fields are populated, with cached/clean flags.
native_rows=[];mapped={}
for row in native['rows']:
 raw=bytes.fromhex(row['rawVmHex']);address=get(raw,0x570);assert get(raw,0x540)==row['handle']
 for page in range(address&~4095,(address+len(raw)+4095)&~4095,4096):
  if page not in mapped:m.mem_map(page,4096);mapped[page]=True
 m.mem_write(address,raw);native_rows.append((row,address,raw))
cpp_address={row[0]:0x74000000+i*0x1000 for i,row in enumerate(cpp)};cpp_rows=[]
for row in cpp:
 value=lambda name:row[field[name]];raw=bytearray(1484)
 for name,bits in zip(fields,row):
  if name.startswith('nativeVmWord0x'):struct.pack_into('<I',raw,int(name.split('0x')[1],16),bits)
 for name,offset in [('worldX',0x59c),('worldY',0x5a0),('worldZ',0x5a4),('childX',0x4ec),('childY',0x4f0),('childZ',0x4f4),('pivotX',0x90),('pivotY',0x94)]:struct.pack_into('<I',raw,offset,value(name))
 flags=value('visible')|2|(value('drawingMode')<<25)|(value('anchorX')<<21)|(value('anchorY')<<23)
 struct.pack_into('<I',raw,0x18,flags);parent=value('parentHandle');assert not parent or parent in cpp_address;struct.pack_into('<I',raw,0x594,cpp_address[parent]if parent else 0)
 for prefix,offset in [('spriteMatrix',0x3e0),('transformMatrix',0x420)]:
  for i in range(16):struct.pack_into('<I',raw,offset+i*4,value(prefix+str(i)))
 address=cpp_address[row[0]];m.mem_write(address,bytes(raw));cpp_rows.append((dict(handle=row[0],file=row[1],script=row[2],ageCurrent=value('ageCurrent')),address,bytes(raw)))
sup=bytes.fromhex(load(N/'compositor-before-readback.json')['supervisorHex']);camera=0x488;view=struct.unpack_from('<16f',sup,camera+0x60);projection=struct.unpack_from('<16f',sup,camera+0xa0);viewport=struct.unpack_from('<4I2f',sup,camera+0xe0);assert viewport==(0,0,640,480,0.,1.)
def transform(v,a):return [sum(v[i]*a[i*4+j]for i in range(4))for j in range(4)]
def quad(address,raw):
 flags=get(raw,0x18);assert ((flags>>25)&31)==8 and not(flags&12)
 m.mem_write(FRAME-0x200,bytes(0x300));put(FRAME-0xd8,0)
 for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,FRAME),(UC_X86_REG_EBX,address),(UC_X86_REG_EAX,flags),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
 m.emu_start(0x477c64,0x4780a8,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x4780a8;m.emu_start(0x4781af,0x4781de,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x4781de;assert bytes(m.mem_read(address,1484))==raw
 matrix=list(struct.unpack('<16f',m.mem_read(FRAME-0xcc,64)));ax=(flags>>21)&3;ay=(flags>>23)&3;assert ax<3 and ay<3;left=[-128,0,-256][ax];top=[-128,0,-256][ay];points=[]
 for x,y in [(left,top),(left+256,top),(left,top+256),(left+256,top+256)]:
  clip=transform(transform(transform([x,y,0,1],matrix),view),projection);assert clip[3]>0
  points.append([(clip[0]/clip[3]+1)*320,(1-clip[1]/clip[3])*240])
 return points,matrix
quads=[];cases=[]
for side,rows in [('native',native_rows),('cpp-proxy',cpp_rows)]:
 for row,address,raw in rows:
  if (row['file'],row['script'])!=(2,16):continue
  if side=='cpp-proxy':color=next(r[field['nativeVmWord0x534']]for r in cpp if r[0]==row['handle'])
  else:color=get(raw,0x534)
  points,matrix=quad(address,raw);quads.append(points);cases.append(dict(side=side,handle=row['handle'],age=row['ageCurrent'],visibleAlpha=color>>24,points=points,world=matrix))
assert sum(x['side']=='native'for x in cases)==21 and sum(x['side']=='cpp-proxy'for x in cases)==20
def triangle(p,a,b,c):
 cross=lambda a,b,p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);v=[cross(a,b,p),cross(b,c,p),cross(c,a,p)];return all(x>=0 for x in v)or all(x<=0 for x in v)
def inside(p,q):return triangle(p,q[0],q[1],q[2])or triangle(p,q[1],q[3],q[2])
n=read(N/nr['readback']['file']);c=read(C/'counterfactual-native-uv.bgra');assert len(n)==len(c)==640*480*4
different=[p for p in range(640*480)if n[p*4:p*4+4]!=c[p*4:p*4+4]];alpha=[p for p in different if n[p*4+3]!=c[p*4+3]];assert len(different)==4460 and len(alpha)==3036
results=[]
for offset in [0.,.5]:
 outside=[p for p in different if not any(inside((p%640+offset,p//640+offset),q)for q in quads)];outside_alpha=[p for p in alpha if not any(inside((p%640+offset,p//640+offset),q)for q in quads)]
 results.append(dict(sampleOffset=offset,differentPixelsInsideUnion=len(different)-len(outside),outsideUnion=len(outside),alphaDifferentPixelsInsideUnion=len(alpha)-len(outside_alpha),alphaOutsideUnion=len(outside_alpha),outsideCoordinates=[[p%640,p//640]for p in outside]))
read(Path(__file__));report=dict(diagnosticOnly=True,originalStateSource='current adopted type0 batch fix with retained Native first-Present reference',actualNativeParticles=21,cppMeasuredProxyParticles=20,actualOriginalCachedWorldSlices=True,cppProxyUsesMeasured303GeometryFieldsOnly=True,cppProxyCleanCacheFlagDeclared=True,bothSidesUseCapturedNativeFullCamera=True,pythonDoubleProjectionNotGpuRounding=True,noClaimOfExactCoverageOrPixelCausality=True,footprints=results,differentFullPixelsAfterDiagnosticUvSwap=len(different),alphaDifferentPixels=len(alpha),noMaskUsedForAcceptance=True,strictWholeFrameStillFails=True,noLiveEngineStateChanged=True,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False,bindings=bindings)
(O/'particle-quads-private.json').write_text(json.dumps(cases,indent=2)+'\n');(O/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['bindings','footprints']}));print(json.dumps([{k:v for k,v in x.items()if k!='outsideCoordinates'}for x in results]))
