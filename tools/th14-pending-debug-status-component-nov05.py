"""Exercise pending debug-status erasure on an owned concurrent x86 fixture.

No game process, game assets, GPU, window, input or audio. The negative policy
deliberately clears another stopped fixture thread's DR6; the positive policy
defers that update when a hardware trap is already pending. Raw exceptions are
retained, never waived as original-game acceptance.
"""
from pathlib import Path
import argparse, ctypes as C, hashlib, importlib.util, json, os, struct, subprocess, time
from ctypes import wintypes as W

R=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
SOURCE=r'''typedef unsigned long U32;typedef void* Handle;
__declspec(dllimport) Handle __stdcall CreateThread(void*,U32,U32(__stdcall*)(void*),void*,U32,U32*);
__declspec(dllimport) U32 __stdcall WaitForSingleObject(Handle,U32);
__declspec(dllimport) int __stdcall CloseHandle(Handle);
__declspec(dllimport) void __stdcall Sleep(U32);
__declspec(dllimport) __declspec(noreturn) void __stdcall ExitProcess(U32);
__declspec(dllexport) volatile U32 serial;
volatile U32 announced[2];
__declspec(dllexport) __declspec(naked) void __cdecl marker(void){
__asm { lock inc dword ptr [serial] }
__asm { ret }
}
__declspec(dllexport) U32 __stdcall worker(void* argument){U32 index=(U32)argument;
for(U32 i=0;i<128;++i){announced[index]=i+1;while(announced[0]<i+1||announced[1]<i+1)Sleep(0);marker();}return 0;}
void entry(void){Handle a=CreateThread(0,0,worker,(void*)0,0,0),b=CreateThread(0,0,worker,(void*)1,0,0);
if(!a||!b)ExitProcess(11);WaitForSingleObject(a,0xffffffffu);WaitForSingleObject(b,0xffffffffu);CloseHandle(a);CloseHandle(b);ExitProcess(serial==256?0:12);}
'''

