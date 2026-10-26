"""Capture an intact original six-stage replay with explicit environment observations through natural replay end. Observe original HUD initialization write instructions before/after using free worker DR3. with resource-phase readiness observations at every transition.
Hardware breakpoints only; initial publication trace with an explicit configurable cutoff and readonly world-camera bytes at each Player boundary; the one declared warm-case write clears only attract
bit0x40 at the untouched first Player boundary, preserving every other native flag. No
instruction, RNG, serial, counter, health or input writes. Hidden, silent config.
"""
import ctypes as C, hashlib, importlib.util, json, os, shutil, struct, time
from ctypes import wintypes as W
import argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1]
observer_source_bytes=Path(__file__).read_bytes()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--assets',required=True,help='Verified private archive directory from th14-native-campaign-assets.mjs')
parser.add_argument('--output',required=True,help='New output directory under artifacts/th14; existing directories are refused')
parser.add_argument('--config',required=True,help='Original TH14 config bytes, copied and made silent only in the private case')
parser.add_argument('--character',type=int,choices=range(3),required=True)
parser.add_argument('--subtype',type=int,choices=range(2),required=True)
parser.add_argument('--difficulty',type=int,choices=range(4),required=True)
parser.add_argument('--publication-cutoff',type=int,default=1000)
parser.add_argument('--combat-schema',type=int,choices=(2,3),default=2)
parser.add_argument('--max-seconds',type=int,default=7200)
parser.add_argument('--maximum-callbacks',type=int,default=160000)
parser.add_argument('--minimum-free-gib',type=float,default=100)
parser.add_argument('--maximum-capture-gib',type=float,default=2)
parser.add_argument('--scene-camera-events',action='store_true',help='Observe scene camera-copy and main-loop camera publication/perspective boundaries during transitions')
parser.add_argument('--controller-phase-events',action='store_true',help='Observe original loading-flag read at controller priority11; combined camera tracing switches its other breakpoint between update and draw')
parser.add_argument('--worker-rng-events',action='store_true',help='Observe replay seed restoration after the worker sleep and retain the paused main-thread PC')
parser.add_argument('--exit-boundary-events',action='store_true',help='Use a free main-thread hardware breakpoint outside loading/publication windows to observe the original WinMain loop exit')
parser.add_argument('--live-callbacks',help='Comma-separated predeclared VM observation callbacks, including1; maximum32')
parser.add_argument('--camera-write-events',action='store_true',help='Observe actual world-right X stores with a draw-phase main-thread DR2 data breakpoint; diagnostic values are never engine inputs')
parser.add_argument('--game-directory',help='Default: directory of executable in runtimes/th14/target.json')
opt=parser.parse_args()
assert not opt.camera_write_events or (opt.scene_camera_events and opt.controller_phase_events)
assert 1<=opt.publication_cutoff<=opt.maximum_callbacks and opt.max_seconds>0
assert opt.minimum_free_gib>=0 and opt.maximum_capture_gib>0
snapshot_callbacks=tuple(int(value)for value in opt.live_callbacks.split(','))if opt.live_callbacks else(1,26000,30000,36000,38900,60000,90000,120000)
assert 1<=len(snapshot_callbacks)<=32 and snapshot_callbacks==tuple(sorted(set(snapshot_callbacks)))and snapshot_callbacks[0]==1
assert snapshot_callbacks[-1]<=opt.maximum_callbacks
storage_spec=importlib.util.spec_from_file_location('test_storage',root/'tools/th14-test-storage.py')
storage=importlib.util.module_from_spec(storage_spec);storage_spec.loader.exec_module(storage)
original=Path(opt.game_directory) if opt.game_directory else Path(json.loads((root/'runtimes/th14/target.json').read_text())['executable']).parent

spec=importlib.util.spec_from_file_location('native_types',root/'tools/th14-native-session-capture.py')
types=importlib.util.module_from_spec(spec);spec.loader.exec_module(types)
home=(root/opt.output).resolve();assert home.is_relative_to((root/'artifacts/th14').resolve());home.mkdir(exist_ok=False)
(home/'observer-source.py').write_bytes(observer_source_bytes)
(home/'snapshot-plan.json').write_text(json.dumps(dict(callbacks=snapshot_callbacks,observationOnly=True,predeclaredBeforeOriginalProcessLaunch=True),indent=2)+'\n')
work=home/'work';work.mkdir();sha=lambda b:hashlib.sha256(b).hexdigest()
def storage_budget():return storage.check_budget(home,int(opt.minimum_free_gib*1024**3),int(opt.maximum_capture_gib*1024**3))
storage_budget()
asset=(root/opt.assets).resolve()
asset_report=json.loads((asset/'manifest.json').read_text())
assert asset_report['passed']and asset_report['changedEntries']==['demo0.rpy']and asset_report['unchangedEntries']==226
assert asset_report['originalArchiveSha256']=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
assert sha((original/'th14.dat').read_bytes())==asset_report['originalArchiveSha256']
assert sha(Path(asset_report['replayPath']).read_bytes())==asset_report['replaySha256']
manifest=[]
for name in ('th14.exe','th14.dat','thbgm.dat','util.dll'):
    source=asset/name if name=='th14.dat'else original/name
    target=work/name;digest=storage.clone_immutable(source,target)
    if source.parent==original:assert not os.path.samefile(source,target)
    manifest.append(dict(name=name,bytes=target.stat().st_size,sha256=digest))
