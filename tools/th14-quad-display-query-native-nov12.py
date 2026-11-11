"""Actual query geometry for the ASCII submit path, distinct from draw mode3."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/quad-display-space-nov12';H=H/'rotations'if '--rotations'in sys.argv else H;O=H/'native-query';assert not O.exists();O.mkdir();meta=json.loads((H/'native.json').read_bytes());inputs=(H/'inputs.bin').read_bytes();assert hashlib.sha256(inputs).hexdigest()==meta['inputSha256'];sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(im.data).hexdigest()==meta['executableSha256'];m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 first=va&~4095;m.mem_map(first,((va+size+4095)&~4095)-first);m.mem_write(va,im.data[off:off+n])
B=0x70000000;VM=B+0x1000;PARENT=B+0x3000;OUTPUT=B+0x7000;STACK=B+0xff000;STOP=B+0xfe000;m.mem_map(B,0x100000);m.mem_write(0x4854a0,b'\xc3');put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));out=bytearray();anchors=[(0,0),(1,2),(2,1)]
for row in meta['rows']:
 raw=inputs[row['input']*3000:(row['input']+1)*3000];width,height,scale,ox,oy,sx,sy,parent=struct.unpack_from('<8I',raw)
 for address,value in [(0x4f7a64,width),(0x4f7a68,height),(0x4f7a6c,scale),(0x4f7a80,ox),(0x4f7a84,oy),(0x4f7a88,sx),(0x4f7a8c,sy)]:put(address,value)
 m.mem_write(VM,raw[32:32+1484]);m.mem_write(PARENT,raw[32+1484:]);put(VM+0x594,PARENT if parent else 0);flags=struct.unpack_from('<I',raw,32+0x18)[0];ax,ay=anchors[row['anchor']];put(VM+0x18,(flags&~((31<<25)|(3<<21)|(3<<23)))|(row['mode']<<25)|(ax<<21)|(ay<<23));before=bytes(m.mem_read(VM,1484))
 m.mem_write(OUTPUT,bytes(48));m.mem_write(STACK,struct.pack('<2I',STOP,OUTPUT))
 for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,VM),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
 m.emu_start(0x479560,STOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==STOP and bytes(m.mem_read(VM,1484))==before;out.extend(m.mem_read(OUTPUT,48))
(O/'outputs.u32').write_bytes(out);report=dict(cases=meta['cases'],entry='479560',outputSha256=hashlib.sha256(out).hexdigest(),inputSha256=meta['inputSha256'],toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),allRotationsZero=meta['allRotationsZero'],drawMode3AndQueryMode3RemainDistinct=True,actualOriginalAsciiWrapperNotExecuted=True,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False);(O/'native.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
