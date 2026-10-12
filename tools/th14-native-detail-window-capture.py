"""Capture retail TH14 at its player-update boundary in an isolated child.

No attachment to existing processes, input injection, or original file writes.
Code modifications are restored debugger breakpoints in the child RAM.
CreateProcess uses a hidden window and workspace-local APPDATA/config/score.
Pointers follow ParaKit's TH14 layout, checked against our fixed 1.00b image.
This is a state baseline, not a GPU/audio or whole-game equivalence proof.
"""
import argparse, ctypes as C, hashlib, json, os, shutil, struct, time
from ctypes import wintypes as W
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_EXE = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
BP = 0x44dbd0


class Startup(C.Structure):
    _fields_ = [('cb', W.DWORD), ('reserved', W.LPWSTR), ('desktop', W.LPWSTR),
                ('title', W.LPWSTR), ('x', W.DWORD), ('y', W.DWORD),
                ('xs', W.DWORD), ('ys', W.DWORD), ('xc', W.DWORD),
                ('yc', W.DWORD), ('fill', W.DWORD), ('flags', W.DWORD),
                ('show', W.WORD), ('nreserved', W.WORD), ('preserved', C.c_void_p),
                ('stdin', W.HANDLE), ('stdout', W.HANDLE), ('stderr', W.HANDLE)]


class ProcessInfo(C.Structure):
    _fields_ = [('process', W.HANDLE), ('thread', W.HANDLE),
                ('pid', W.DWORD), ('tid', W.DWORD)]


class ExceptionRecord(C.Structure):
    _fields_ = [('code', W.DWORD), ('flags', W.DWORD), ('record', C.c_void_p),
                ('address', C.c_void_p), ('nparameters', W.DWORD),
                ('parameters', C.c_size_t * 15)]


class ExceptionInfo(C.Structure):
    _fields_ = [('record', ExceptionRecord), ('first_chance', W.DWORD)]


class CreateProcessInfo(C.Structure):
    _fields_ = [('file', W.HANDLE), ('process', W.HANDLE), ('thread', W.HANDLE),
                ('base', C.c_void_p), ('debug_offset', W.DWORD),
                ('debug_size', W.DWORD), ('tls', C.c_void_p),
                ('start', C.c_void_p), ('image_name', C.c_void_p), ('unicode', W.WORD)]


class CreateThreadInfo(C.Structure):
    _fields_ = [('thread', W.HANDLE), ('tls', C.c_void_p), ('start', C.c_void_p)]


class LoadDllInfo(C.Structure):
    _fields_ = [('file', W.HANDLE), ('base', C.c_void_p), ('debug_offset', W.DWORD),
                ('debug_size', W.DWORD), ('image_name', C.c_void_p), ('unicode', W.WORD)]


class DebugData(C.Union):
    _fields_ = [('exception', ExceptionInfo), ('create_process', CreateProcessInfo),
                ('create_thread', CreateThreadInfo), ('dll', LoadDllInfo),
                ('exit_code', W.DWORD)]