assert manifest[0]['sha256']==types.EXPECTED_EXE
assert manifest[1]['sha256']==asset_report['referenceArchiveSha256']
appdata=work/'appdata';cfgdir=appdata/'ShanghaiAlice/th14';cfgdir.mkdir(parents=True)
config=bytearray((root/opt.config).read_bytes());assert len(config)>=0x3a
config[0x22]=config[0x23]=0;config[0x39]&=~1;config[0x1f]=3
(cfgdir/'th14.cfg').write_bytes(config)
env={k:v for k,v in os.environ.items()if k.upper()!='APPDATA'};env['APPDATA']=str(appdata)
envblock=C.create_unicode_buffer('\0'.join(f'{k}={v}'for k,v in sorted(env.items(),key=lambda p:p[0].upper()))+'\0\0')
k=C.WinDLL('kernel32',use_last_error=True)
signatures={
 'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
 'WaitForDebugEvent':([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),'ContinueDebugEvent':([W.DWORD,W.DWORD,W.DWORD],W.BOOL),
 'ReadProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
 'WriteProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
 'Wow64GetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),'Wow64SetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
 'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),'CloseHandle':([W.HANDLE],W.BOOL),
}
for name,(args,result)in signatures.items():getattr(k,name).argtypes=args;getattr(k,name).restype=result
def checked(ok):
    if not ok:raise C.WinError(C.get_last_error())
import subprocess
probe=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter \"Name = 'th14.exe'\").Count"],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW);assert probe.returncode==0 and probe.stdout.strip()=='0',probe.stdout+probe.stderr
pi,si=types.ProcessInfo(),types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0
exe=str(work/'th14.exe');checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x400,envblock,str(work),C.byref(si),C.byref(pi)))
combat_module=root/('tools/th14-combat-pool-readonly-v'+str(opt.combat_schema)+'-oct25.py')
combat_spec=importlib.util.spec_from_file_location('combat_pool',combat_module)
combat_pool=importlib.util.module_from_spec(combat_spec);combat_spec.loader.exec_module(combat_pool)
combat_snapshots=[]
latest_camera_boundary=None;camera_boundary_count=0;scene_camera_copies=[];main_camera_phase='update'
camera_right_write_count=0;latest_camera_right_write=None
sleep_pcs={};transition_trace=False;transition_events=[]
pending_worker_rng=set()
targets={0x435b0f:'sleep60-before-call',0x435b11:'sleep60-returned',0x456133:'replay-seeds-restored-before-globals-copy',0x44dbd0:'player-entry',0x47e938:'initial-anm-publication',0x45286f:'beam-uninitialized-scratch-read',0x47d720:'main-resource-pump',0x47d0ec:'cpu-resource-queued',0x4441a8:'signature-ready-flag-published',0x444222:'ascii-ready-flag-published',0x4595e1:'title-worker-signature-retirement',0x459615:'title-ready-flag-published',0x44c4c6:'initial-player-file-returned',0x44d2aa:'initial-player-initialized',0x435e22:'initial-player-options-ready',0x43605a:'initial-control-loading-flag-cleared',0x4360c6:'initial-worker-complete'}
targets.update({0x40dae9:'controller-camera-published',0x4465a6:'world-perspective-right-written',0x40d435:'scene-camera-copy-before',0x40d447:'scene-camera-copy-after',0x436bed:'controller-loading-flag-read'})
serial_watch_manager=0;pending_publications={};allocation_rows=[];serial_write_rows=[];hud_raw=bytearray()
serial_after_to_publish={0x47e90f:(0x47e938,'edi'),0x47e918:(0x47e938,'edi'),0x47e9b8:(0x47e9e1,'esi'),0x47e9c1:(0x47e9e1,'esi'),0x47ea6f:(0x47ea98,'edi'),0x47ea78:(0x47ea98,'edi'),0x47eb18:(0x47eb41,'esi'),0x47eb21:(0x47eb41,'esi')}

targets.update({0x42ec65:'hud-score-initialization-before-write',0x42ec6b:'hud-score-initialization-after-write'})
hud_score_pc={};hud_score_writes=[]
targets[0x44477a]='startup-ascii-create-call-instruction'
targets[0x469c48]='winmain-loop-exit-boundary'
ascii_create_invocations=[]
pcs=list(targets);threads={};handles={pi.process,pi.thread};events=[];debug_errors=[];started=time.monotonic();exited=False;error='';complete=False
process_exit_event=None;observer_termination_requested=False
capture_stop_requested=False;exit_boundary_events=[]
camera_raw=bytearray();live_capture_callbacks=[];thread_events=[];callback_count=0;raw=bytearray();player_times=bytearray();initialization=None;last_stage=0;first_snapshot=None
worker_phase_pcs={};main_resource_frames=0;last_pan=None;last_rectangle=None;last_player_time=started;terminal_menu_samples=[];last_terminal_check=0.
(home/'process-start.json').write_text(json.dumps(dict(pid=pi.pid,exe=exe,onlyOwnCreatedProcess=True,createdUnixNs=time.time_ns()),indent=2)+'\n')
print(json.dumps(dict(nativeChildStarted=True,pid=pi.pid,hidden=True,configuredSilent=True,mode='intact original stages1 through6; declared one attract-mode clear at first Player; no RNG/counter/health writes')),flush=True)
def read(address,count):
    b=C.create_string_buffer(count);got=C.c_size_t();checked(k.ReadProcessMemory(pi.process,address,b,count,C.byref(got)));assert got.value==count;return b.raw
def u32(address):return struct.unpack('<I',read(address,4))[0]
def context(handle):
    b=C.create_string_buffer(716);struct.pack_into('<I',b,0,0x10017);checked(k.Wow64GetThreadContext(handle,b));return b
