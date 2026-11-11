"""Extend the retained original geometry oracle through actual cache submission."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';H=H/'rotations'if '--rotations'in sys.argv else H;O=H/'native-submit-query';assert not O.exists();O.mkdir();meta=json.loads((H/'native.json').read_bytes());geometry=(H/'outputs.u32').read_bytes();assert hashlib.sha256(geometry).hexdigest()==meta['outputSha256']
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(im.data).hexdigest()==meta['executableSha256'];m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 first=va&~4095;m.mem_map(first,((va+size+4095)&~4095)-first);m.mem_write(va,im.data[off:off+n])
B=0x70000000;VM=B+0x1000;MANAGER=B+0x9000;STACK=B+0xff000;m.mem_map(B,0x100000)
reports=[]
for route in ['draw','ascii']:
 selected=geometry
 if route=='ascii':
  query=json.loads((H/'native-query/native.json').read_bytes());selected=(H/'native-query/outputs.u32').read_bytes();assert hashlib.sha256(selected).hexdigest()==query['outputSha256']
 outputs=bytearray()
 for i,row in enumerate(meta['rows']):
  pixel=int(route=='ascii'or row['mode']==0);raw=selected[i*48:(i+1)*48]
  for v in range(4):m.mem_write(0x4fd218+v*28,raw[v*12:(v+1)*12]+struct.pack('<fIII',1,0,0,0))
  m.mem_write(STACK,struct.pack('<3I',0,VM,pixel))
  for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,MANAGER),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
  m.emu_start(0x4756e0,0x47589b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x47589b
  outputs.extend(m.mem_read(VM+0x4f8,48))
 name=route+'-outputs.u32';(O/name).write_bytes(outputs);reports.append(dict(route=route,cases=meta['cases'],sha256=hashlib.sha256(outputs).hexdigest(),path=name))
j=dict(cases=meta['cases'],routes=reports,actualOriginalSubmitSlice='4756e0..47589b',actualOriginalX87PixelRounding=True,actualOriginalPositionCacheStores=True,declaredManagerOffsetZero=True,preSubmitDrawGeometrySha256=meta['outputSha256'],preSubmitQueryGeometrySha256=query['outputSha256'],toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),executableSha256=meta['executableSha256'],noGpuOrMaterialExecuted=True,newGameRuns=0,audibleOutput=False,completeGame=False)
(O/'native.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j))
