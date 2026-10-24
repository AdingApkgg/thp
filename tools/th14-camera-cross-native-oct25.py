"""Original446539..4465a6 right-axis arithmetic with actual x86 D3DX normalize."""
from pathlib import Path
import hashlib,importlib,json,random,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_MXCSR
ROOT=Path(__file__).resolve().parents[1]
def main():
 sys.path.insert(0,str(ROOT/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,off,count in image.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[off:off+count])
 home=ROOT/'artifacts/th14/camera-cross-oct25/unit';home.mkdir(parents=True,exist_ok=True);base=0x70000000;m.mem_map(base,0x100000);camera=base+0x1000;up=base+0x2000;ebp=base+0xf0000;service=base+0xe0000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));word=lambda f:struct.unpack('<I',struct.pack('<f',f))[0];vectors=importlib.import_module('th14-d3dx-windows').WindowsVectors(m,service,home/'d3dx');put(0x4b12b8,service)
 rng=random.Random(14446539);inputs=[list(map(word,v))for v in [(0,0,1,0,1,0),(0,0,0,0,0,0),(0,.44721359,.89442718,0,1,0),(1,1,1,1,-1,0),(-0.,0.,-0.,0.,-0.,0.)]]
 for i in range(2048):inputs.append([word(rng.uniform(-8,8))for _ in range(6)])
 rows=[]
 try:
  for words in inputs:
   m.mem_write(camera,bytes(0x124));m.mem_write(up,struct.pack('<3I',*words[3:]));m.mem_write(ebp-0x2c,struct.pack('<3I',*words[:3]));put(ebp-0x20,camera);m.reg_write(UC_X86_REG_EBX,up);m.reg_write(UC_X86_REG_EBP,ebp);m.reg_write(UC_X86_REG_ESP,ebp-0x50);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
   m.emu_start(0x446539,0x4465a0,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x4465a0;cross=list(struct.unpack('<3I',m.mem_read(camera+0x30,12)));m.emu_start(0x4465a0,0x4465a6,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x4465a6;rows.append(dict(inputBits=words,crossBits=cross,outputBits=list(struct.unpack('<3I',m.mem_read(camera+0x30,12)))))
 finally:backend=vectors.close()
 report=dict(originalExecutableSha256=sha(image.data),toolSha256=sha(Path(__file__).read_bytes()),targetInstructionBytesPatched=0,iatBinding='D3DXVec3Normalize slot4b12b8 bound to the explicit actual Windows x86 DLL service',backend=backend,rows=rows,scope='Original446539..44659d SSE inline cross product, followed by original call4465a0 to actual installed x86 D3DX9_43 normalization. Direction/up are declared six float32 inputs; matrices, device SetTransform, original caller and complete camera function are excluded. No original game process or audio starts.',completeGame=False,nativeEquivalent=False);(home/'native.json').write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps(dict(nativeCases=len(rows),actualWindowsX86D3dx=True,targetInstructionBytesPatched=0)))
if __name__=='__main__':main()