def install(tid,current=False):
    b=context(threads[tid])
    pending=pending_publications.get(tid)
    trace_publications=first_snapshot is not None and callback_count<opt.publication_cutoff
    addresses=[0x44dbd0,serial_watch_manager+0xff52c8 if trace_publications else sleep_pcs.get(tid,0x435b0f),pending['publishPc']if trace_publications and pending else (0x456133 if tid==pi.tid else sleep_pcs.get(tid,0x435b0f)) if trace_publications else (0x456133 if tid==pi.tid else 0x47d0ec),0x47d720 if tid==pi.tid and transition_trace else 0x47d0ec if tid!=pi.tid and trace_publications else 0]if first_snapshot is not None else[0x44dbd0,serial_watch_manager+0xff52c8 if serial_watch_manager else 0x47e938,pending['publishPc']if pending else 0,0x47d720 if tid==pi.tid else worker_phase_pcs.get(tid,0x47d0ec)]
    if first_snapshot is not None and tid!=pi.tid:addresses[3]=hud_score_pc.get(tid,0x42ec65)
    if first_snapshot is not None and not trace_publications and tid!=pi.tid and tid in pending_worker_rng:addresses[2]=0x456133
    if first_snapshot is not None and not trace_publications and tid==pi.tid and transition_trace and opt.scene_camera_events:
        addresses[1:3]=[0x40dae9,0x4465a6]
    if first_snapshot is not None and not trace_publications and tid==pi.tid and transition_trace and opt.controller_phase_events:
        addresses[2]=0x436bed
        if opt.scene_camera_events:addresses[1]=0x40dae9 if main_camera_phase=='update'else 0x4465a6
    watch_camera_write=first_snapshot is not None and not trace_publications and tid==pi.tid and transition_trace and opt.camera_write_events and main_camera_phase=='draw'
    if watch_camera_write:addresses[2]=0x4d9544
    if first_snapshot is not None and not trace_publications and tid==pi.tid and not transition_trace and opt.exit_boundary_events:
        addresses[3]=0x469c48
    if first_snapshot is None and tid==pi.tid and not ascii_create_invocations:addresses[0]=0x44477a
    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)
    struct.pack_into('<I',b,20,0)
    struct.pack_into('<I',b,24,(sum(1<<(2*i)for i,a in enumerate(addresses)if a)|(0xd00000 if trace_publications else 0)) if first_snapshot is not None else 0x45|(0x10 if pending else 0)|(0xd00000 if serial_watch_manager else 0))
    if watch_camera_write:struct.pack_into('<I',b,24,struct.unpack_from('<I',b,24)[0]|0xd000000)
    if current:struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]|0x10000)
    checked(k.Wow64SetThreadContext(threads[tid],b))
def player_snapshot():
    globals_=struct.unpack('<32I',read(0x4f5828,128));player,control,enemies=[u32(x)for x in (0x4db67c,0x4db558,0x4db544)]
    assert player and control
    p=read(player,0x184c0);pu=lambda offset:struct.unpack_from('<I',p,offset)[0]
    script_seed,_,script_calls,game_seed,_,game_calls=struct.unpack('<HHIHHI',read(0x4db508,16))
    words=[u32(control+0x14),u32(0x4d6a90),u32(0x4d6a9c),*[pu(o)for o in(0x5ec,0x5f0,0x684,0x690,0x6a4,0x6b8,0x182c4,0x1833c,0x184b0)],
           *[globals_[n]for n in(2,6,9,12,15,16,18,19,5)],script_seed,script_calls,game_seed,game_calls,
           u32(enemies+0xd8)if enemies else 0,sum(pu(0x6c8+n*0xd0+0x98)!=0 for n in range(256)),globals_[0],globals_[1],globals_[3],u32(0x4f58a4),pu(0x182d4)]
    assert len(words)==32;return words
def allocation_snapshot(pc,tid,b):
    global serial_watch_manager
    dr6=struct.unpack_from('<I',b,20)[0]
    regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
    if serial_watch_manager and dr6&2:
        assert pc in serial_after_to_publish,hex(pc)
        publish,reg=serial_after_to_publish[pc];serial=u32(serial_watch_manager+0xff52c8)
        pending_publications[tid]=dict(publishPc=publish,vm=regs[reg],serialAtCounterWrite=serial,afterSerialWritePc=pc)
        serial_write_rows.append([pc,serial,tid])
        return
    pending=pending_publications.pop(tid,None)
    if pending:
        assert pc==pending['publishPc'],(hex(pc),pending)
        vm=pending['vm']
    else:
        assert not serial_watch_manager and pc==0x47e938
        vm=regs['edi'];serial_watch_manager=u32(0x4f56cc)
        assert serial_watch_manager
        for other in tuple(threads):
            if other!=tid:install(other)
    blob=read(vm,0x5cc);handle=struct.unpack_from('<I',blob,0x540)[0];slot=struct.unpack_from('<I',blob,0x544)[0]
    if pending:assert handle>>13==pending['serialAtCounterWrite']
    control=u32(0x4db558)
    row=dict(serial=handle>>13,handle=handle,poolSlot=slot,file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0],layer=struct.unpack_from('<I',blob,0x24)[0],hostMonotonicNs=time.monotonic_ns(),idleCounter=u32(0x4f58bc),signatureDraws=u32(u32(0x4db668)+0x60c)if u32(0x4db668)else None,titleState=u32(u32(0x4db6a4)+0x1c)if u32(0x4db6a4)else None,
             pc=pc,threadId=tid,precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),stageFrame=u32(control+0x14)if control else None,rngHex=read(0x4db508,16).hex())
    row['publicationOrdinal']=len(allocation_rows)+1
    assert row['serial']==(row['publicationOrdinal']-1)%0x7ffff+1,(row,len(allocation_rows))
    if row['file']==2 and row['script']==17 and callback_count==0:
        stack_bytes=b'';stack_error=''
        for count in [512,128,32]:
            try:stack_bytes=read(regs['esp'],count);break
            except (OSError,AssertionError)as e:stack_error=repr(e)
        (home/'ascii-first-publication-callsite.json').write_text(json.dumps(dict(actualFunctionEntry=False,actualPublicationBoundary=True,readOnly=True,publication=row,registers=regs,stackHex=stack_bytes.hex(),stackBytes=len(stack_bytes),stackReadError=stack_error),indent=2)+'\n')
    allocation_rows.append(row)
    if len(allocation_rows)%1000==0:storage_budget()
    with(home/'allocation-events.jsonl').open('a',encoding='utf8')as f:f.write(json.dumps(row)+'\n')

