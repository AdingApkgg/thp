"""Read-only hardware observation of an isolated retail ordinary-menu replay.

Navigate the original menu with Computer Use, separately from this observer.
No input, code, game flags, RNG or counter writes occur here. Attract callbacks
are excluded by the actual native flags. This bounded trace is not full fidelity.
"""
import argparse, ctypes as C, hashlib, importlib.util, json, os, struct, subprocess, time, traceback
from ctypes import wintypes as W
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--replay', required=True)
    parser.add_argument('--maximum-callbacks', type=int, default=40000)
    parser.add_argument('--maximum-seconds', type=int, default=1200)
    opt = parser.parse_args()
    assert 1 <= opt.maximum_callbacks <= 160000 and 1 <= opt.maximum_seconds <= 3600
    storage = module('ordinary_storage', ROOT/'tools/th14-test-storage.py')
    types = module('ordinary_types', ROOT/'tools/th14-native-session-capture.py')
    home = (ROOT/opt.output).resolve()
    assert home.is_relative_to((ROOT/'artifacts/th14').resolve())
    home.mkdir(exist_ok=False)
    (home/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    plan = dict(options=vars(opt), minimumFreeBytes=100*1024**3, maximumObservationBytes=128*1024**2,
                originalArchiveUnmodified=True, hardwareBreakpointsOnly=True, instructionWrites=0,
                gameStateWrites=0, observerInputInjection=False, uiNavigationRequired=True,
                nativeFlagsRequire=2, nativeFlagsExclude=64, silent=True, completeGame=False)
    (home/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    budget = lambda: storage.check_budget(home, plan['minimumFreeBytes'], plan['maximumObservationBytes'])
    budget()
    original = Path(json.loads((ROOT/'runtimes/th14/target.json').read_text())['executable']).parent
    work = home/'work'
    work.mkdir()
    files = []
    for name in ('th14.exe', 'th14.dat', 'thbgm.dat', 'util.dll'):
        src, dst = original/name, work/name
        checksum = storage.clone_immutable(src, dst)
        assert not os.path.samefile(src, dst)
        files.append(dict(name=name, sha256=checksum, bytes=dst.stat().st_size))
    assert files[0]['sha256'] == types.EXPECTED_EXE
    assert files[1]['sha256'] == '57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    replay = (ROOT/opt.replay).resolve(strict=True)
    assert replay.is_relative_to((ROOT/'artifacts/th14').resolve())
    replay_bytes = replay.read_bytes()
    assert replay_bytes[:6] == b't13r\x02\x00'
    appdata = work/'appdata'
    cfgdir = appdata/'ShanghaiAlice/th14'
    cfgdir.mkdir(parents=True)
    config = bytearray.fromhex(json.loads((ROOT/'artifacts/th14/replay-writer-native.json').read_text())['configs'][0]['config'])
    assert len(config) >= 0x3a
    config[0x22] = config[0x23] = 0
    config[0x39] &= ~1
    config[0x1f] = 3
    (cfgdir/'th14.cfg').write_bytes(config)
    for replay_dir in (cfgdir/'replay', work/'replay'):
        replay_dir.mkdir()
        (replay_dir/'th14_01.rpy').write_bytes(replay_bytes)
    preflight = subprocess.run(['powershell', '-NoProfile', '-Command', "@(Get-Process th14 -ErrorAction SilentlyContinue).Count"],
                               capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    assert preflight.returncode == 0 and preflight.stdout.strip() == '0', preflight.stdout+preflight.stderr
    env = {k:v for k,v in os.environ.items() if k.upper() != 'APPDATA'}
    env['APPDATA'] = str(appdata)
    envblock = C.create_unicode_buffer('\0'.join(f'{k}={v}' for k,v in sorted(env.items(), key=lambda p:p[0].upper()))+'\0\0')
    k = C.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateProcessW': ([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
        'WaitForDebugEvent': ([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),
        'ContinueDebugEvent': ([W.DWORD,W.DWORD,W.DWORD],W.BOOL),
        'ReadProcessMemory': ([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
        'Wow64GetThreadContext': ([W.HANDLE,C.c_void_p],W.BOOL),
        'Wow64SetThreadContext': ([W.HANDLE,C.c_void_p],W.BOOL),
        'TerminateProcess': ([W.HANDLE,W.UINT],W.BOOL),
        'WaitForSingleObject': ([W.HANDLE,W.DWORD],W.DWORD), 'CloseHandle': ([W.HANDLE],W.BOOL),
    }
    for name,(args,result) in signatures.items():
        getattr(k,name).argtypes, getattr(k,name).restype = args,result
    def checked(ok):
        if not ok: raise C.WinError(C.get_last_error())
    pi, si = types.ProcessInfo(), types.Startup()
    si.cb, si.flags, si.show = C.sizeof(si), 1, 1
    exe = str(work/'th14.exe')
    checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x400,envblock,str(work),C.byref(si),C.byref(pi)))
    (home/'process-start.json').write_text(json.dumps(dict(pid=pi.pid,exe=exe,onlyOwnProcess=True,configHex=config.hex(),
        files=files,replayPath=str(replay),replaySha256=digest(replay),createdUnixNs=time.time_ns()),indent=2)+'\n')
    print(json.dumps(dict(pid=pi.pid,waitingForOrdinaryMenu=True,silent=True)),flush=True)
    threads, handles = {}, {pi.process,pi.thread}
    raw, cameras, hud = bytearray(), bytearray(), bytearray()
    callbacks = 0
    started = last_player = time.monotonic()
    exited = natural_end = False
    first = None
    error = ''
    events, terminal, debug_errors = [], [], []
    def read(address,count):
        data,got = C.create_string_buffer(count), C.c_size_t()
        checked(k.ReadProcessMemory(pi.process,address,data,count,C.byref(got)))
        assert got.value == count
        return data.raw
    def u32(address): return struct.unpack('<I',read(address,4))[0]
    def context(handle):
        data = C.create_string_buffer(716)
        struct.pack_into('<I',data,0,0x10017)
        checked(k.Wow64GetThreadContext(handle,data))
        return data
    def install(tid,resume=False):
        data = context(threads[tid])
        for index,address in enumerate((0x44dbd0,0x456133,0,0)):
            struct.pack_into('<I',data,4+4*index,address)
        struct.pack_into('<I',data,20,0)
        struct.pack_into('<I',data,24,5)
        if resume: struct.pack_into('<I',data,192,struct.unpack_from('<I',data,192)[0]|0x10000)
        checked(k.Wow64SetThreadContext(threads[tid],data))
    def player():
        globals_ = struct.unpack('<32I',read(0x4f5828,128))
        player,control,enemies = [u32(a) for a in (0x4db67c,0x4db558,0x4db544)]
        assert player and control
        data = read(player,0x184c0)
        word = lambda o:struct.unpack_from('<I',data,o)[0]
        s,_,sc,g,_,gc = struct.unpack('<HHIHHI',read(0x4db508,16))
        return [u32(control+0x14),u32(0x4d6a90),u32(0x4d6a9c),
            *[word(o) for o in (0x5ec,0x5f0,0x684,0x690,0x6a4,0x6b8,0x182c4,0x1833c,0x184b0)],
            *[globals_[n] for n in (2,6,9,12,15,16,18,19,5)],s,sc,g,gc,
            u32(enemies+0xd8) if enemies else 0,
            sum(word(0x6c8+n*0xd0+0x98)!=0 for n in range(256)),
            globals_[0],globals_[1],globals_[3],u32(0x4f58a4),word(0x182d4)]
    def terminal_sample():
        pause,replay,control = [u32(a) for a in (0x4db678,0x4db688,0x4db558)]
        if not (pause and replay and control): return None
        words = list(struct.unpack('<2I',read(pause,8)))
        if words != [2,3] or u32(pause+0x108)!=1 or u32(pause+0x10c)!=3: return None
        disabled = [u32(pause+0xc8+4*n) for n in range(3)]
        if disabled != [3,2,0] or not u32(control+0x80)&0x10 or u32(replay+0x10)!=1: return None
        return dict(callbacks=callbacks,stage=u32(0x4f58a4),frame=u32(control+0x14),score=u32(0x4f5830),
                    lives=u32(0x4f5864),pauseWords=words,disabledEntries=disabled,hostMonotonicNs=time.monotonic_ns())
    try:
        while time.monotonic()-started < opt.maximum_seconds and callbacks < opt.maximum_callbacks and not natural_end and not exited:
            ev = types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(ev),250):
                code = C.get_last_error()
                if code != 121: raise C.WinError(code)
                budget()
                if callbacks and time.monotonic()-last_player>3:
                    sample = terminal_sample()
                    if sample:
                        terminal.append(sample)
                        natural_end = len(terminal)>=3 and len({r['callbacks'] for r in terminal[-3:]})==1
                continue
            status = 0x10002
            try:
                assert ev.pid == pi.pid
                if ev.kind == 3:
                    assert ev.data.create_process.base == 0x400000
                    handle = ev.data.create_process.thread
                    handles.update((ev.data.create_process.process,handle))
                    threads[ev.tid] = handle
                    if ev.data.create_process.file: k.CloseHandle(ev.data.create_process.file)
                    install(ev.tid)
                elif ev.kind == 2:
                    handle = ev.data.create_thread.thread
                    handles.add(handle)
                    if 0x400000 <= ev.data.create_thread.start < 0x500000:
                        threads[ev.tid] = handle
                        install(ev.tid)
                elif ev.kind == 4: threads.pop(ev.tid,None)
                elif ev.kind == 5: exited = True
                elif ev.kind == 6:
                    if ev.data.dll.file: k.CloseHandle(ev.data.dll.file)
                elif ev.kind == 1:
                    exception = ev.data.exception.record
                    if exception.code in (0x80000004,0x4000001e) and ev.tid in threads:
                        data = context(threads[ev.tid])
                        pc = struct.unpack_from('<I',data,184)[0]
                        if pc not in (0x44dbd0,0x456133): status = 0x80010001
                        else:
                            flags = u32(0x4f58b8)
                            if flags&2 and not flags&64:
                                if pc == 0x456133:
                                    event = dict(pc=pc,callbacks=callbacks,flags=flags,stage=u32(0x4f58a4),rngHex=read(0x4db508,16).hex(),hostMonotonicNs=time.monotonic_ns())
                                    events.append(event)
                                    with (home/'seed-restore-events.jsonl').open('a') as stream: stream.write(json.dumps(event)+'\n')
                                else:
                                    words = player()
                                    assert len(words)==32 and words[27:30]==[1,1,1], words[27:31]
                                    if first is None:
                                        manager=u32(0x4db688)
                                        assert manager and u32(manager+0x10)==1
                                        first=dict(words=words,flags=flags,replayManagerMode=u32(manager+0x10),
                                            rngHex=read(0x4db508,16).hex(),originalClockInput=u32(0x4d9688),
                                            originalSecurityCookie=u32(0x4d0cc0),hostMonotonicNs=time.monotonic_ns())
                                        (home/'first-player.json').write_text(json.dumps(first,indent=2)+'\n')
                                    raw.extend(struct.pack('<32I',*words))
                                    cameras.extend(read(0x4d9514,0x124))
                                    pointer=u32(0x4db550)
                                    hud.extend(struct.pack('<2I',u32(pointer+0x140),u32(0x4f5830)))
                                    callbacks+=1
                                    last_player=time.monotonic()
                                    if callbacks%300==0 or callbacks==1:
                                        budget()
                                        (home/'selected-state.u32').write_bytes(raw)
                                        (home/'world-camera.raw').write_bytes(cameras)
                                        (home/'hud-score.u32').write_bytes(hud)
                                        progress=dict(callbacks=callbacks,stage=words[30],stageFrame=words[0],elapsedSeconds=time.monotonic()-started)
                                        (home/'progress.json').write_text(json.dumps(progress)+'\n')
                                        print(json.dumps(progress),flush=True)
                            install(ev.tid,True)
                    elif exception.code not in (0x80000003,0x4000001f):
                        debug_errors.append(dict(code=exception.code,address=exception.address,firstChance=ev.data.exception.first_chance))
                        status=0x80010001
            finally: checked(k.ContinueDebugEvent(ev.pid,ev.tid,status))
    except BaseException as exc:
        error=repr(exc)
        (home/'exception.txt').write_text(traceback.format_exc(),encoding='utf8')
    finally:
        if not exited:
            k.TerminateProcess(pi.process,0)
            deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                ev=types.DebugEvent()
                if not k.WaitForDebugEvent(C.byref(ev),100): continue
                if ev.kind==6 and ev.data.dll.file: k.CloseHandle(ev.data.dll.file)
                checked(k.ContinueDebugEvent(ev.pid,ev.tid,0x10002))
                if ev.kind==5: break
            k.WaitForSingleObject(pi.process,2000)
        for handle in handles:
            if handle: k.CloseHandle(handle)
        for name,data in (('selected-state.u32',raw),('world-camera.raw',cameras),('hud-score.u32',hud)):
            (home/name).write_bytes(data)
        report=dict(plan=plan,pid=pi.pid,error=error,debugErrors=debug_errors,callbacks=callbacks,
            firstPlayer=first,recordedStages=sorted({r[30] for r in struct.iter_unpack('<32I',raw)}),
            observedForcedReplayEndMenu=natural_end,terminalMenuSamples=terminal,
            sourceSha256=digest(home/'run-tool.py'),files=files,configHex=config.hex(),
            replaySha256=digest(replay),originalArchiveSha256=files[1]['sha256'],
            selectedSha256=hashlib.sha256(raw).hexdigest(),seedRestoreEvents=events,
            elapsedSeconds=time.monotonic()-started,instructionWrites=0,gameStateWrites=0,
            debuggerPausesAffectTiming=True,completeGame=False,nativeEquivalent=False)
        (home/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(callbacks=callbacks,error=error,naturalEnd=natural_end)),flush=True)
    if error or not first: raise SystemExit(1)

if __name__=='__main__': main()
