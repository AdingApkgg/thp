"""Recover actual reset/copy/draw camera roles; no live game, GPU or input writes."""
from pathlib import Path
import ctypes as C,hashlib,importlib,json,struct,sys
from ctypes import wintypes as W
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_MXCSR
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-roles-nov12-v3';H.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(im.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,off,n in im.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,im.data[off:off+n])
B=0x78000000;STACK=B+0xf0000;STOP=B+0xe0000;m.mem_map(B,0x100000);get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];put=lambda p,v:m.mem_write(p,struct.pack('<I',v));rows=[]
def service(uc,pc,size,unused):
 sp=m.reg_read(UC_X86_REG_ESP)
 if pc==0x446250:
  at=get(sp+4);mode=get(at+248);rows.append(dict(address=hex(at),mode=mode,returnPc=hex(get(sp)),viewport=list(struct.unpack('<4I2f',m.mem_read(at+224,24))),renderSize=[get(at+88),get(at+92)]));cleanup=4
 else:assert pc==0x4854a0;cleanup=0
 m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4+cleanup)
for pc in [0x446250,0x4854a0]:m.hook_add(UC_HOOK_CODE,service,begin=pc,end=pc)
put(0x4f7a64,640);put(0x4f7a68,480);m.mem_write(0x4f7a6c,struct.pack('<f',1));put(STACK,STOP)
for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,0x4d8f60),(UC_X86_REG_MXCSR,0x1f80)]:m.reg_write(reg,value)
m.emu_start(0x4465e0,STOP,count=100000);assert m.reg_read(UC_X86_REG_EIP)==STOP
(H/'reset-arguments.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
assert len(rows)==4 and sorted(r['mode'] for r in rows)==[0,1,2,3]
names={0:'play_camera',1:'scaled_play_camera',2:'full_camera',3:'world_camera'};roles={names[r['mode']]:r for r in rows}
assert roles['world_camera']['address']=='0x4d9514' and roles['scaled_play_camera']['address']=='0x4d92bc'
assert roles['world_camera']['viewport'][:4]==[116,4,408,472] and roles['scaled_play_camera']['viewport'][:4]==[128,16,384,448]
decoder=Cs(CS_ARCH_X86,CS_MODE_32);instructions=[]
for pc,mnemonic,operand in [(0x40d43a,'mov','esi, 0x4d9514'),(0x40e35e,'mov','edi, 0x4d9514'),(0x40e365,'push','0x4d9514'),(0x47e132,'push','0x4d9514')]:
 ins=next(decoder.disasm(im.read(pc,15),pc));assert (ins.mnemonic,ins.op_str)==(mnemonic,operand);instructions.append(dict(pc=hex(pc),role='world_camera',instructionSha256=sha(bytes(ins.bytes))))
class Cache(C.Structure):_fields_=[('level',C.c_ubyte),('assoc',C.c_ubyte),('line',C.c_ushort),('size',W.DWORD),('kind',C.c_int)]
class Data(C.Union):_fields_=[('cache',Cache),('reserved',C.c_ulonglong*2)]
class Info(C.Structure):_fields_=[('mask',C.c_size_t),('relation',C.c_int),('data',Data)]
k=C.WinDLL('kernel32',use_last_error=True);f=k.GetLogicalProcessorInformation;f.argtypes=[C.POINTER(Info),C.POINTER(W.DWORD)];f.restype=W.BOOL;length=W.DWORD();assert not f(None,C.byref(length)) and C.get_last_error()==122
data=(Info*(length.value//C.sizeof(Info)))();assert f(data,C.byref(length));lines=sorted({r.data.cache.line for r in data if r.relation==2});assert lines==[64]
world=int(roles['world_camera']['address'],16);right=world+48;assert right%8==4 and right//64==(right+7)//64
pe=struct.unpack_from('<I',im.data,0x3c)[0];count=struct.unpack_from('<H',im.data,pe+6)[0];optional=struct.unpack_from('<H',im.data,pe+20)[0];section=None
for i in range(count):
 at=pe+24+optional+i*40;size,va=struct.unpack_from('<II',im.data,at+8);flags=struct.unpack_from('<I',im.data,at+36)[0]
 if im.image_base+va<=world<im.image_base+va+size:section=dict(name=im.data[at:at+8].split(b'\0')[0].decode(),flags=hex(flags),notCachedFlag=bool(flags&0x04000000))
assert section and not section['notCachedFlag']
report=dict(schema='thp/th14-native-camera-roles/1',roles=roles,worldProducerAndConsumerInstructionBindings=instructions,
 originalWorldRightAddress=hex(right),originalWorldRightQwordNaturallyAligned=False,originalWorldRightQwordWithinMeasuredCacheLine=True,measuredCacheLineBytes=lines,
 originalWorldImageSection=section,ordinaryCachedImageMappingAssumptionExplicit=True,liveHistoricalPageProtectionNotMeasured=True,
 correctAtomicityBasis='P6-or-newer unaligned cached 16/32/64-bit access contained within one cache line; not an aligned-qword claim about 0x4d9190',
 intelReference='https://www.intel.com/content/dam/support/us/en/documents/processors/pentium4/sb/25366821.pdf',intelSection='7.1.1, PDF page272 (zero-based)',
 resetScreenMathDeclaredService=True,resetInstructionStreamUnmodified=True,rawMathAndWholeThreadSchedulingAccepted=False,
 previousWrongRoleClaim='camera-right-pair-nov12 used 0x4d9190 as world and called its pair naturally aligned; this address is play_camera',
 runtimeBehaviorChanged=False,newGameRuns=0,newGpuRuns=0,audibleOutput=False,completeGame=False,executableSha256=sha(im.data),toolSha256=sha(Path(__file__).read_bytes()))
(H/'checked.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