def capture_live_animations(label='first-player-live-vms'):
    manager=u32(0x4f56cc);rows=[];seen=set()
    # The two real ordinary/overlay lists at47e5e0/47e6c0. Each +570 node owns
    # [value,next,previous]. Do not infer liveness from retained pool bytes.
    for group,offset in enumerate((0xfe8208,0xfe8210)):
        node=u32(manager+offset)
        while node:
            assert node not in seen and len(seen)<8192
            seen.add(node);vm=u32(node);assert vm+0x570==node
            blob=read(vm,0x5cc)
            def w(offset):return struct.unpack_from('<I',blob,offset)[0]
            rows.append(dict(handle=w(0x540),group=group,file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<H',blob,0x4aa)[0],timerPrevious=w(0x548),timerCurrent=w(0x54c),timerFraction=w(0x550),pendingInterrupt=w(0x4a0),ageCurrent=w(0x560),rawVmHex=blob.hex()))
            node=u32(node+4)
    (home/(label+'.json')).write_text(json.dumps(dict(readOnly=True,hostMonotonicNs=time.monotonic_ns(),mainResourceFrame=main_resource_frames,ordinaryAndOverlayRegistryWalk=True,rows=rows),indent=2)+'\n')

def event_snapshot(pc,tid,b):
    global last_pan,last_rectangle,capture_stop_requested,main_resource_frames,transition_trace
    global latest_camera_boundary,camera_boundary_count,main_camera_phase
    if pc==0x469c48:
        assert opt.exit_boundary_events and tid==pi.tid
        regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
        control=u32(0x4db558)
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),stageFrame=u32(control+0x14)if control else None,registers=regs,stackHex=read(regs['esp'],64).hex(),localResult=u32(regs['esp']+12),quitFlag=u32(0x4f5a20),renderFlags=u32(0x4f7a54),readOnly=True)
        exit_boundary_events.append(row)
        with(home/'exit-boundary-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        return
    if pc==0x436bed:
        assert opt.controller_phase_events and tid==pi.tid
        # The preceding mov436be7 already read the flags. Retain EAX as a
        # diagnostic of races across this instruction, never an engine input.
        assert read(0x436be7,6).hex()=='8b8780000000' and read(pc,2).hex()=='a804'
        control=u32(0x4db558)
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),cachedFlags=struct.unpack_from('<I',b,176)[0],currentFlags=u32(control+0x80),stageFrame=u32(control+0x14),readOnly=True)
        with(home/'controller-phase-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        return
    if pc in (0x40dae9,0x4465a6,0x40d435,0x40d447):
        assert opt.scene_camera_events
        ebx,esi=struct.unpack_from('<I',b,164)[0],struct.unpack_from('<I',b,160)[0]
        if pc==0x4465a6 and esi!=0x4d9514:return
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),readOnly=True,mainPhaseAtObservation=main_camera_phase)
        if pc==0x40d435:
            assert read(pc,5).hex()=='b94b000000'
            row.update(scene=ebx,sourceRightHex=read(0x4d9544,12).hex(),lastMainCameraBoundary=latest_camera_boundary)
            if opt.camera_write_events:
                main=context(threads[pi.tid]);row.update(mainThreadPcAtWorkerEvent=struct.unpack_from('<I',main,184)[0],lastMainCameraRightWrite=latest_camera_right_write)
            hud_score_pc[tid]=0x40d447
            with(home/'scene-camera-copy-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        elif pc==0x40d447:
            assert read(0x40d435,5).hex()=='b94b000000' and read(0x40d445,2).hex()=='f3a5'
            row.update(scene=ebx,copiedBytes=0x12c,copiedRightHex=read(ebx+0x42a4,12).hex(),lastMainCameraBoundary=latest_camera_boundary)
            if opt.camera_write_events:
                main=context(threads[pi.tid]);row.update(mainThreadPcAtWorkerEvent=struct.unpack_from('<I',main,184)[0],lastMainCameraRightWrite=latest_camera_right_write)
            scene_camera_copies.append(row);hud_score_pc[tid]=0x43605a
            with(home/'scene-camera-copy-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        else:
            camera_boundary_count+=1;row.update(ordinal=camera_boundary_count,rightHex=read(0x4d9544,12).hex());latest_camera_boundary=row
            with(home/'camera-boundary-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        return
    if pc in (0x435b0f,0x435b11,0x456133):
        regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
        control=u32(0x4db558)
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),stageFrame=u32(control+0x14)if control else None,rngHex=read(0x4db508,16).hex(),registers=regs,originalInstructionBytes=read(pc,6).hex())
        if opt.worker_rng_events and tid!=pi.tid and pi.tid in threads:
            main=context(threads[pi.tid]);row['mainThreadPcAtWorkerEvent']=struct.unpack_from('<I',main,184)[0]
        if pc==0x435b0f:
            row['requestedMilliseconds']=u32(regs['esp']);assert row['requestedMilliseconds']==60
            assert row['originalInstructionBytes'].startswith('ffd0');sleep_pcs[tid]=0x435b11;transition_trace=True
            if tid!=pi.tid and pi.tid in threads:install(pi.tid)
        elif pc==0x435b11:
            before=next(x for x in reversed(transition_events)if x['event']=='sleep60-before-call'and x['threadId']==tid)
            row['callBoundaryHostMonotonicNs']=before['hostMonotonicNs'];row['observedCallToReturnNanoseconds']=row['hostMonotonicNs']-before['hostMonotonicNs'];row['includesDebuggerPauseAtCallBoundary']=True;row['returnInstructionObservedDirectly']=True;sleep_pcs[tid]=0x435b0f
            if opt.worker_rng_events and tid!=pi.tid:pending_worker_rng.add(tid)
        else:
            row['restoredReplaySeed']=struct.unpack('<H',read(regs['esi']-0x12,2))[0];assert row['originalInstructionBytes'].startswith('f3a5')
            pending_worker_rng.discard(tid)
        transition_events.append(row)
        with(home/'transition-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True);return
    if pc in (0x44c4c6,0x44d2aa,0x435e22,0x43605a,0x4360c6):
        control=u32(0x4db558)
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),mainResourceFrame=main_resource_frames,stage=u32(0x4f58a4),precedingPlayerCallbacks=callback_count,controlFlags=u32(control+0x80)if control else None,rngHex=read(0x4db508,16).hex(),serial=u32(serial_watch_manager+0xff52c8),resourceSlots=[])
        if pc==0x43605a:
            row.update(observedOriginalLoadingFlagClear=True,clearInstructionPc=0x436053,clearInstructionBytes=read(0x436053,7).hex(),readOnly=True)
            assert row['clearInstructionBytes']=='83a380000000fb' and control and not(row['controlFlags']&4)
        if first_snapshot is not None and tid!=pi.tid:
            hud_score_pc[tid]=0x4360c6 if pc==0x43605a else 0x42ec65 if pc==0x4360c6 else hud_score_pc.get(tid,0x42ec65)
        worker_phase_pcs[tid]={0x44c4c6:0x44d2aa,0x44d2aa:0x435e22,0x435e22:0x47d0ec,0x43605a:0x4360c6,0x4360c6:0x47d0ec}[pc]
        with(home/'resource-ready-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        return
    if pc in (0x47d720,0x47d0ec,0x4441a8,0x444222,0x4595e1,0x459615):
        regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
        manager=u32(0x4f56cc);owner=u32(0x4db668)
        if pc==0x47d720:main_resource_frames+=1;main_camera_phase='update'
        row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),mainResourceFrame=main_resource_frames,signatureDraws=u32(owner+0x60c)if owner else None,idleCounter=u32(0x4f58bc),rngHex=read(0x4db508,16).hex(),resourceSlots=[],controlFlags=u32(u32(0x4db558)+0x80)if u32(0x4db558)else None)
        for slot in range(26):
            resource=u32(manager+0xbc7b0c+slot*4)
            if resource:
                blob=read(resource,0x13c)
                row['resourceSlots'].append(dict(file=slot,address=resource,name=blob[4:264].split(b'\0')[0].decode('cp932',errors='replace'),wait=struct.unpack_from('<I',blob,0x128)[0],tailHex=blob[0x120:].hex()))
        if pc==0x47d0ec:
            resource=regs['esi'];row['queuedFile']=u32(resource);assert u32(resource+0x128)==1
            if row['queuedFile']==1:worker_phase_pcs[tid]=0x4441a8
            elif row['queuedFile']==2:worker_phase_pcs[tid]=0x444222
            elif row['queuedFile']==17:worker_phase_pcs[tid]=0x4595e1
            elif row['queuedFile']==9:worker_phase_pcs[tid]=0x44c4c6
            elif row['queuedFile']==6:worker_phase_pcs[tid]=0x43605a
        elif pc in (0x4441a8,0x444222):
            assert owner==regs['edi']
            row['supervisorSignatureState']=u32(owner+0x604);row['supervisorAsciiState']=u32(owner+0x608)
            assert row['supervisorSignatureState'if pc==0x4441a8 else 'supervisorAsciiState']==1
            worker_phase_pcs[tid]=0x47d0ec
        elif pc in (0x4595e1,0x459615):
            title=u32(0x4db6a4);row['titleTickFlags']=u32(u32(title+0xc)+4);row['titleReadyGlobal']=u32(0x4f7ac8)
            if pc==0x4595e1:worker_phase_pcs[tid]=0x459615
            else:
                assert row['titleTickFlags']&2 and row['titleReadyGlobal']==1
                worker_phase_pcs[tid]=0x47d0ec
        with(home/'resource-ready-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
        return
    if pc!=0x45286f:return allocation_snapshot(pc,tid,b)
    regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
    control=u32(0x4db558)
    row=dict(event=targets[pc],pc=pc,threadId=tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,
             stage=u32(0x4f58a4),stageFrame=u32(control+0x14),registers=regs)
    if pc==0x4524df:
        # Candidate slot relation inferred from the independently captured EBP
        # chain. Record its address/value; do not assert it universally matches.
        address=regs['ebp']-148
        row.update(candidateScratchAddress=address,candidateScratchBits=u32(address),inferredSlotRelation=True)
        last_pan=row;return
    address=regs['esp']+0x2c
    row.update(scratchAddress=address,scratchBits=u32(address),actualOriginalSecurityCookie=u32(0x4d0cc0))
    if pc==0x45292e:last_rectangle=row;return
    obj=regs['edi'];target=regs['esi'];area=u32(obj+0xc0)
    row.update(shotAddress=obj,shotHex=read(obj,0xd0).hex(),targetHex=read(target,12).hex(),areaHex=read(area,0xa4).hex(),
        stackHex=read(regs['esp'],160).hex(),rngHex=read(0x4db508,16).hex(),lastObservedPan=last_pan,lastObservedRectangle=last_rectangle,
        interveningOtherStackWritersNotObserved=True)
    capture_stop_requested=True # Diagnostic stop is distinct from a natural replay-end menu.
    events.append(row)
    with(home/'events.jsonl').open('a',encoding='utf-8')as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(dict(beamFallback=True,stage=row['stage'],stageFrame=row['stageFrame'],bits=row['scratchBits'],callbacks=callback_count)),flush=True)

