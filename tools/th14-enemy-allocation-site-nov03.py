"""Execute the original enemy factory to its allocation/constructor boundary."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EBP,UC_X86_REG_EDI,UC_X86_REG_ESI,UC_X86_REG_ESP,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));Image=importlib.import_module('th12-pe').Image;exe=Image('H:/Games/th/14/th14.exe');sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(exe.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert exe.read(0x421ef0,3).hex()=='558bec' and exe.read(0x421efe,5).hex()=='680c530000' and exe.read(0x421f03,5).hex()=='e8a7350600' and exe.read(0x421f14,5).hex()=='e8970b0000'
assert exe.read(0x485583,6).hex()=='ff15e4114b00' and exe.read(0x488e04,6).hex()=='ff1574114b00';pe=struct.unpack_from('<I',exe.data,0x3c)[0];directory=exe.image_base+struct.unpack_from('<I',exe.data,pe+0x18+0x68)[0];resolved={}
for j in range(200):
 oft,_,_,name_rva,first=struct.unpack('<5I',exe.read(directory+j*20,20))
 if not any([oft,name_rva,first]):break
 dll=exe.cstring(exe.image_base+name_rva);thunk=exe.image_base+(oft or first)
 for k in range(1000):
  value=exe.u32(thunk+k*4)
  if not value:break
  address=exe.image_base+first+k*4
  if address in (0x4b11e4,0x4b1174):
   assert not value&0x80000000 and address not in resolved;resolved[address]=(dll,exe.cstring(exe.image_base+value+2))
assert resolved=={0x4b11e4:('KERNEL32.dll','HeapAlloc'),0x4b1174:('KERNEL32.dll','GetProcessHeap')}
cases=[]
for address in [0x11001000,0x22002000,0x33003000,0x44004000]:
 m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,va,size,offset,count in exe.sections:
  page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,exe.data[offset:offset+count])
 m.mem_map(0x70000000,0x100000);stack=0x700ff000;manager=0x70002000;script=0x70003000;position=0x70004000;sentinel=0x70001000
 heap=0x70006000;heap_entry=0x70007000;get_heap_entry=0x70008000;m.mem_write(0x4db544,struct.pack('<I',manager));m.mem_write(0x4b11e4,struct.pack('<I',heap_entry));m.mem_write(0x4b1174,struct.pack('<I',get_heap_entry));m.mem_write(stack,struct.pack('<I',sentinel));m.reg_write(UC_X86_REG_ESP,stack)
 for reg in [UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EBP,UC_X86_REG_EDI,UC_X86_REG_ESI]:m.reg_write(reg,0)
 m.emu_start(0x488e04,get_heap_entry,count=1000);assert m.reg_read(UC_X86_REG_EIP)==get_heap_entry;init_sp=m.reg_read(UC_X86_REG_ESP);assert struct.unpack('<I',m.mem_read(init_sp,4))[0]==0x488e0a;m.reg_write(UC_X86_REG_EAX,heap);m.reg_write(UC_X86_REG_ESP,init_sp+4);m.emu_start(0x488e0a,sentinel,count=1000);assert m.reg_read(UC_X86_REG_EIP)==sentinel and m.reg_read(UC_X86_REG_EAX)==1 and struct.unpack('<I',m.mem_read(0x4dafec,4))[0]==heap
 m.mem_write(stack,struct.pack('<4I',sentinel,script,position,0));m.reg_write(UC_X86_REG_ESP,stack)
 m.emu_start(0x421ef0,0x4854af,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x4854af;sp=m.reg_read(UC_X86_REG_ESP);return_pc,size=struct.unpack('<2I',m.mem_read(sp,8));assert return_pc==0x421f08 and size==0x530c
 # Execute the original CRT wrapper with a declared initialized heap; stop at
 # the imported OS call and return a synthetic pointer with stdcall cleanup.
 m.emu_start(0x4854af,heap_entry,count=1000);assert m.reg_read(UC_X86_REG_EIP)==heap_entry;heap_sp=m.reg_read(UC_X86_REG_ESP);heap_return,actual_heap,flags,heap_bytes=struct.unpack('<4I',m.mem_read(heap_sp,16));assert (heap_return,actual_heap,flags,heap_bytes)==(0x485589,heap,0,0x530c)
 m.reg_write(UC_X86_REG_EAX,address);m.reg_write(UC_X86_REG_ESP,heap_sp+16);m.emu_start(heap_return,0x422ab0,count=1000);assert m.reg_read(UC_X86_REG_EIP)==0x422ab0 and m.reg_read(UC_X86_REG_ECX)==address
 sp=m.reg_read(UC_X86_REG_ESP);constructor_return,constructor_arg=struct.unpack('<2I',m.mem_read(sp,8));assert constructor_return==0x421f19 and constructor_arg==script
 cases.append(dict(syntheticAllocatorPointer=hex(address),requestedBytes=size,heapAllocBytes=heap_bytes,heapAllocFlags=flags,actualAllocationCall='0x421f03',actualConstructorCall='0x421f14',allocatorReturnReachedConstructorUnchanged=True,constructorArgumentPreserved=True))
# Independent null-handle control must report CRT setup failure and retain a
# zero heap, rather than treating the declared OS boundary as always successful.
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,offset,count in exe.sections:
 page=va&~4095;m.mem_map(page,((va+size+4095)&~4095)-page);m.mem_write(va,exe.data[offset:offset+count])
m.mem_map(0x70000000,0x100000);stack=0x700ff000;sentinel=0x70001000;get_heap_entry=0x70008000;m.mem_write(0x4b1174,struct.pack('<I',get_heap_entry));m.mem_write(stack,struct.pack('<I',sentinel));m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x488e04,get_heap_entry,count=1000);sp=m.reg_read(UC_X86_REG_ESP);assert struct.unpack('<I',m.mem_read(sp,4))[0]==0x488e0a;m.reg_write(UC_X86_REG_EAX,0);m.reg_write(UC_X86_REG_ESP,sp+4);m.emu_start(0x488e0a,sentinel,count=1000);assert m.reg_read(UC_X86_REG_EIP)==sentinel and m.reg_read(UC_X86_REG_EAX)==0 and struct.unpack('<I',m.mem_read(0x4dafec,4))[0]==0
result=dict(verifiedFiniteOriginalEnemyFactoryBoundary=True,cases=cases,originalExecutableSha256=sha(exe.data),actualOriginalInstructionSequencesExecuted=True,enemyObjectRequestedBytes=0x530c,originalCrtProcessHeapSetupExecuted=True,heapSetupImport='KERNEL32.dll!GetProcessHeap',nullProcessHeapControlRejected=True,originalCrtWrapperExecuted=True,heapImport='KERNEL32.dll!HeapAlloc',allocatorImplementationExecuted=False,originalWindowsHeapLayoutProved=False,crossProcessObjectLifetimeProved=False,nativeValuesProvidedToEngine=False,productionCodeChanged=False,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()),scope='Actual original CRT process-heap setup, factory and allocation wrapper instructions execute through imported GetProcessHeap and HeapAlloc boundaries. Those OS calls return declared synthetic handles and pointers; original instructions then reach the constructor. The Windows allocator and constructor body are not executed; this does not determine actual addresses or heap layout.')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'docs/porting/th14-enemy-allocation-site-nov03.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'docs/porting') or out.is_relative_to(R/'artifacts/th14');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:assert not out.exists();out.write_bytes(data)
print(json.dumps(result))
