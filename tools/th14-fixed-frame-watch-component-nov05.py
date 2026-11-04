"""Validate four stable hardware watches, including passes with no Player.

The owned fixture has two threads. Every eighth pass omits its Player step;
entry and pump observations must still arrive. No original process or assets.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib.util,json,struct,time,traceback
from ctypes import wintypes as W
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
SOURCE=r'''typedef unsigned long U32;typedef void* Handle;
__declspec(dllimport) Handle __stdcall CreateThread(void*,U32,U32(__stdcall*)(void*),void*,U32,U32*);
__declspec(dllimport) U32 __stdcall WaitForSingleObject(Handle,U32);
__declspec(dllimport) int __stdcall CloseHandle(Handle);
__declspec(dllimport) void __stdcall Sleep(U32);
__declspec(dllimport) __declspec(noreturn) void __stdcall ExitProcess(U32);
__declspec(dllexport) volatile U32 serial;
volatile U32 announced[2];
__declspec(dllexport) __declspec(naked) void __cdecl entry_point(void){__asm {nop} __asm {ret}}
__declspec(dllexport) __declspec(naked) void __cdecl pump(void){__asm {nop} __asm {nop} __asm {ret}}
__declspec(dllexport) __declspec(naked) void __cdecl player(void){__asm {lock inc dword ptr [serial]} __asm {ret}}
__declspec(dllexport) U32 __stdcall worker(void* argument){U32 index=(U32)argument;
for(U32 i=0;i<128;++i){announced[index]=i+1;while(announced[0]<i+1||announced[1]<i+1)Sleep(0);
entry_point();pump();if((i&7)!=7)player();}return 0;}
void entry(void){Handle a=CreateThread(0,0,worker,(void*)0,0,0),b=CreateThread(0,0,worker,(void*)1,0,0);
if(!a||!b)ExitProcess(11);WaitForSingleObject(a,0xffffffffu);WaitForSingleObject(b,0xffffffffu);CloseHandle(a);CloseHandle(b);ExitProcess(serial==224?0:12);}
'''
def run(home,out):
    out.mkdir(exist_ok=False);helper=module(R/'tools/th14-pending-debug-status-component-nov05.py','owned_build')
    info=json.loads((home/'build.json').read_bytes());raw=(home/'fixture.exe').read_bytes();assert SHA(raw)==info['executableSha256']
    exports,offset=helper.symbols(raw);image_base=0x400000
    def address(name):return image_base+next(v for k,v in exports.items()if k.lstrip('_').split('@')[0]==name)
    names=['entry_point','pump','player','serial','worker'];entry,pump,player,serial,worker=map(address,names)
    assert len({entry,pump,player,serial,worker})==5
    at=offset(player-0x400000);assert raw[at:at+7]==b'\xf0\xff\x05'+struct.pack('<I',serial)
    labels={entry:'entry',pump:'pump',player:'player',player+7:'store'}
    types=module(R/'tools/th14-native-session-capture.py','owned_types');k=C.WinDLL('kernel32',use_last_error=True)
    signatures={
        'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
        'WaitForDebugEvent':([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),'ContinueDebugEvent':([W.DWORD,W.DWORD,W.DWORD],W.BOOL),
        'Wow64GetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),'Wow64SetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
        'GetExitCodeThread':([W.HANDLE,C.POINTER(W.DWORD)],W.BOOL),'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),
        'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),'CloseHandle':([W.HANDLE],W.BOOL)}
    for name,(args,result)in signatures.items():getattr(k,name).argtypes=args;getattr(k,name).restype=result
    def checked(value):
        if not value:raise C.WinError(C.get_last_error())
        return value
    def context(handle):
        b=C.create_string_buffer(716);struct.pack_into('<I',b,0,0x10017);checked(k.Wow64GetThreadContext(handle,b));return b
    u32=lambda b,at:struct.unpack_from('<I',b,at)[0]
    threads={};events=[];deferrals=0
    def arm(tid,current=False):
        nonlocal deferrals
        handle=threads[tid];alive=W.DWORD();checked(k.GetExitCodeThread(handle,C.byref(alive)))
        if alive.value!=259:return
        b=context(handle)
        if not current and u32(b,20)&15:deferrals+=1;return
        struct.pack_into('<I',b,0,0x10011 if current else 0x10010)
        for i,value in enumerate([player,entry,pump,serial]):struct.pack_into('<I',b,4+4*i,value)
        struct.pack_into('<I',b,20,0);struct.pack_into('<I',b,24,0xd0000055)
        if current:struct.pack_into('<I',b,192,u32(b,192)|0x10000)
        checked(k.Wow64SetThreadContext(handle,b))
    si=types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0;pi=types.ProcessInfo();exe=str(home/'fixture.exe')
    checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x08000000,None,str(home),C.byref(si),C.byref(pi)))
    handles={pi.process,pi.thread};exit_code=None;exited=False;pending=False;event=None;error='';start=time.monotonic()
    try:
        while not exited:
            assert time.monotonic()-start<45,'Owned fixture timeout';event=types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(event),100):assert C.get_last_error()==121;continue
            pending=True;assert event.pid==pi.pid;status=0x10002
            if event.kind==3:
                image_base=int(event.data.create_process.base);entry,pump,player,serial,worker=map(address,names)
                labels={entry:'entry',pump:'pump',player:'player',player+7:'store'};handles.update([event.data.create_process.thread,event.data.create_process.process])
                if event.data.create_process.file:k.CloseHandle(event.data.create_process.file)
            elif event.kind==2:
                handle=event.data.create_thread.thread;handles.add(handle)
                if int(event.data.create_thread.start)==worker:threads[event.tid]=handle;arm(event.tid)
            elif event.kind==4:threads.pop(event.tid,None)
            elif event.kind==6:
                if event.data.dll.file:k.CloseHandle(event.data.dll.file)
            elif event.kind==5:exited=True;exit_code=int(event.data.exit_code)
            elif event.kind==1:
                code=int(event.data.exception.record.code)
                if code in (0x80000004,0x4000001e)and event.tid in threads:
                    b=context(threads[event.tid]);pc=u32(b,184);dr6=u32(b,20);kind=labels.get(pc);slots=struct.unpack_from('<4I',b,4)
                    matching=8 if kind=='store'else sum(1<<i for i,a in enumerate(slots)if a==pc)
                    known=kind is not None and bool(dr6&matching)
                    events.append(dict(threadId=event.tid,kind=kind,pc=pc,debugStatus=dr6,matchingSlotBits=matching,known=known))
                    if not known:status=0x80010001
                    else:
                        for tid in list(threads):arm(tid,tid==event.tid)
                elif code not in (0x80000003,0x4000001f):events.append(dict(exceptionCode=code,known=False));status=0x80010001
            checked(k.ContinueDebugEvent(event.pid,event.tid,status));pending=False
    except BaseException:error=traceback.format_exc()
    finally:
        if not exited:
            k.TerminateProcess(pi.process,99)
            if pending:k.ContinueDebugEvent(event.pid,event.tid,0x10002)
            k.WaitForSingleObject(pi.process,5000)
        for handle in handles:
            if handle:k.CloseHandle(handle)
    expected=[]
    for n in range(128):expected+=['entry','pump']+(['player','store']if n&7!=7 else[])
    tids={x['threadId']for x in events if 'threadId'in x};counts={name:sum(x.get('kind')==name for x in events)for name in ['entry','pump','player','store']}
    equal=len(tids)==2 and all([x['kind']for x in events if x.get('threadId')==tid]==expected for tid in tids)
    report=dict(passed=not error and exit_code==0 and equal and all(x['known']for x in events),exitCode=exit_code,error=error,counts=counts,
        events=events,perThreadOrderEqual=equal,omittedPlayerPasses=32,entryAndPumpStillObservedOnOmittedPlayerPasses=equal,
        unknownExceptions=sum(not x['known']for x in events),deferredPendingUpdates=deferrals,
        sourceSha256=info['sourceSha256'],executableSha256=info['executableSha256'],toolSha256=SHA(Path(__file__).read_bytes()),
        hardwareAddressesNeverMultiplexed=True,originalProcessAccessed=False,instructionOrDataMemoryWrittenByDebugger=False,
        windowsCreated=False,physicalAudioDevicesOpened=0,elapsedSeconds=time.monotonic()-start,completeGame=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']and counts==dict(entry=256,pump=256,player=224,store=224)
    return {k:report[k]for k in ['passed','counts','omittedPlayerPasses','unknownExceptions','deferredPendingUpdates']}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True);(out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    helper=module(R/'tools/th14-pending-debug-status-component-nov05.py','owned_builder');helper.SOURCE=SOURCE;helper.build(out/'build')
    print(json.dumps(run(out/'build',out/'stable')),flush=True)