def terminal_menu_sample():
    pause,replay,control=[u32(a)for a in(0x4db678,0x4db688,0x4db558)]
    if not(pause and replay and control):return None
    words=struct.unpack('<2I',read(pause,8));count=u32(pause+0x10c)
    if words!=(2,3) or u32(pause+0x108)!=1 or u32(pause+0x38)!=1 or u32(pause+0x40)!=5 or count!=3:return None
    disabled=[u32(pause+0xc8+4*i)for i in range(count)]
    if disabled!=[3,2,0] or not(u32(control+0x80)&0x10) or u32(replay+0x10)!=1:return None
    return dict(hostMonotonicNs=time.monotonic_ns(),stage=u32(0x4f58a4),pauseWords=list(words),disabledEntries=disabled,
        cursor=u32(pause+0x38),menuCount=5,forcedExit=1,controlFrame=u32(control+0x14),score=u32(0x4f5830),lives=u32(0x4f5864),
        lifeState=u32(u32(0x4db67c)+0x684),callbacks=callback_count,hudPointer=u32(0x4db550),hudDisplayedScoreUnits=u32(u32(0x4db550)+0x140))

try:
    while time.monotonic()-started<opt.max_seconds and callback_count<opt.maximum_callbacks and not complete and not capture_stop_requested and not exited:
        ev=types.DebugEvent()
        if not k.WaitForDebugEvent(C.byref(ev),500):
            code=C.get_last_error()
            if code==121:
                if callback_count>1000 and time.monotonic()-last_player_time>3 and time.monotonic()-last_terminal_check>.25:
                    last_terminal_check=time.monotonic();sample=terminal_menu_sample()
                    if sample:
                        terminal_menu_samples.append(sample)
                        if len(terminal_menu_samples)>=3 and len({r['callbacks']for r in terminal_menu_samples[-3:]})==1:complete=True
                continue
            raise C.WinError(code)
        status=0x10002
        try:
            assert ev.pid==pi.pid
            if ev.kind==3:
                assert ev.data.create_process.base==0x400000;h=ev.data.create_process.thread;handles.update((ev.data.create_process.process,h));threads[ev.tid]=h
                if ev.data.create_process.file:k.CloseHandle(ev.data.create_process.file)
                install(ev.tid);thread_events.append(dict(kind='main',tid=ev.tid))
            elif ev.kind==2:
                h=ev.data.create_thread.thread;handles.add(h)
                if 0x400000<=ev.data.create_thread.start<0x500000:
                    threads[ev.tid]=h;install(ev.tid);thread_events.append(dict(kind='original-code-thread',tid=ev.tid,start=ev.data.create_thread.start))
            elif ev.kind==4:threads.pop(ev.tid,None)
            elif ev.kind==6:
                if ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
            elif ev.kind==5:
                exited=True
                process_exit_event=dict(exitCode=int(ev.data.exit_code),hostMonotonicNs=time.monotonic_ns(),callbacks=callback_count,observerTerminationRequested=False)
            elif ev.kind==1:
                x=ev.data.exception.record
                if x.code in(0x80000004,0x4000001e)and ev.tid in threads:
                    b=context(threads[ev.tid]);pc=struct.unpack_from('<I',b,184)[0]
                    camera_write_hit=opt.camera_write_events and ev.tid==pi.tid and bool(struct.unpack_from('<I',b,20)[0]&4) and struct.unpack_from('<I',b,12)[0]==0x4d9544 and struct.unpack_from('<I',b,24)[0]&0xf000000==0xd000000
                    if pc in targets or camera_write_hit or (serial_watch_manager and struct.unpack_from('<I',b,20)[0]&2) or (ev.tid in pending_publications and pc==pending_publications[ev.tid]['publishPc']):
                        if camera_write_hit:
                            camera_right_write_count+=1
                            row=dict(event='world-camera-right-x-write',pc=pc,threadId=ev.tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),mainPhaseAtObservation=main_camera_phase,watchAddress=0x4d9544,watchBytes=4,hardwareDataWrite=True,readOnly=True,ordinal=camera_right_write_count,rightHex=read(0x4d9544,12).hex())
                            latest_camera_right_write=row
                            with(home/'camera-right-write-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\n')
                        elif pc==0x44477a:
                            row=dict(event=targets[pc],pc=pc,threadId=ev.tid,hostMonotonicNs=time.monotonic_ns(),mainResourceFrame=main_resource_frames,precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),readOnly=True,originalInstructionBytes=read(pc,5).hex(),actualCallInstruction=True,callTarget=0x47ed10)
                            assert row['stage']==0 and callback_count==0 and not ascii_create_invocations
                            assert row['originalInstructionBytes']=='e891a50300'
                            ascii_create_invocations.append(row)
                            (home/'ascii-create-call-events.json').write_text(json.dumps(dict(readOnly=True,actualFunctionEntry=False,actualCallInstruction=True,rows=ascii_create_invocations),indent=2)+'\n')
                        elif pc in (0x42ec65,0x42ec6b):
                            ebx,eax=struct.unpack_from('<I',b,164)[0],struct.unpack_from('<I',b,176)[0]
                            row=dict(event=targets[pc],pc=pc,threadId=ev.tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),hud=ebx,hudDisplayedScoreUnits=u32(ebx+0x140),globalScoreUnits=u32(0x4f5830),eax=eax,originalInstructionBytes=read(pc,10).hex(),readOnly=True)
                            if ev.tid in pending_worker_rng:row['workerRngBoundaryMissingBeforeHud']=True;pending_worker_rng.discard(ev.tid)
                            hud_score_writes.append(row)
                            with(home/'hud-initialization-events.jsonl').open('a',encoding='utf8')as f:f.write(json.dumps(row)+'\n')
                            hud_score_pc[ev.tid]=0x42ec6b if pc==0x42ec65 else 0x40d435 if opt.scene_camera_events else 0x43605a
                        elif pc==0x44dbd0:
                            main_camera_phase='draw'
                            words=player_snapshot();last_player_time=time.monotonic()
                            if first_snapshot is None:
                                assert words[27:31]==[opt.character,opt.subtype,opt.difficulty,1],words[27:31]
                                flags=u32(0x4f58b8);manager=u32(0x4db688);assert flags&0x40 and manager and u32(manager+0x10)==1
                                first_snapshot=dict(hostMonotonicNs=time.monotonic_ns(),mainResourceFrame=main_resource_frames,words=words,attractFlags=flags,replayManagerMode=1,rngHex=read(0x4db508,16).hex(),actualInitialTimeGetTimeInput=u32(0x4d9688),actualOriginalSecurityCookie=u32(0x4d0cc0),anmManagerSerial=u32(u32(0x4f56cc)+0xff52c8))
                                (home/'untouched-first-player.json').write_text(json.dumps(first_snapshot,indent=2)+'\n')
                                before_flags=flags;after_flags=flags&~0x40
                                payload=C.create_string_buffer(struct.pack('<I',after_flags));written=C.c_size_t();checked(k.WriteProcessMemory(pi.process,0x4f58b8,payload,4,C.byref(written)));assert written.value==4
                                initialization=dict(name='declared warm replay case',address=0x4f58b8,beforeFlags=before_flags,afterFlags=after_flags,attractBitClearOnly=True,gameplayRngOrHealthOrInputOrCounterWrites=False)
                                for other in tuple(threads):
                                    if other!=ev.tid:install(other)
                                complete=False
                            hud_pointer=u32(0x4db550);assert hud_pointer;hud_raw.extend(struct.pack('<2I',u32(hud_pointer+0x140),u32(0x4f5830)))
                            camera_raw.extend(read(0x4d9514,0x124));raw.extend(struct.pack('<32I',*words));player_times.extend(struct.pack('<Q',time.monotonic_ns()));callback_count+=1
                            if combat_pool.due(callback_count,words[0]):
                                checkpoint=combat_pool.capture(read,callback_count,words,home/'combat-pools')
                                combat_snapshots.append(checkpoint)
                                (home/'combat-pool-index.json').write_text(json.dumps(dict(readOnly=True,fields=combat_pool.SCHEMA,snapshots=combat_snapshots),indent=2)+'\n')
                            if callback_count in snapshot_callbacks:
                                capture_live_animations('live-vms-callback-'+str(callback_count));live_capture_callbacks.append(callback_count)
                            if transition_trace and 2<=words[30]<=6 and words[0]>0 and not(u32(u32(0x4db558)+0x80)&4):
                                transition_trace=False
                                for other in tuple(threads):
                                    if other!=ev.tid:install(other)
                            if words[30]!=last_stage or callback_count%300==0:
                                storage_budget()
                                progress=dict(callbacks=callback_count,stage=words[30],stageFrame=words[0],elapsedSeconds=time.monotonic()-started,completeGame=False,nativeEquivalent=False)
                                (home/'progress.json').write_text(json.dumps(progress)+'\n');print(json.dumps(progress),flush=True);last_stage=words[30]
                                (home/'selected-state.u32').write_bytes(raw);(home/'player-host-monotonic.u64').write_bytes(player_times);(home/'world-camera.raw').write_bytes(camera_raw);(home/'hud-score.u32').write_bytes(hud_raw)
                            assert words[27:30]==[opt.character,opt.subtype,opt.difficulty],words[27:30]
                        else:event_snapshot(pc,ev.tid,b)
                        install(ev.tid,current=True)
                    else:status=0x80010001;debug_errors.append(dict(code=x.code,pc=pc))
                elif x.code not in(0x80000003,0x4000001f):
                    status=0x80010001;debug_errors.append(dict(code=x.code,address=x.address,firstChance=ev.data.exception.first_chance,callbacks=callback_count,hostMonotonicNs=time.monotonic_ns()))
                    if not ev.data.exception.first_chance:raise RuntimeError('Unexpected second-chance child exception')
        finally:checked(k.ContinueDebugEvent(ev.pid,ev.tid,status))
