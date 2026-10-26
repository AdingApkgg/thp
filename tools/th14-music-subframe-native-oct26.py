"""Silent whole retail481ee0 with controlled COM and readonly file services."""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib,json,math,struct,sys
from ctypes import wintypes as W
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();O=args.output.resolve();assert O.is_relative_to(R/'artifacts/th14');O.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(R/'tools'));sha=lambda b:hashlib.sha256(b).hexdigest()
image=importlib.import_module('th-anm-handlers').handlers(14)[0];assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,b,size,offset,n in image.sections:
 start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,image.data[offset:offset+n])
base=0x70000000;heap_base=0x72000000;m.mem_map(base,0x200000);m.mem_map(heap_base,0x800000)
controller,reader,fmt,holder,old_buffer,device,device_holder,notify,stack=[base+x for x in [0x1000,0x2000,0x3000,0x4000,0x5000,0x6000,0x7000,0x8000,0x180000]]
vtable=base+0xa000;device_table=vtable+0x100;notify_table=vtable+0x200;get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
def ret(value=0,argc=0):
 sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,value&0xffffffff);m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4+argc*4)
heap=heap_base;buffers={};file_cursor=0;events=[];reads=[];created=[];unlocked=[];play_cursor=0
def allocate(n):
 global heap
 assert 0<n<0x200000;p=heap;heap=(heap+n+15)&~15;assert heap<heap_base+0x800000;m.mem_write(p,b'\xcd'*n);return p
archive=json.loads((R/'artifacts/archive-differential/th14.json').read_bytes());format_bytes=(Path(archive['extraction'])/'thbgm.fmt').read_bytes();target=json.loads((R/'runtimes/th14/target.json').read_bytes());k=C.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE
k.SetFilePointer.argtypes=[W.HANDLE,W.LONG,C.c_void_p,W.DWORD];k.SetFilePointer.restype=W.DWORD
k.ReadFile.argtypes=[W.HANDLE,C.c_void_p,W.DWORD,C.POINTER(W.DWORD),C.c_void_p];k.ReadFile.restype=W.BOOL
k.CloseHandle.argtypes=[W.HANDLE]
file_handle=k.CreateFileW(target['dataArchives']['thbgm.dat']['path'],0x80000000,3,None,3,0x80,None);assert file_handle not in [None,C.c_void_p(-1).value]
read_buffer=C.create_string_buffer(705600)
def service(machine,pc,size,user):
 global file_cursor
 sp=m.reg_read(UC_X86_REG_ESP);a=lambda i:get(sp+i*4)
 if pc==base+0x100:
  put(a(1),10000000);put(a(1)+4,0);ret(1,1)
 elif pc==base+0x110:
  assert a(1)==7 and a(3)==a(4)==0;before=file_cursor;C.set_last_error(0);result=k.SetFilePointer(file_handle,W.LONG(a(2)),None,0);error=C.get_last_error();file_cursor=k.SetFilePointer(file_handle,0,None,1);events.append(dict(kind='seek',offset=a(2),signedDistance=W.LONG(a(2)).value,result=result,lastError=error,before=before,after=file_cursor));ret(result,4)
 elif pc==base+0x120:
  assert a(1)==7 and a(5)==0 and a(3)<=705600;got=W.DWORD();assert k.ReadFile(file_handle,read_buffer,a(3),C.byref(got),None);raw=read_buffer.raw[:got.value];m.mem_write(a(2),raw);put(a(4),len(raw));reads.append(dict(offset=file_cursor,requested=a(3),bytes=len(raw),sha256=sha(raw)));file_cursor+=len(raw);ret(1,5)
 elif pc in [0x484e50,0x4854af,0x485540]:ret(allocate(a(1)))
 elif pc in [0x486b83,0x4854fe]:ret()
 elif pc==0x4854a0:ret(m.reg_read(UC_X86_REG_EAX))
 elif pc==base+0x200:
  desc=a(2);n=get(desc+8);assert n==705600;obj=allocate(0x100);put(obj,vtable);pcm=allocate(n);buffers[obj]=(pcm,n);put(a(3),obj);created.append(dict(bytes=n,flags=get(desc+4),formatHex=bytes(m.mem_read(get(desc+16),16)).hex()));ret(0,4)
 elif pc==base+0x210:put(a(3),notify);ret(0,3)
 elif pc==base+0x220:ret(0,1)
 elif pc==base+0x230:events.append(dict(kind='notify',count=a(2)));assert a(2)==8;ret(0,3)
 elif pc==base+0x240:put(a(2),0);ret(0,2)
 elif pc==base+0x250:
  obj=a(1);pcm,n=buffers[obj];offset=a(2);size=a(3);assert offset+size<=n;put(a(4),pcm+offset);put(a(5),size);assert a(8)==0
  if a(6):put(a(6),0)
  if a(7):put(a(7),0)
  events.append(dict(kind='lock',offset=offset,bytes=size));ret(0,8)
 elif pc==base+0x260:
  obj=a(1);pcm,n=buffers[obj];size=a(3);assert pcm<=a(2)<pcm+n and a(4)==a(5)==0;raw=bytes(m.mem_read(a(2),size));unlocked.append(dict(bytes=size,sha256=sha(raw),allZero=not any(raw)));events.append(dict(kind='unlock',bytes=size));ret(0,5)
 elif pc==base+0x270:events.append(dict(kind='stop'));ret(0,1)
 elif pc==base+0x280:events.append(dict(kind='position',bytes=a(2)));ret(0,2)
 elif pc==base+0x290:events.append(dict(kind='volume',value=a(2)));ret(0,2)
 elif pc==base+0x2a0:events.append(dict(kind='play',reserved=a(2),priority=a(3),flags=a(4)));ret(0,4)
 elif pc==base+0x2b0:
  if a(2):put(a(2),play_cursor)
  if a(3):put(a(3),(play_cursor+88200)%705600)
  ret(0,3)
 else:raise AssertionError(hex(pc))