class DebugEvent(C.Structure):
    _fields_ = [('kind', W.DWORD), ('pid', W.DWORD), ('tid', W.DWORD), ('data', DebugData)]


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--frames', type=int, default=1200)
    args.add_argument('--seconds', type=float, default=55)
    args.add_argument('--output', default='artifacts/th14/native-session-oct10.json')
    args.add_argument('--work-directory', help='Separate workspace artifact directory for this reference child.')
    args.add_argument('--demo-replay', help='Copy a test replay as three loose demo files in a separate artifact directory; verify the resulting native selection before using the trace.')
    args.add_argument('--reference-archive', help='Workspace diagnostic archive with an explicitly replaced demo recording; requires separate work directory.')
    args.add_argument('--stop-selection-change', action='store_true', help='End this capture before a different attract replay selection is sampled.')
    args.add_argument('--rng-frame', type=int, default=0, help='Watch gameplay RNG writes for one selected demo player interval.')
    args.add_argument('--rng-demo', type=int, choices=(0,1,2), default=0)
    args.add_argument('--startup-visual-rng', action='store_true', help='Watch visual seed writes on isolated child threads until the first player snapshot.')
    args.add_argument('--beam-scratch', action='store_true', help='Capture retail circular-beam fallback stack values in this child.')
    args.add_argument('--bullet-details', action='store_true', help='Capture active enemy-bullet fields through stage frame 350.')
    args.add_argument('--fire-details', action='store_true', help='Capture original Sakuya demo bullet-emitter calls through frame 350.')
    args.add_argument('--detail-start',type=int,default=0)
    args.add_argument('--detail-end',type=int,default=0)
    opt = args.parse_args()
    assert 0<=opt.detail_start<=opt.detail_end
    if os.name != 'nt' or C.sizeof(C.c_void_p) != 8:
        raise RuntimeError('Requires 64-bit Windows Python (WOW64 child).')
    assert C.sizeof(ExceptionRecord) == 152 and C.sizeof(DebugEvent) == 176
    target = json.loads((ROOT / 'runtimes/th14/target.json').read_text(encoding='utf-8'))
    original = Path(target['dataArchives']['th14.dat']['path']).parent
    work = (ROOT / opt.work_directory).resolve() if opt.work_directory else ROOT / 'artifacts/th14/native-reference-oct10'
    if opt.work_directory and not work.is_relative_to((ROOT/'artifacts/th14').resolve()):
        raise RuntimeError('Reference work directory must remain under workspace artifacts/th14.')
    if (opt.demo_replay or opt.reference_archive) and not opt.work_directory:
        raise RuntimeError('Test replay/archive requires a separate --work-directory.')
    work.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in ('th14.exe', 'th14.dat', 'thbgm.dat', 'util.dll'):
        src, dst = ((ROOT/opt.reference_archive).resolve() if name=='th14.dat' and opt.reference_archive else original/name), work / name
        if opt.reference_archive and name=='th14.dat' and not src.is_relative_to((ROOT/'artifacts/th14').resolve()):
            raise RuntimeError('Diagnostic archive must be under workspace artifacts/th14.')
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, dst)
        digest = hashlib.sha256(dst.read_bytes()).hexdigest()
        manifest.append(dict(name=name, bytes=dst.stat().st_size, sha256=digest))
    if manifest[0]['sha256'] != EXPECTED_EXE:
        raise RuntimeError('Executable version mismatch; no process started.')
    test_replay = None
    if opt.demo_replay:
        data = (ROOT/opt.demo_replay).resolve().read_bytes()
        # TH14 retail deliberately retains TH13's t13r/version2 header.
        if len(data)<0x24 or data[:6] != b't13r\x02\x00':
            raise RuntimeError('Test replay is not retail TH14 format.')
        for name in ('demo0.rpy','demo1.rpy','demo2.rpy'):
            (work/name).write_bytes(data)
        test_replay = dict(path=str((ROOT/opt.demo_replay).resolve()),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),delivery='loose demo files; actual native selection must be checked')
    appdata = work / 'appdata'
    cfgdir = appdata / 'ShanghaiAlice/th14'
    cfgdir.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / 'artifacts/th14/replay-writer-native.json').read_text())['configs'][0]['config']
    cfg = bytearray.fromhex(config)
    cfg[0x22] = cfg[0x23] = 0  # Silent native reference; audio excluded.
    # WinMain 469595 checks config +38 bit 100 to show a startup screen-mode
    # dialog. Disable that optional dialog in this isolated config, so the
    # hidden reference can enter its ordinary automatic title/demo path.
    cfg[0x39] &= ~1
    cfg[0x1f] = 3  # Native 640x480 window mode (46ae40/46af7d).
    (cfgdir / 'th14.cfg').write_bytes(cfg)
    env = {k: v for k, v in os.environ.items() if k.upper() != 'APPDATA'}
    env['APPDATA'] = str(appdata)
    envblock = C.create_unicode_buffer('\0'.join(f'{k}={v}' for k, v in sorted(env.items(), key=lambda p: p[0].upper())) + '\0\0')
    k = C.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateProcessW': ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR, C.POINTER(Startup), C.POINTER(ProcessInfo)], W.BOOL),
        'WaitForDebugEvent': ([C.POINTER(DebugEvent), W.DWORD], W.BOOL),
        'ContinueDebugEvent': ([W.DWORD, W.DWORD, W.DWORD], W.BOOL),
        'ReadProcessMemory': ([W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)], W.BOOL),
        'WriteProcessMemory': ([W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)], W.BOOL),
        'FlushInstructionCache': ([W.HANDLE, C.c_void_p, C.c_size_t], W.BOOL),
        'Wow64GetThreadContext': ([W.HANDLE, C.c_void_p], W.BOOL),
        'Wow64SetThreadContext': ([W.HANDLE, C.c_void_p], W.BOOL),
        'TerminateProcess': ([W.HANDLE, W.UINT], W.BOOL),
        'WaitForSingleObject': ([W.HANDLE, W.DWORD], W.DWORD),
        'CloseHandle': ([W.HANDLE], W.BOOL),
        'SuspendThread': ([W.HANDLE], W.DWORD),
        'ResumeThread': ([W.HANDLE], W.DWORD),
    }
    for name, (argtypes, restype) in signatures.items():
        f = getattr(k, name)
        f.argtypes, f.restype = argtypes, restype
    def checked(ok):
        if not ok:
            raise C.WinError(C.get_last_error())
    pi, si = ProcessInfo(), Startup()
    si.cb, si.flags, si.show = C.sizeof(si), 1, 0  # STARTF_USESHOWWINDOW/SW_HIDE.
    exe = str(work / 'th14.exe')
    checked(k.CreateProcessW(exe, C.create_unicode_buffer('"' + exe + '"'), None, None, False,
                             2 | 0x400, envblock, str(work), C.byref(si), C.byref(pi)))
    print(f'Own isolated retail child {pi.pid}; capturing at {BP:#x}', flush=True)
    report = dict(executableSha256=EXPECTED_EXE, files=manifest, pid=pi.pid,
                  testReplay=test_replay,
                  referenceArchive=str((ROOT/opt.reference_archive).resolve()) if opt.reference_archive else None,
                  breakpoint=hex(BP), configurationHex=cfg.hex(), appdata=str(appdata),
                  noInputInjection=True, frames=[], events=[], rngWrites=[], beamFallbacks=[], bulletFires=[], error='', completeGame=False,
                  scope='Hidden isolated retail auto-attract; all threads paused at player entry for each snapshot. Only child RAM breakpoint modified. Silent config. No native GPU/audio comparison.')
    def read(p, n):
        b, got = C.create_string_buffer(n), C.c_size_t()
        checked(k.ReadProcessMemory(pi.process, p, b, n, C.byref(got)))
        if got.value != n:
            raise RuntimeError(f'Short process read at {p:#x}')
        return b.raw
    def write(p, b):
        got = C.c_size_t()
        checked(k.WriteProcessMemory(pi.process, p, C.create_string_buffer(b), len(b), C.byref(got)))
        checked(k.FlushInstructionCache(pi.process, p, len(b)))
    def u32(p): return struct.unpack('<I', read(p, 4))[0]
    def s32(p): return struct.unpack('<i', read(p, 4))[0]
    def snapshot():
        player, control, enemies = u32(0x4db67c), u32(0x4db558), u32(0x4db544)
        if not player or not control:
            return None
        p = read(player, 0x184c0)
        pu = lambda off: struct.unpack_from('<I', p, off)[0]
        ps = lambda off: struct.unpack_from('<i', p, off)[0]
        globals_ = [s32(0x4f5828 + n * 4) for n in range(32)]
        row = dict(index=len(report['frames']), selection=[globals_[0], globals_[1], globals_[3], s32(0x4f58a4)],
                    stageFrame=s32(control + 0x14), controlFlags=u32(control + 0x80),
                    held=u32(0x4d6a90), pressed=u32(0x4d6a9c), released=u32(0x4d6aa0),
                    globals=globals_, scriptRng=list(struct.unpack('<HHI', read(0x4db508, 8))),
                    replayRng=list(struct.unpack('<HHI', read(0x4db510, 8))),
                    player=[ps(o) for o in (0x5ec, 0x5f0, 0x684, 0x690, 0x6a4, 0x6b8, 0x182c4, 0x1833c, 0x184b0)],
                    playerFloatBits=[pu(0x5e0), pu(0x5e4)], scaleFlags=pu(0x182d4),
                    enemyCount=s32(enemies + 0xd8) if enemies else 0,
                    shots=sum(pu(0x6c8 + n * 0xd0 + 0x98) != 0 for n in range(256)),
                    shotRewardCounters=[pu(off) for off in (0x184b4,0x184b8,0x184bc)])
        replay_manager=u32(0x4db688)
        row['replayMode']=u32(replay_manager+0x10) if replay_manager else 0
        popup_manager=u32(0x4db694)
        row['popupCursor']=u32(popup_manager+0x14) if popup_manager else 0
        popup_words=list(struct.unpack('<324I',read(popup_manager+0x5e4,18*72))) if popup_manager else [0]*324
        for n in range(18):popup_words[n*18+11]=int(popup_words[n*18+11]!=0)
        row['popupWords']=popup_words
        row['enemyIds']=[];row['enemyNextId']=u32(enemies+0xdc) if enemies else 0
        idnode,seen=u32(enemies+0xd0) if enemies else 0,set()
        while idnode and idnode not in seen and len(seen)<1000:
            seen.add(idnode);ep=u32(idnode)
            if ep:row['enemyIds'].append(u32(ep+0x11e4))
            idnode=u32(idnode+4)
        if opt.detail_start <= row['stageFrame'] <= opt.detail_end or row['stageFrame'] <= 1000 or 1200 <= row['stageFrame'] <= 1400 or 2920 <= row['stageFrame'] <= 2950 or 3000 <= row['stageFrame'] <= 3120 or 3690 <= row['stageFrame'] <= 3705:
            row['liveShots'] = [[n, pu(o + 0x98), pu(o + 0x1c), pu(o + 0xac),
                                 *[pu(o + f) for f in (0x54,0x58,0x5c,0x6c,0x70,0xb0,0xb4)]]
                                for n in range(256) if pu((o := 0x6c8+n*0xd0) + 0x98)]
            row['enemyDetails'] = []
            row['enemyPhaseDetails'] = []
            node, visited = u32(enemies + 0xd0) if enemies else 0, set()
            while node and node not in visited and len(visited) < 1000:
                visited.add(node); enemy = u32(node)
                if enemy:
                    body = enemy + 0x11f0
                    row['enemyDetails'].append([u32(body + off) for off in (0x3f74,0x3f78,0x4054,0x44,0x48,0x110,0x114,0x118,0x11c,0x2d4)])
                    row['enemyPhaseDetails'].append([u32(body+0x2c0), *[u32(body+0x3f90+4*n) for n in range(14)], *[u32(body+0x406c+16*n) for n in range(8)]])
                node = u32(node + 4)
        if 3000 <= row['stageFrame'] <= 3120:
            row['damageAreas']=[]
            for j in range(256):
                a=0xde18+j*0xa4
                if not pu(a+0x10)&1:continue
                owner=pu(a+0x98)-player
                valid=0x6c8 <= owner < 0xde18 and (owner-0x6c8)%0xd0==0
                row['damageAreas'].append([j,*[pu(a+off) for off in (0x10,0x14,0x1c,0x24,0x28,0x2c,0x30,0x34,0x70,0x74,0x78,0x84,0x88,0x8c,0x90,0x94)],int(pu(a+0xa0)!=0),pu(owner+0x1c) if valid else 0,pu(owner+0x10) if valid else 0])
        if opt.detail_start <= row['stageFrame'] <= opt.detail_end or 900 <= row['stageFrame'] <= 1000:
            manager=u32(0x4db660);row['itemDetails']=[]
            if manager:
                pool=read(manager+0x14,4696*0xc18)
                word=lambda offset:struct.unpack_from('<I',pool,offset)[0]
                for n in range(4696):
                    base=n*0xc18
                    if word(base+0xbf0):row['itemDetails'].append([word(base+off) for off in (0xbf0,0xbf4,0xbf8,0xbac,0xbb0,0xbb4,0xbb8,0xbbc,0xbc0,0xbd0,0xbfc,0xc00)])
        if opt.bullet_details and (opt.detail_start <= row['stageFrame'] <= opt.detail_end or row['stageFrame'] <= 350):
            manager=u32(0x4db530);row['bulletDetails']=[]
            node,visited=u32(manager+0x80) if manager else 0,set()
            while node and node not in visited and len(visited)<2000:
                visited.add(node);bullet=u32(node)
                if bullet:
                    data=read(bullet,0x13f4)
                    word=lambda offset:struct.unpack_from('<I',data,offset)[0]
                    row['bulletDetails'].append([struct.unpack_from('<H',data,0xc0e)[0],*[word(off) for off in (0x20,0x24,0xbc0,0xbc4,0xbc8,0xbcc,0xbd0,0xbd4,0xbd8,0xbdc,0xbe0,0xbe4,0x13c4,0x13ec,0xc04)]])
                node=u32(node+4)
        return row
    threads = {pi.tid: pi.thread}
    pending_step = None
    pending_address = BP
    beam_bp = 0x45286f
    beam_oldbyte = None
    fire_bp,fire_oldbyte=0x4191a0,None
    armed, oldbyte, exited = False, None, False
    watching_rng = False
    watching_startup=False
    rng_watch_address=0x4db510
    start = time.monotonic()
    selection_changed = False
    try:
        while time.monotonic() - start < opt.seconds and len(report['frames']) < opt.frames and not selection_changed:
            ev = DebugEvent()
            if not k.WaitForDebugEvent(C.byref(ev), 200):
                error = C.get_last_error()
                if error == 121: continue  # ERROR_SEM_TIMEOUT.
                raise C.WinError(error)
            status = 0x10002  # DBG_CONTINUE.
            if ev.kind == 3:
                c = ev.data.create_process
                if c.base != 0x400000: raise RuntimeError('Unexpected retail image base')
                if c.file: k.CloseHandle(c.file)
                threads[ev.tid] = c.thread
                oldbyte = read(BP, 1)
                if oldbyte != b'\x55': raise RuntimeError('Unexpected player entry opcode')
                write(BP, b'\xcc'); armed = True
                if opt.startup_visual_rng:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid],context))
                    struct.pack_into('<I',context,4,0x4db508);struct.pack_into('<I',context,20,0);struct.pack_into('<I',context,24,0x50001)
                    checked(k.Wow64SetThreadContext(threads[ev.tid],context))
                    watching_rng=watching_startup=True;rng_watch_address=0x4db508
                if opt.beam_scratch:
                    beam_oldbyte=read(beam_bp,1)
                    if beam_oldbyte!=b'\xf3':raise RuntimeError('Unexpected beam fallback opcode')
                    write(beam_bp,b'\xcc')
            elif ev.kind == 2:
                threads[ev.tid] = ev.data.create_thread.thread
                if watching_startup:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid],context))
                    struct.pack_into('<I',context,4,0x4db508);struct.pack_into('<I',context,20,0);struct.pack_into('<I',context,24,0x50001)
                    checked(k.Wow64SetThreadContext(threads[ev.tid],context))
            elif ev.kind == 4:
                threads.pop(ev.tid, None)
            elif ev.kind == 6:
                if ev.data.dll.file: k.CloseHandle(ev.data.dll.file)
            elif ev.kind == 5:
                report['exitCode'] = ev.data.exit_code
                exited = True
            elif ev.kind == 1:
                x = ev.data.exception.record
                # WOW64 reports 32-bit breakpoint/step events as WX86 status
                # codes to a 64-bit debugger. Continuing those without the
                # rewind would skip the original push-ebp and corrupt a frame.
                if x.code in (0x80000003, 0x4000001f) and x.address == BP:
                    row = snapshot()
                    if opt.stop_selection_change and row is not None and report['frames'] and row['selection']!=report['frames'][0]['selection']:
                        selection_changed=True
                        report['nextSelection']=row['selection']
                        row=None
                    if row is not None:
                        report['frames'].append(row)
                        if 'updateCallbacks' not in report:
                            report['captureToolSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                            callbacks=[];dispatcher=u32(0x4db51c)
                            link=u32(dispatcher+0x18) if dispatcher else 0;visited=set()
                            while link and link not in visited and len(visited)<256:
                                visited.add(link);callback=u32(link)
                                if callback:callbacks.append(dict(priority=s32(callback),flags=u32(callback+4),function=hex(u32(callback+8)),owner=hex(u32(callback+0x24))))
                                link=u32(link+4)
                            report['updateCallbacks']=callbacks
                    if opt.fire_details and row and row['selection']==[2,0,1,1] and fire_oldbyte is None:
                        fire_oldbyte=read(fire_bp,1)
                        if fire_oldbyte!=b'\x55':raise RuntimeError('Unexpected emitter entry opcode')
                        write(fire_bp,b'\xcc')
                    if row and len(report['frames']) % 300 == 0:
                        print(f"Captured {len(report['frames'])} frames, selection={row['selection']} player={row['player'][:4]}", flush=True)
                    context = C.create_string_buffer(716)
                    struct.pack_into('<I', context, 0, 0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid], context))
                    selection=([0,0,1,3],[1,1,1,4],[2,0,1,1])[opt.rng_demo]
                    watch=bool(opt.rng_frame and row and row['selection']==selection and row['stageFrame']==opt.rng_frame)
                    if watching_startup and row is None:watch=True
                    elif watching_startup:
                        watching_startup=False
                        for tid,handle in threads.items():
                            if tid==ev.tid:continue
                            other=C.create_string_buffer(716);struct.pack_into('<I',other,0,0x10017)
                            checked(k.Wow64GetThreadContext(handle,other))
                            struct.pack_into('<I',other,4,0);struct.pack_into('<I',other,20,0);struct.pack_into('<I',other,24,0)
                            checked(k.Wow64SetThreadContext(handle,other))
                    if watch or watching_rng:
                        # WOW64_CONTEXT Dr0/Dr6/Dr7 at 4/20/24. Local write
                        # watchpoint, length 2 bytes, only on this child thread.
                        rng_watch_address=0x4db508 if watching_startup else 0x4db510
                        struct.pack_into('<I', context, 4, rng_watch_address if watch else 0)
                        struct.pack_into('<I', context, 20, 0)
                        struct.pack_into('<I', context, 24, 0x50001 if watch else 0)
                        watching_rng=watch
                    struct.pack_into('<I', context, 184, BP)
                    flags = struct.unpack_from('<I', context, 192)[0]
                    struct.pack_into('<I', context, 192, flags | 0x100)
                    write(BP, oldbyte); armed = False
                    checked(k.Wow64SetThreadContext(threads[ev.tid], context))
                    pending_step = ev.tid
                    pending_address = BP
                elif x.code in (0x80000003,0x4000001f) and opt.beam_scratch and x.address==beam_bp:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid],context))
                    sp=struct.unpack_from('<I',context,196)[0];obj=struct.unpack_from('<I',context,156)[0]
                    target=struct.unpack_from('<I',context,160)[0];fp=struct.unpack_from('<I',context,180)[0]
                    area=u32(obj+0xc0);control=u32(0x4db558)
                    report['beamFallbacks'].append(dict(stageFrame=s32(control+0x14),selection=[s32(0x4f5828+4*n) for n in (0,1,3)]+[s32(0x4f58a4)],
                        scratchBits=u32(sp+0x2c),origin=list(struct.unpack('<3f',read(obj+0x54,12))),angle=struct.unpack('<f',read(obj+0x70,4))[0],
                        target=list(struct.unpack('<3f',read(target,12))),size=list(struct.unpack('<2f',read(area+0x24,8))),radius=struct.unpack('<f',read(fp+0x10,4))[0]))
                    struct.pack_into('<I',context,184,beam_bp);flags=struct.unpack_from('<I',context,192)[0];struct.pack_into('<I',context,192,flags|0x100)
                    write(beam_bp,beam_oldbyte);checked(k.Wow64SetThreadContext(threads[ev.tid],context));pending_step=ev.tid;pending_address=beam_bp
                elif x.code in (0x80000003,0x4000001f) and fire_oldbyte and x.address==fire_bp:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid],context));sp=struct.unpack_from('<I',context,196)[0]
                    emitter=u32(sp+4);control=u32(0x4db558);frame=s32(control+0x14)
                    if frame<=350:
                        player=u32(0x4db67c)
                        report['bulletFires'].append(dict(stageFrame=frame,returnAddress=hex(u32(sp)),emitter=read(emitter,0x380).hex(),playerBits=[u32(player+0x5e0),u32(player+0x5e4)],exclusionBits=u32(u32(0x4db530)+0x60)))
                    struct.pack_into('<I',context,184,fire_bp);flags=struct.unpack_from('<I',context,192)[0];struct.pack_into('<I',context,192,flags|0x100)
                    write(fire_bp,fire_oldbyte);checked(k.Wow64SetThreadContext(threads[ev.tid],context));pending_step=ev.tid;pending_address=fire_bp
                elif x.code in (0x80000004, 0x4000001e) and pending_step == ev.tid:
                    context = C.create_string_buffer(716)
                    struct.pack_into('<I', context, 0, 0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid], context))
                    flags = struct.unpack_from('<I', context, 192)[0]
                    struct.pack_into('<I', context, 192, flags & ~0x100)
                    checked(k.Wow64SetThreadContext(threads[ev.tid], context))
                    write(pending_address, b'\xcc')
                    if pending_address==BP:armed = True
                    pending_step = None
                elif x.code in (0x80000004, 0x4000001e) and watching_rng:
                    context=C.create_string_buffer(716);struct.pack_into('<I',context,0,0x10017)
                    checked(k.Wow64GetThreadContext(threads[ev.tid],context))
                    sp=struct.unpack_from('<I',context,196)[0]
                    words=struct.unpack('<96I',read(sp,384));ip=struct.unpack_from('<I',context,184)[0]
                    row=dict(thread=ev.tid,ip=hex(ip),stack=[hex(n) for n in words],rngAddress=hex(rng_watch_address),startup=watching_startup,
                        screen=s32(0x4d9648),stage=s32(0x4f58a4),rng=list(struct.unpack('<HHI',read(rng_watch_address,8))))
                    # At next32's seed store the saved EDI is the ANM VM for
                    # the float-reference helpers and bounded integer helper. Read only this known
                    # call chain; other RNG callers do not carry a VM here.
                    if watching_startup and ip==0x403376 and any(w in (0x46f854,0x46f87c,0x46f8a4,0x46fbca) for w in words):
                        vm=words[0];resource=u32(vm+0x30);instruction=u32(vm+0x28);begin=u32(vm+0x38)
                        row['animation']=dict(vm=hex(vm),file=struct.unpack('<H',read(vm+0x36,2))[0],script=struct.unpack('<h',read(vm+0x4aa,2))[0],
                            resourceName=read(resource+4,256).split(b'\0',1)[0].decode('cp932',errors='replace'),
                            instructionOffset=instruction-begin,instruction=read(instruction,32).hex(),timer=s32(vm+0x54c),flags=u32(vm+0x18),flags2=u32(vm+0x1c))
                        parent=u32(vm+0x594)
                        if parent:
                            row['animation']['parent']=dict(vm=hex(parent),file=struct.unpack('<H',read(parent+0x36,2))[0],script=struct.unpack('<h',read(parent+0x4aa,2))[0],instructionOffset=u32(parent+0x28)-u32(parent+0x38))
                        bp=struct.unpack_from('<I',context,180)[0];chain=[]
                        for _ in range(12):
                            if not sp<=bp<sp+0x10000:break
                            previous,ret=struct.unpack('<II',read(bp,8));chain.append(hex(ret))
                            if previous<=bp:break
                            bp=previous
                        row['animation']['frameReturns']=chain
                    report['rngWrites'].append(row)
                    struct.pack_into('<I',context,20,0);checked(k.Wow64SetThreadContext(threads[ev.tid],context))
                elif x.code not in (0x80000003, 0x4000001f):
                    if len(report['events']) < 50:
                        event = dict(code=hex(x.code), address=hex(x.address or 0), firstChance=ev.data.exception.first_chance)
                        if x.code == 0xc0000005 and ev.data.exception.first_chance:
                            ctx = C.create_string_buffer(716)
                            struct.pack_into('<I', ctx, 0, 0x10007)
                            if k.Wow64GetThreadContext(threads[ev.tid], ctx):
                                sp = struct.unpack_from('<I', ctx, 196)[0]
                                event['registers'] = {name: hex(struct.unpack_from('<I', ctx, off)[0]) for name,off in [('eax',176),('ecx',172),('edx',168),('ebx',164),('esi',160),('edi',156),('eip',184)]}
                                event['stack'] = [hex(n) for n in struct.unpack('<32I', read(sp, 128))]
                        report['events'].append(event)
                    status = 0x80010001  # DBG_EXCEPTION_NOT_HANDLED.
            checked(k.ContinueDebugEvent(ev.pid, ev.tid, status))
            if exited: break
        report['capturedFrames'] = len(report['frames'])
        report['selectionChanged'] = selection_changed
        report['timedOut'] = not exited and len(report['frames']) < opt.frames
        if not report['frames']:
            report['startup'] = dict(screen=s32(0x4d9648), pause=s32(0x4f7ac8)) if not exited else {}
            report['startup']['threads'] = []
            if not exited:
                for tid, handle in threads.items():
                    if k.SuspendThread(handle) == 0xffffffff: continue
                    try:
                        ctx = C.create_string_buffer(716)
                        struct.pack_into('<I', ctx, 0, 0x10007)
                        checked(k.Wow64GetThreadContext(handle, ctx))
                        ip, sp = struct.unpack_from('<I', ctx, 184)[0], struct.unpack_from('<I', ctx, 196)[0]
                        chunks = []
                        for offset in range(0, 4096, 128):
                            try: chunks.extend(struct.unpack('<32I', read(sp + offset, 128)))
                            except OSError: break
                        stack = chunks
                        report['startup']['threads'].append(dict(tid=tid, ip=hex(ip), stack=[hex(n) for n in stack[:32]], gameReturnCandidates=[hex(n) for n in stack if 0x400000 <= n < 0x4b0000]))
                    finally: k.ResumeThread(handle)
    except Exception as e:
        report['error'] = str(e)
        raise
    finally:
        if not exited:
            if armed and oldbyte:
                try: write(BP, oldbyte)
                except OSError: pass
            if beam_oldbyte:
                try:write(beam_bp,beam_oldbyte)
                except OSError:pass
            if fire_oldbyte:
                try:write(fire_bp,fire_oldbyte)
                except OSError:pass
            # This handle can refer only to the child created above.
            k.TerminateProcess(pi.process, 0)
            k.WaitForSingleObject(pi.process, 2000)
        k.CloseHandle(pi.thread); k.CloseHandle(pi.process)
        report['elapsedSeconds'] = round(time.monotonic() - start, 3)
        output = ROOT / opt.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"Native reference: {len(report['frames'])} frames; {output}", flush=True)


if __name__ == '__main__': main()