def build(out):
    assert not out.exists();out.mkdir(parents=True)
    vswhere=Path('C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe')
    compiler=Path(subprocess.check_output([str(vswhere),'-latest','-products','*','-find','VC/Tools/MSVC/*/bin/Hostx64/x86/cl.exe'],text=True).strip())
    linker=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/lld-link.exe'
    library=Path('C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0/um/x86/kernel32.lib')
    (out/'fixture.c').write_text(SOURCE,encoding='utf8',newline='\n')
    argv=[[str(compiler),'/nologo','/O2','/GS-','/Zl','/c',str(out/'fixture.c'),'/Fo'+str(out/'fixture.obj')],
        [str(linker),'/machine:x86','/entry:entry','/subsystem:console','/nodefaultlib','/dynamicbase:no','/base:0x400000','/out:'+str(out/'fixture.exe'),str(out/'fixture.obj'),str(library)]]
    for i,command in enumerate(argv):
        p=subprocess.run(command,cwd=R,capture_output=True,timeout=60,env={**os.environ,'TMP':str(out),'TEMP':str(out)})
        (out/(str(i)+'.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
    value=dict(compiled=True,sourceSha256=SHA((out/'fixture.c').read_bytes()),executableSha256=SHA((out/'fixture.exe').read_bytes()),
        compilerSha256=SHA(compiler.read_bytes()),linkerSha256=SHA(linker.read_bytes()),argv=argv,gameFilesAccessed=False)
    (out/'build.json').write_text(json.dumps(value,indent=2)+'\n');return value

def symbols(raw):
    pe=struct.unpack_from('<I',raw,0x3c)[0];optional=pe+24;size=struct.unpack_from('<H',raw,pe+20)[0]
    assert raw[pe:pe+4]==b'PE\0\0'and struct.unpack_from('<H',raw,optional)[0]==0x10b
    sections=[struct.unpack_from('<IIII',raw,optional+size+i*40+8)for i in range(struct.unpack_from('<H',raw,pe+6)[0])]
    def offset(rva):
        for virtual_size,address,length,start in sections:
            if address<=rva<address+max(virtual_size,length):return start+rva-address
        raise ValueError(rva)
    e=offset(struct.unpack_from('<I',raw,optional+96)[0]);_,_,count,addresses,names,ordinals=struct.unpack_from('<6I',raw,e+16);result={}
    for i in range(count):
        at=offset(struct.unpack_from('<I',raw,offset(names)+i*4)[0]);name=raw[at:raw.index(0,at)].decode()
        ordinal=struct.unpack_from('<H',raw,offset(ordinals)+i*2)[0];result[name]=struct.unpack_from('<I',raw,offset(addresses)+ordinal*4)[0]
    return result,offset

def run(home,out,policy):
    assert not out.exists();out.mkdir(parents=True)
    info=json.loads((home/'build.json').read_bytes());raw=(home/'fixture.exe').read_bytes();assert SHA(raw)==info['executableSha256']
    names,offset=symbols(raw);marker=next(v for k,v in names.items()if'marker'in k);worker=next(v for k,v in names.items()if'worker'in k);serial=next(v for k,v in names.items()if'serial'in k)
    assert raw[offset(marker):offset(marker)+7]==b'\xf0\xff\x05'+struct.pack('<I',0x400000+serial)
    spec=importlib.util.spec_from_file_location('own_debug_types',R/'tools/th14-native-session-capture.py');types=importlib.util.module_from_spec(spec);spec.loader.exec_module(types)
    k=C.WinDLL('kernel32',use_last_error=True)
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
    def arm(handle):
        b=context(handle);struct.pack_into('<I',b,0,0x10010)
        for i,value in enumerate([0x400000+serial,0,0,0]):struct.pack_into('<I',b,4+4*i,value)
        struct.pack_into('<I',b,20,0);struct.pack_into('<I',b,24,0xd0001);checked(k.Wow64SetThreadContext(handle,b))
    si=types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0;pi=types.ProcessInfo();exe=str(home/'fixture.exe')
    checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x08000000,None,str(home),C.byref(si),C.byref(pi)))
    threads={};handles={pi.process,pi.thread};events=[];cross=[];exit_code=None;exited=False;pending=False;event=None;error='';start=time.monotonic()
    try:
        while not exited:
            assert time.monotonic()-start<45,'Owned fixture timeout'
            event=types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(event),100):assert C.get_last_error()==121;continue
            pending=True;assert event.pid==pi.pid;status=0x10002
            if event.kind==3:
                assert int(event.data.create_process.base)==0x400000;handles.update([event.data.create_process.thread,event.data.create_process.process])
                if event.data.create_process.file:k.CloseHandle(event.data.create_process.file)
            elif event.kind==2:
                handle=event.data.create_thread.thread;handles.add(handle)
                if int(event.data.create_thread.start)==0x400000+worker:threads[event.tid]=handle;arm(handle)
            elif event.kind==4:threads.pop(event.tid,None)
            elif event.kind==6:
                if event.data.dll.file:k.CloseHandle(event.data.dll.file)
            elif event.kind==5:exited=True;exit_code=int(event.data.exit_code)
            elif event.kind==1:
                code=int(event.data.exception.record.code)
                if code in (0x80000004,0x4000001e)and event.tid in threads:
                    b=context(threads[event.tid]);pc=u32(b,184);dr6=u32(b,20)
                    row=dict(threadId=event.tid,pc=pc,debugStatus=dr6,knownMarkerAfterStore=pc==0x400000+marker+7,
                        ownWatchBitSet=bool(dr6&1),exceptionCode=code,firstChance=int(event.data.exception.first_chance))
                    events.append(row)
                    if not row['knownMarkerAfterStore']or not row['ownWatchBitSet']:
                        status=0x80010001 # retain and deliver the fixture's unknown exception
                    else:
                        for tid,handle in list(threads.items()):
                            if tid==event.tid:continue
                            alive=W.DWORD();checked(k.GetExitCodeThread(handle,C.byref(alive)))
                            if alive.value!=259:continue
                            other=context(handle);old=u32(other,20);defer=policy=='defer-pending'and bool(old&15)
                            cross.append(dict(eventThread=event.tid,targetThread=tid,pc=u32(other,184),beforeDebugStatus=old,pendingHardwareBits=old&15,updateDeferred=defer))
                            if not defer:
                                struct.pack_into('<I',other,0,0x10010);struct.pack_into('<I',other,20,0);checked(k.Wow64SetThreadContext(handle,other))
                        resume=context(threads[event.tid]);struct.pack_into('<I',resume,0,0x10011);struct.pack_into('<I',resume,20,0);struct.pack_into('<I',resume,192,u32(resume,192)|0x10000);checked(k.Wow64SetThreadContext(threads[event.tid],resume))
                elif code not in (0x80000003,0x4000001f):
                    events.append(dict(exceptionCode=code,firstChance=int(event.data.exception.first_chance),unrecognized=True));status=0x80010001
            checked(k.ContinueDebugEvent(event.pid,event.tid,status));pending=False
    except BaseException as exc:error=repr(exc)
    finally:
        if not exited:
            k.TerminateProcess(pi.process,99)
            if pending:k.ContinueDebugEvent(event.pid,event.tid,0x10002)
            k.WaitForSingleObject(pi.process,5000)
        for handle in handles:
            if handle:k.CloseHandle(handle)
    result=dict(policy=policy,exitCode=exit_code,error=error,exited=exited,elapsedSeconds=time.monotonic()-start,
        hardwareEvents=len(events),crossThreadChecks=len(cross),pendingOtherHardwareStatuses=sum(bool(x['pendingHardwareBits'])for x in cross),
        deferredUpdates=sum(x['updateDeferred']for x in cross),unknownOrLostStatusEvents=sum(not x.get('ownWatchBitSet',False)for x in events),
        all256MarkerEventsAccepted=len(events)==256 and all(x.get('knownMarkerAfterStore')and x.get('ownWatchBitSet')for x in events),
        events=events,crossThreadObservations=cross,sourceSha256=info['sourceSha256'],executableSha256=info['executableSha256'],
        toolSha256=SHA(Path(__file__).read_bytes()),ownSourceOnly=True,originalProcessAccessed=False,windowCreated=False,
        physicalAudioDevicesOpened=0,originalStartupCauseProven=False,completeGame=False)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['policy','exitCode','error','hardwareEvents','pendingOtherHardwareStatuses','deferredUpdates','unknownOrLostStatusEvents','all256MarkerEventsAccepted']}))
    assert not error
    if policy=='defer-pending':assert exit_code==0 and result['all256MarkerEventsAccepted']
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--policy',choices=['clear-other','defer-pending']);p.add_argument('--build-only',action='store_true');a=p.parse_args()
    home=a.build.resolve();assert home.is_relative_to(R/'artifacts/th14')
    if a.build_only:print(json.dumps(build(home)))
    else:
        assert a.output and a.policy;out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14');run(home,out,a.policy)
