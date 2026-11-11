"""Compare actual retained transition quad caches to original/C++ geometry."""
from pathlib import Path
import hashlib,importlib,json,os,struct,subprocess,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/first-present-alpha-localization-nov12/embedded-quads';assert not H.exists();H.mkdir();load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R/'artifacts/th14/current-first-present-vm303-nov12';parent=load(P/'private-vms-qualified.json');assert all(x['wordsCompared']==303 and not x['differences']for x in parent['embedded'][:4]);N=R/'artifacts/th14/current-startup-prefix-nov10/native';raw=bytes.fromhex(load(N/'transition-before-readback.json')['geometryHex']);assert len(raw)==5*1484+8
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert hashlib.sha256(im.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 first=va&~4095;m.mem_map(first,((va+size+4095)&~4095)-first);m.mem_write(va,im.data[off:off+n])
B=0x70000000;VM=B+0x1000;OUTPUT=B+0x4000;STACK=B+0xff000;STOP=B+0xfe000;m.mem_map(B,0x100000);m.mem_write(0x4854a0,b'\xc3');put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
for p,v in [(0x4f7a64,640),(0x4f7a68,480),(0x4f7a6c,0x3f800000),(0x4f7a80,320),(0x4f7a84,16),(0x4f7a88,320),(0x4f7a8c,16)]:put(p,v)
inputs=bytearray();geometry=bytearray();captured=bytearray()
for i in range(4):
 vm=raw[i*1484:(i+1)*1484];assert struct.unpack_from('<I',vm,0x594)[0]==0 and(struct.unpack_from('<I',vm,0x18)[0]>>25)&31==1
 inputs.extend(struct.pack('<8I',640,480,0x3f800000,320,16,320,16,0)+vm+bytes(1484));captured.extend(vm[0x4f8:0x528]);m.mem_write(VM,vm);m.mem_write(STACK,struct.pack('<6I',STOP,VM,OUTPUT,OUTPUT+12,OUTPUT+24,OUTPUT+36))
 for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
 m.emu_start(0x4766e0,STOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==STOP and bytes(m.mem_read(VM,1484))==vm;geometry.extend(m.mem_read(OUTPUT,48))
for name,data in [('inputs.bin',inputs),('native-geometry.u32',geometry),('native-captured.u32',captured)]:(H/name).write_bytes(data)
core=load(R/'artifacts/th14/mode8-display-space-nov12/current-core/build.json');providers=load(R/'artifacts/th14/quad-display-space-nov12/candidate-v3/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==core['compilerSha256'];objects=[]
for p,d in providers['objects'].items():assert sha(R/p)==d,p;objects.append(str(R/p))
fixture=R/'tools/th14-embedded-transition-quads-nov12.cpp';cmd=[str(cc),*core['flags'],'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*objects,'-o',str(H/'probe.wasm')]
with(H/'build.log').open('wb')as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(H),'TMP':str(H),'TMPDIR':str(H)})
j=dict(cases=4,wasmSha256=sha(H/'probe.wasm'),inputSha256=sha(H/'inputs.bin'),nativeGeometrySha256=sha(H/'native-geometry.u32'),nativeCapturedCacheSha256=sha(H/'native-captured.u32'),fixtureSha256=sha(fixture),includedFixtureSha256=sha(R/'tools/th14-mode8-display-component-nov12.cpp'),objects=providers['objects'],originalEntry='4766e0',measuredFirstFourCanonical303Match=True,cppUsesEquivalentMeasuredGeometryInputs=True,cppDeclaredRendererOffsetZero=True,actualApplicationNotRerun=True,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False)
(H/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({k:v for k,v in j.items()if k!='objects'}))