except BaseException as e:
    import traceback
    error=repr(e);(home/'exception.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
    if not exited:
        observer_termination_requested=True
        k.TerminateProcess(pi.process,0);deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            ev=types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(ev),100):continue
            if ev.kind==6 and ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
            checked(k.ContinueDebugEvent(ev.pid,ev.tid,0x10002))
            if ev.kind==5:
                exited=True
                process_exit_event=dict(exitCode=int(ev.data.exit_code),hostMonotonicNs=time.monotonic_ns(),callbacks=callback_count,observerTerminationRequested=True)
                break
        k.WaitForSingleObject(pi.process,2000)
    for handle in handles:
        if handle:k.CloseHandle(handle)
    (home/'selected-state.u32').write_bytes(raw);(home/'player-host-monotonic.u64').write_bytes(player_times);(home/'world-camera.raw').write_bytes(camera_raw);(home/'hud-score.u32').write_bytes(hud_raw)
    report=dict(privateImmutableStorageCacheUsed=True,originalGameFilesNotHardlinked=True,storageHelperSha256=sha((root/'tools/th14-test-storage.py').read_bytes()),combatPoolSchemaVersion=opt.combat_schema,observerOptions=vars(opt),combatPoolSnapshots=combat_snapshots,combatPoolObserverSha256=sha(combat_module.read_bytes()),diagnosticPrefixOnly=False,asciiBeginObservedAtActualFunctionEntry=False,asciiCreationObservedAtActualCallInstruction=True,asciiCreateCallPc=0x44477a,asciiCreateInvocations=ascii_create_invocations,asciiPublicationCallsiteReadOnly=True,hudInitializationEvents=hud_score_writes,pid=pi.pid,executableSha256=manifest[0]['sha256'],files=manifest,referenceArchiveManifestSha256=sha((asset/'manifest.json').read_bytes()),
        changedArchiveEntries=['demo0.rpy'],unchangedArchiveEntries=226,configHex=config.hex(),events=events,threadEvents=thread_events,
        hardwareBreakpointsOnly=True,instructionBytesPatched=0,gameStateWordWrites=int(initialization is not None),caseInitialization=initialization,
        rngOrCounterWrites=0,inputInjected=False,realOriginalWindowsProcess=True,ordinaryMenuReplayInitialization=False,hiddenWindowRequested=True,
        configuredMusicAndSoundVolumeZero=True,actualAudioPcmMeasured=False,debuggerPausesAffectTiming=True,hostTimeIsOriginalClockInput=False,
        callbacks=callback_count,selectedSha256=sha(raw),selectedBytes=len(raw),playerHostTimesSha256=sha(player_times),observedReplayTerminalMarker=None,replayTerminalMarkerObservationImplemented=False,observedForcedReplayEndMenu=complete,observedColdFirstPlayerBoundary=first_snapshot is not None,derivedSingleStageReplay=False,derivedTwoStageReplay=False,intactOriginalReplay=True,recordedStages=sorted({struct.unpack_from('<I',raw,i+120)[0]for i in range(0,len(raw),128)}),transitionEvents=transition_events,sourceFullReplaySha256=asset_report['replaySha256'],recordedStageHeaderInputAndFpsRetainedExactly=True,anmPublicationTraceEndsAtFirstPlayer=False,anmPublicationTraceCutoffPlayerCallbacks=opt.publication_cutoff,hudScoreStride=8,hudScoreSha256=sha(hud_raw),worldCameraSha256=sha(camera_raw),worldCameraBytes=len(camera_raw),worldCameraStride=0x124,mainResourceFrames=main_resource_frames,allAnmPublications=len(allocation_rows),serialWriteObservations=len(serial_write_rows),allocationEventsSha256=sha((home/'allocation-events.jsonl').read_bytes())if(home/'allocation-events.jsonl').exists()else None,allRecordedSerialsContiguous=len(allocation_rows)<=0x7ffff,serialModulus=0x7ffff,serialSkipsZero=True,allRecordedPublicationOrdinalsContiguous=all(r['publicationOrdinal']==i+1 and r['serial']==i%0x7ffff+1 for i,r in enumerate(allocation_rows)),observedSerialWrapPublicationOrdinals=[r['publicationOrdinal']for r in allocation_rows if r['serial']==1 and r['publicationOrdinal']>1],terminalMenuSamples=terminal_menu_samples,beamFallbackCount=len(events),
        readOnlyLiveAnimationSnapshots=live_capture_callbacks,liveAnimationSnapshotBoundary="before original Player callback",childExited=exited,error=error,debugErrors=debug_errors,elapsedSeconds=time.monotonic()-started,sourceSha256=sha(observer_source_bytes),observerSourceFrozenAtStart=True,controllerPhaseEventsSha256=sha((home/'controller-phase-events.jsonl').read_bytes())if(home/'controller-phase-events.jsonl').exists()else None,sceneCameraCopyEventsSha256=sha((home/'scene-camera-copy-events.jsonl').read_bytes())if(home/'scene-camera-copy-events.jsonl').exists()else None,sceneCameraCopyEvents=len(scene_camera_copies),mainCameraBoundaryEvents=camera_boundary_count,
        nativeTypesSourceSha256=sha((root/'tools/th14-native-session-capture.py').read_bytes()),completeGame=False,nativeEquivalent=False)
    report.update(processExitEvent=process_exit_event,observerTerminationRequested=observer_termination_requested,exitBoundaryEvents=exit_boundary_events,diagnosticStopBeforeBeamFallback=capture_stop_requested,cameraRightWriteEvents=camera_right_write_count,cameraRightWriteEventsSha256=sha((home/'camera-right-write-events.jsonl').read_bytes())if(home/'camera-right-write-events.jsonl').exists()else None)
    (home/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('observedForcedReplayEndMenu','allAnmPublications','beamFallbackCount','callbacks','childExited','error','elapsedSeconds','processExitEvent','observerTerminationRequested')}),flush=True)
if error or not complete:raise SystemExit(1)
