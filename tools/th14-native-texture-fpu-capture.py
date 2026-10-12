"""Observe real retail texture upload precision in an isolated hidden child.

Only restored debugger breakpoints in this owned child's RAM are written.
Original files are read-only; configuration and score are workspace-local.
Ordinary no-input title/automatic attract, silent audio. No GPU pixel claim.
"""
import argparse, ctypes as C, hashlib, importlib, json, os, shutil, struct, time
from ctypes import wintypes as W
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
types=importlib.import_module('th14-native-session-capture')
sha=lambda b:hashlib.sha256(b).hexdigest()
BREAKS={0x47cb70:0x55,0x47cc68:0xff,0x47ccf8:0xff,
        0x46b235:0xff,0x46b238:0x85,0x44dbd0:0x55}

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--seconds',type=float,default=65)
    opt=args.parse_args()
    assert os.name=='nt' and C.sizeof(C.c_void_p)==8
    work=ROOT/'artifacts/th14/native-texture-fpu-reference'
    work.mkdir(parents=True,exist_ok=True)
    target=json.loads((ROOT/'runtimes/th14/target.json').read_text(encoding='utf-8'))
    original=Path(target['dataArchives']['th14.dat']['path']).parent
    manifest=[]
    for name in ['th14.exe','th14.dat','thbgm.dat','util.dll']:
        src,dst=original/name,work/name
        source_hash=sha(src.read_bytes())
        if not dst.exists() or sha(dst.read_bytes())!=source_hash:
            shutil.copyfile(src,dst)
        assert sha(dst.read_bytes())==source_hash
        manifest.append(dict(name=name,bytes=dst.stat().st_size,sha256=source_hash))
    assert manifest[0]['sha256']==types.EXPECTED_EXE
    appdata=work/'appdata';cfgdir=appdata/'ShanghaiAlice/th14';cfgdir.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'artifacts/th14/replay-writer-native.json').read_text())['configs'][0]['config']
    cfg=bytearray.fromhex(config);cfg[0x22]=cfg[0x23]=0;cfg[0x39]&=~1;cfg[0x1f]=3
    (cfgdir/'th14.cfg').write_bytes(cfg)
    env={k:v for k,v in os.environ.items() if k.upper()!='APPDATA'};env['APPDATA']=str(appdata)
    envblock=C.create_unicode_buffer('\0'.join(f'{k}={v}' for k,v in sorted(env.items(),key=lambda q:q[0].upper()))+'\0\0')
    k=C.WinDLL('kernel32',use_last_error=True)
    signatures={
        'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
        'WaitForDebugEvent':([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),
        'ContinueDebugEvent':([W.DWORD,W.DWORD,W.DWORD],W.BOOL),
        'ReadProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
        'WriteProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
        'FlushInstructionCache':([W.HANDLE,C.c_void_p,C.c_size_t],W.BOOL),
        'Wow64GetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
        'Wow64SetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
        'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),
        'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),
        'CloseHandle':([W.HANDLE],W.BOOL),
    }
    for name,(arguments,result) in signatures.items():
        f=getattr(k,name);f.argtypes=arguments;f.restype=result
    def checked(ok):
        if not ok:raise C.WinError(C.get_last_error())
    pi,si=types.ProcessInfo(),types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0
    exe=str(work/'th14.exe')
    checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x400,envblock,str(work),C.byref(si),C.byref(pi)))
    print('Own hidden retail texture reference',pi.pid,flush=True)
    report=dict(executableSha256=types.EXPECTED_EXE,files=manifest,pid=pi.pid,configurationHex=cfg.hex(),
                captureToolSha256=sha(Path(__file__).read_bytes()),contextTypesToolSha256=sha(Path(types.__file__).read_bytes()),
                noInputInjection=True,completeGame=False,nativeEquivalent=False,records=[],events=[],error='',
                scope='Real isolated retail640x480 window-mode title/first automatic attract. Entry and actual D3DX CreateTexture/LoadSurfaceFromMemory call-site x87 control captured with WOW64 floating context. Only debugger breakpoints in owned child RAM; workspace-local config/score; silent. Timing may change under debugger. No pixel readback or full-game equivalence claim.')
    def read(address,count):
        buffer,got=C.create_string_buffer(count),C.c_size_t()
        checked(k.ReadProcessMemory(pi.process,address,buffer,count,C.byref(got)))
        assert got.value==count
        return buffer.raw
    def write(address,data):
        got=C.c_size_t();checked(k.WriteProcessMemory(pi.process,address,C.create_string_buffer(data),len(data),C.byref(got)))
        checked(k.FlushInstructionCache(pi.process,address,len(data)))
    def word(address):return struct.unpack('<I',read(address,4))[0]
    def resource_name(entry):
        manager=word(0x4f56cc)
        for slot in range(26):
            resource=word(manager+0xbc7b0c+slot*4)
            if not resource:continue
            first,count=word(resource+0x124),word(resource+0x110)
            if first<=entry<first+count*24 and (entry-first)%24==0:
                return dict(resource=read(resource+4,256).split(b'\0',1)[0].decode('cp932','replace'),file=slot,chunk=(entry-first)//24)
        return dict(resource=None,entry=hex(entry))
    threads,oldbytes,pending={},{},None
    current={};start=time.monotonic();exited=False;seen_player=False
    try:
        while time.monotonic()-start<opt.seconds and not seen_player:
            event=types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(event),200):
                if C.get_last_error()==121:continue
                raise C.WinError(C.get_last_error())
            status=0x10002
            if event.kind==3:
                c=event.data.create_process;assert c.base==0x400000
                if c.file:k.CloseHandle(c.file)
                threads[event.tid]=c.thread
                for address,expected in BREAKS.items():
                    b=read(address,1);assert b==bytes([expected]),hex(address)
                    oldbytes[address]=b;write(address,b'\xcc')
            elif event.kind==2:threads[event.tid]=event.data.create_thread.thread
            elif event.kind==4:threads.pop(event.tid,None)
            elif event.kind==6:
                if event.data.dll.file:k.CloseHandle(event.data.dll.file)
            elif event.kind==5:
                report['exitCode']=event.data.exit_code;exited=True
            elif event.kind==1:
                x=event.data.exception.record
                if x.code in (0x80000003,0x4000001f) and x.address in BREAKS:
                    address=x.address;context=C.create_string_buffer(716)
                    # FLOATING_POINT bit0x8 is required for FloatSave.ControlWord.
                    struct.pack_into('<I',context,0,0x1001f)
                    checked(k.Wow64GetThreadContext(threads[event.tid],context))
                    sp=struct.unpack_from('<I',context,196)[0]
                    cw=struct.unpack_from('<I',context,28)[0]&0xffff
                    assert cw&0x3f==0x3f,hex(cw)
                    row=dict(address=hex(address),thread=event.tid,fpcw=cw,precision={0:24,0x200:53,0x300:64}.get(cw&0x300),rounding=(cw>>10)&3)
                    if address==0x47cb70:
                        entry=word(sp+4);current[event.tid]=resource_name(entry)
                        row.update(current[event.tid]);row['requestedFormat']=word(sp+12)
                    elif address in (0x47cc68,0x47ccf8):
                        row.update(current.get(event.tid,{}))
                        args=[word(sp+i*4) for i in range(8 if address==0x47cc68 else 10)]
                        if address==0x47cc68:
                            row['creationArguments']=args[1:7]
                        else:
                            src=list(struct.unpack('<4i',read(args[7],16)));dst=list(struct.unpack('<4i',read(args[2],16)))
                            size=args[5]*src[3];assert 0<size<=0x4000000
                            row.update(sourceRect=src,destinationRect=dst,sourceFormat=args[4],pitch=args[5],filter=args[8],sourceBytes=size,sourceSha256=sha(read(args[3],size)))
                    elif address==0x46b235:
                        args=[word(sp+i*4) for i in range(7)]
                        row.update(deviceType=args[2],behaviorFlags=args[4])
                    elif address==0x46b238:
                        row['result']=struct.unpack_from('<I',context,176)[0]
                    elif address==0x44dbd0:
                        row['selection']=[word(0x4f5828+4*i) for i in (0,1,3)]+[word(0x4f58a4)]
                        seen_player=True
                    report['records'].append(row)
                    struct.pack_into('<I',context,184,address)
                    flags=struct.unpack_from('<I',context,192)[0];struct.pack_into('<I',context,192,flags|0x100)
                    write(address,oldbytes[address]);checked(k.Wow64SetThreadContext(threads[event.tid],context))
                    assert pending is None
                    pending=(event.tid,address)
                elif x.code in (0x80000004,0x4000001e) and pending and pending[0]==event.tid:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[event.tid],context))
                    flags=struct.unpack_from('<I',context,192)[0];struct.pack_into('<I',context,192,flags&~0x100)
                    checked(k.Wow64SetThreadContext(threads[event.tid],context));write(pending[1],b'\xcc');pending=None
                elif x.code not in (0x80000003,0x4000001f):
                    if len(report['events'])<50:report['events'].append(dict(code=hex(x.code),address=hex(x.address or 0),firstChance=event.data.exception.first_chance))
                    status=0x80010001
            checked(k.ContinueDebugEvent(event.pid,event.tid,status))
            if exited:break
        report['seenFirstPlayer']=seen_player;report['timedOut']=not seen_player and not exited
    except Exception as e:
        report['error']=str(e)
        raise
    finally:
        if not exited:
            for address,b in oldbytes.items():
                try:write(address,b)
                except OSError:pass
            k.TerminateProcess(pi.process,0);k.WaitForSingleObject(pi.process,2000)
        k.CloseHandle(pi.thread);k.CloseHandle(pi.process)
        report['elapsedSeconds']=round(time.monotonic()-start,3)
        output=ROOT/'artifacts/th14/native-texture-fpu-capture.json'
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Native upload FPU records',len(report['records']),'first player',seen_player,'error',report['error'],flush=True)

if __name__=='__main__':main()