addresses=[base+x for x in [0x100,0x110,0x120,0x200,0x210,0x220,0x230,0x240,0x250,0x260,0x270,0x280,0x290,0x2a0,0x2b0]]+[0x484e50,0x4854af,0x485540,0x486b83,0x4854fe,0x4854a0]
for pc in addresses:m.hook_add(UC_HOOK_CODE,service,begin=pc,end=pc)
put(0x4b10e0,base+0x100);put(0x4b10bc,base+0x110);put(0x4b108c,base+0x120)
for offset,pc in [(0,0x210),(8,0x220),(0x24,0x240),(0x2c,0x250),(0x4c,0x260),(0x48,0x270),(0x34,0x280),(0x3c,0x290),(0x30,0x2a0),(0x10,0x2b0)]:put(vtable+offset,base+pc)
put(device_table+0xc,base+0x200);put(notify_table+0xc,base+0x230);put(notify_table+8,base+0x220);put(device,device_table);put(device_holder,device);put(notify,notify_table)
put(0x4fd1ac,100);put(0x4fd190,0);m.mem_write(0x4f5815,b'\0');m.mem_write(0x4f5a34,struct.pack('<Q',10000000));m.mem_write(0x4f5a3c,bytes(8));descriptor=struct.pack('<IIIIIIIII',36,0x18188,705600,0,0,0,0,0,0)
rows=[]
for index in range(18):
 entry=format_bytes[index*52:(index+1)*52];rate=struct.unpack_from('<I',entry,36)[0]
 for clock_ns in [0,1,11000,22675,22676,1250000000]:
  seconds=clock_ns/1e9
  heap=heap_base;buffers.clear();events.clear();reads.clear();created.clear();unlocked.clear();file_cursor=0
  m.mem_write(controller,bytes(0xb0));m.mem_write(reader,bytes(0xa0));m.mem_write(fmt,entry);put(controller+4,holder);put(holder,old_buffer);put(old_buffer,vtable);buffers[old_buffer]=(allocate(705600),705600);put(controller+8,705600);put(controller+0xc,reader);put(controller+0x10,1);put(controller+0x24,1);m.mem_write(controller+0x58,descriptor);put(controller+0x7c,device_holder);put(controller+0x94,88200);put(controller+0x98,0x1234);put(reader+0x90,fmt);put(reader+0x8c,7);put(0x4fd180,controller)
  # Execute the original initial fill, so failed restoration seeks preserve
  # a real, declared prior reader position rather than inventing EOF behavior.
  put(stack,base);put(stack+4,old_buffer);put(stack+8,0);put(stack+12,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,controller);m.emu_start(0x480cf0,base,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==base and len(unlocked)==1
  preroll=dict(fileCursor=file_cursor,fill=unlocked[0],reads=reads[:],events=events[:]);unlocked.clear();reads.clear();events.clear()
  put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,controller);m.reg_write(UC_X86_REG_XMM1,struct.unpack('<Q',struct.pack('<d',seconds))[0]);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
  try:m.emu_start(0x481ee0,base,count=5000000)
  except Exception as e:raise RuntimeError('originalpc '+hex(m.reg_read(UC_X86_REG_EIP)))from e
  assert m.reg_read(UC_X86_REG_EIP)==base;assert len(unlocked)==1
  chunks=[dict(fill=unlocked[0],reads=reads[:])]
  if seconds==0:
   remaining=get(reader+8);count=12 if reads[0]['bytes']==0 else max(12,math.ceil(remaining/88200)+2)
   for step in range(count):
    before=len(reads);play_cursor=((step+1)*88200)%705600;put(stack,base);put(stack+4,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,controller);m.emu_start(0x481620,base,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==base and m.reg_read(UC_X86_REG_EAX)==0
    assert len(unlocked)==step+2;chunks.append(dict(fill=unlocked[-1],reads=reads[before:]))
  rows.append(dict(track=index,name=entry[:16].split(b'\0')[0].decode(),seconds=seconds,clockNs=clock_ns,formatHex=entry.hex(),initialFill=preroll,restoreSeeks=[e for e in events if e['kind']=='seek'][:1],created=created[:],chunks=chunks,controllerPlaying=get(controller+0x50),loopReached=bool(get(reader+0x9c))))
k.CloseHandle(file_handle);report=dict(fileServices='Actual Windows readonly CreateFileW/SetFilePointer/ReadFile; signed LONG and real failure-preserved cursor',initialReaderState='Actual whole480cf0 initial4sec fill; no prior notification refills',cases=len(rows),streamingCases=sum(r['seconds']==0 for r in rows),descriptorInputs=dict(bufferBytes=705600,chunkBytes=88200,segments=8,flags=0x18188,rate=44100,channels=2,bits=16,derivation='Retail46e0a5..46e0b8 derives aligned half-second chunk;48055f multiplies by8 for4sec. Raw-reader7c=0 observed read-only separately; descriptor flags constructed from48057a.'),rows=rows,executableSha256=sha(image.data),toolSha256=sha(Path(__file__).read_bytes()),audioDevicesOpened=0,audioPlayed=False,productionChanged=False,completeGame=False,nativeEquivalent=False);(O/'full-restore-native.json').write_text(json.dumps(report,indent=2)+'\n');print('cases',len(rows),'zero filled',sum(r['chunks'][0]['fill']['allZero']for r in rows))
