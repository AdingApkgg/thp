"""Observe actual retail D3D9 CreateDevice arguments and returns, without input.

Only a newly created, hidden, silent private child is observed. Device-only
mode reads hardware COM boundaries. Optional frame readback redirects its
original render thread into a declared diagnostic allocation, reads the
backbuffer before Present, releases readback resources, then ends the child.
Original instructions, game data, input and RNG are never written. Diagnostic
code, context redirects and extra D3D calls are reported explicitly.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib.util,json,os,struct,subprocess,time,traceback
from ctypes import wintypes as W

ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--maximum-seconds',type=int,default=45)
    parser.add_argument('--capture-present',type=int,default=0,help='Read back one actual backbuffer before this declared Present entry; zero observes device creation only')
    parser.add_argument('--capture-stage-frame',type=int,help='Read before Present when the actual controller reaches this frame; at most3000 Presents')
    parser.add_argument('--capture-stage',type=int,default=3,help='Actual stage for --capture-stage-frame; default is the first automatic demo')
    parser.add_argument('--snapshot-vms',action='store_true',help='Read ordinary/overlay animation registries before target Present diagnostic calls')
    parser.add_argument('--trace-publications',action='store_true',help='Read animation handle publications using the original serial-counter hardware watchpoint')
    parser.add_argument('--trace-resource-pump',action='store_true',help='Read resource slots and startup-ready flags at main resource pump entry')
    parser.add_argument('--trace-startup-ready',action='store_true',help='Read worker queue, signature/ASCII-ready and title-retirement publication boundaries')
    parser.add_argument('--trace-stage-worker',action='store_true',help='Read first stage CPU worker boundaries and option VMs; hardware observations perturb scheduling and do not prescribe port delays')
    parser.add_argument('--trace-ecl-anm',action='store_true',help='Read inline ECL ANM CPU entry, GPU publication and wait exit using the existing worker hardware slot')
    parser.add_argument('--d3d9-header',type=Path,default=Path('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/shared/d3d9.h'))
    args=parser.parse_args();assert 1<=args.maximum_seconds<=120
    stage_capture=args.capture_stage_frame is not None
    assert 1<=args.capture_stage<=7
    if stage_capture:
        assert args.capture_present==0 and 0<=args.capture_stage_frame<=400
        args.capture_present=3000
    assert 0<=args.capture_present<=(3000 if stage_capture else 600)
    assert not args.snapshot_vms or args.capture_present>0
    assert not args.trace_publications or args.capture_present>0
    assert not args.trace_resource_pump or args.capture_present>0
    assert not args.trace_startup_ready or args.capture_present>0
    assert not args.trace_stage_worker or (stage_capture and not args.trace_publications)
    assert not args.trace_ecl_anm or (args.trace_stage_worker and args.trace_startup_ready)
    worker_pcs=(0x435e17,0x435e22,0x435ed0,0x435ee4,0x435efa)
    if args.trace_ecl_anm:worker_pcs+=(0x435f03,0x435f0c,0x435f15,0x435f1e,0x435f27,0x435f30)
    worker_pcs+=(0x435fba,0x435fc3,0x435fcc,0x436049,0x436053,0x436060)
    home=args.output.resolve();assert home.is_relative_to(ROOT/'artifacts/th14')
    home.mkdir(parents=True,exist_ok=False);(home/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    storage=module('device_storage',ROOT/'tools/th14-test-storage.py')
    types=module('device_types',ROOT/'tools/th14-native-session-capture.py')
    budget=lambda:storage.check_budget(home,100*1024**3,128*1024**2)
    plan=dict(maximumSeconds=args.maximum_seconds,maximumComBoundaryEvents=12,
        minimumFreeBytes=100*1024**3,maximumObservationBytes=128*1024**2,
        hardwareEntryPcs=[0x46b110,0x46b1a0],
        hardwareCallGroups=[[0x46b13d,0x46b169,0x46b18a],[0x46b235,0x46b262,0x46b286]],
        hardwareReturnPcRule='observed call PC plus3',
        capturePresentOrdinal=args.capture_present,newDiagnosticCodeAllocated=bool(args.capture_present),
        captureStageTrigger=dict(stage=args.capture_stage,controllerFrame=args.capture_stage_frame)if stage_capture else None,
        captureStageTriggerObserved=False,
        snapshotLiveAnimationsBeforeReadback=args.snapshot_vms,
        traceAnimationPublications=args.trace_publications,maximumPublications=1024,
        traceMainResourcePump=args.trace_resource_pump,maximumResourcePumpEntries=1200,
        traceStartupReadyBoundaries=args.trace_startup_ready,maximumStartupBoundaries=128,
        traceStageWorkerBoundaries=args.trace_stage_worker,maximumStageWorkerBoundaries=len(worker_pcs),
        stageWorkerHardwareObservationPerturbsScheduling=bool(args.trace_stage_worker),
        stageWorkerBoundaryPcs=list(worker_pcs)if args.trace_stage_worker else [],
        traceInlineEclAnm=args.trace_ecl_anm,maximumInlineEclAnmEvents=48,
        inlineEclAnmPcs=[0x422565,0x42257a,0x422599]if args.trace_ecl_anm else [],
        inlineEclAnmObservation='Hardware execute slot3 switches after HUD returns through the remaining stage constructors, then restores at435fba; no instruction or game state writes',
        originalThreadContextRedirectDeclared=bool(args.capture_present),
        extraD3dReadbackCallsDeclared=bool(args.capture_present),gameNeverResumesAfterDiagnosticReadback=bool(args.capture_present),
        originalCodeWrites=0,gameStateWrites=0,inputInjection=False,silent=True,
        browserRun=False,completeGame=False,nativeEquivalent=False)
    (home/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');budget()
    original=Path(json.loads((ROOT/'runtimes/th14/target.json').read_text())['executable']).parent
    work=home/'work';work.mkdir();files=[]
    for name in ('th14.exe','th14.dat','thbgm.dat','util.dll'):
        src,dst=original/name,work/name
        checksum=storage.clone_immutable(src,dst);assert not os.path.samefile(src,dst)
        files.append(dict(name=name,bytes=dst.stat().st_size,sha256=checksum))
    assert files[0]['sha256']==types.EXPECTED_EXE
    assert files[1]['sha256']=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    appdata=work/'appdata';cfgdir=appdata/'ShanghaiAlice/th14';cfgdir.mkdir(parents=True)
    cfg=bytearray.fromhex(json.loads((ROOT/'artifacts/th14/replay-writer-native.json').read_text())['configs'][0]['config'])
    cfg[0x22]=cfg[0x23]=0;cfg[0x39]&=~1;cfg[0x1f]=3
    (cfgdir/'th14.cfg').write_bytes(cfg)
    preflight=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process th14 -ErrorAction SilentlyContinue).Count"],
        capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert preflight.returncode==0 and preflight.stdout.strip()=='0',preflight.stdout+preflight.stderr
    env={k:v for k,v in os.environ.items()if k.upper()!='APPDATA'};env['APPDATA']=str(appdata)
    envblock=C.create_unicode_buffer('\0'.join(f'{k}={v}'for k,v in sorted(env.items(),key=lambda p:p[0].upper()))+'\0\0')
    k=C.WinDLL('kernel32',use_last_error=True)
    signatures={
        'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
        'WaitForDebugEvent':([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),
        'ContinueDebugEvent':([W.DWORD,W.DWORD,W.DWORD],W.BOOL),
        'ReadProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
        'Wow64GetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
        'Wow64SetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),
        'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),
        'CloseHandle':([W.HANDLE],W.BOOL),
        'VirtualAllocEx':([W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,W.DWORD],C.c_void_p),
        'VirtualProtectEx':([W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)],W.BOOL),
        'WriteProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
        'FlushInstructionCache':([W.HANDLE,C.c_void_p,C.c_size_t],W.BOOL),
    }
    for name,(parameters,result)in signatures.items():getattr(k,name).argtypes=parameters;getattr(k,name).restype=result
    def checked(ok):
        if not ok:raise C.WinError(C.get_last_error())
    pi,si=types.ProcessInfo(),types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0
    exe=str(work/'th14.exe')
    checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x400,envblock,str(work),C.byref(si),C.byref(pi)))
    (home/'process-start.json').write_text(json.dumps(dict(pid=pi.pid,exe=exe,onlyOwnCreatedProcess=True),indent=2)+'\n')
    print(json.dumps(dict(pid=pi.pid,silent=True,originalDeviceObservation=True)),flush=True)
    threads={};handles={pi.process,pi.thread};pending={};rows=[];debug_errors=[]
    groups={0x46b110:(0x46b13d,0x46b169,0x46b18a),0x46b1a0:(0x46b235,0x46b262,0x46b286)}
    selected_groups={};all_calls={pc for group in groups.values()for pc in group}
    completed=exited=False;error='';started=time.monotonic()
    device_observed=False;present_pc=0;present_tid=0;present_count=0;device_pointer=0
    readback_program=None;readback_phase='';readback_result={};context_redirects=0
    normalized_input_samples=[];stage_progress=[];title_reference=[]
    serial_manager=0;publication_pending={};publications=[]
    resource_pumps=[]
    startup_phases={};startup_boundaries=[]
    stage_worker_pcs=worker_pcs
    stage_worker_index=0;stage_worker_tid=0;stage_worker_boundaries=[]
    inline_ecl_anm=[]
    serial_after_to_publish={0x47e90f:(0x47e938,'edi'),0x47e918:(0x47e938,'edi'),
        0x47e9b8:(0x47e9e1,'esi'),0x47e9c1:(0x47e9e1,'esi'),
        0x47ea6f:(0x47ea98,'edi'),0x47ea78:(0x47ea98,'edi'),
        0x47eb18:(0x47eb41,'esi'),0x47eb21:(0x47eb41,'esi')}
    def read(address,count):
        data,got=C.create_string_buffer(count),C.c_size_t()
        checked(k.ReadProcessMemory(pi.process,address,data,count,C.byref(got)));assert got.value==count;return data.raw
    def u32(address):return struct.unpack('<I',read(address,4))[0]
    def snapshot_live_animations():
        manager=u32(0x4f56cc);assert manager
        rows=[];seen=set()
        for group,offset in enumerate((0xfe8208,0xfe8210)):
            node=u32(manager+offset)
            while node:
                assert node not in seen and len(seen)<8192
                seen.add(node);vm=u32(node);assert vm+0x570==node
                blob=read(vm,0x5cc)
                def w(at):return struct.unpack_from('<I',blob,at)[0]
                rows.append(dict(handle=w(0x540),group=group,file=struct.unpack_from('<H',blob,0x36)[0],
                    script=struct.unpack_from('<H',blob,0x4aa)[0],timerPrevious=w(0x548),timerCurrent=w(0x54c),
                    timerFraction=w(0x550),pendingInterrupt=w(0x4a0),ageCurrent=w(0x560),rawVmHex=blob.hex()))
                node=u32(node+4)
        (home/'live-vms-before-readback.json').write_text(json.dumps(dict(readOnly=True,
            presentOrdinal=present_count,readBeforeDiagnosticCalls=True,ordinaryAndOverlayRegistryWalk=True,
            hostMonotonicNs=time.monotonic_ns(),rows=rows),indent=2)+'\n')
    def context(tid):
        data=C.create_string_buffer(716);struct.pack_into('<I',data,0,0x10017)
        checked(k.Wow64GetThreadContext(threads[tid],data));return data
    def install(tid,resume=False):
        data=context(tid)
        if present_pc:
            addresses=[present_pc if tid==present_tid else 0,0,0,0]
            if args.trace_publications:
                addresses[1]=serial_manager+0xff52c8 if serial_manager else 0x47e938
                addresses[2]=publication_pending[tid]['publishPc']if tid in publication_pending else 0
            elif args.trace_stage_worker and tid!=present_tid and stage_worker_index<len(stage_worker_pcs):
                if not stage_worker_tid or tid==stage_worker_tid:addresses[1]=stage_worker_pcs[stage_worker_index]
            if args.trace_resource_pump and tid==present_tid:addresses[3]=0x47d720
            elif args.trace_startup_ready and tid!=present_tid:addresses[3]=startup_phases.get(tid,0x47d0ec)
        else:addresses=[*selected_groups[tid],pending[tid]['returnPc']if tid in pending else 0]if tid in selected_groups else[0x46b110,0x46b1a0,0,0]
        for index,address in enumerate(addresses):struct.pack_into('<I',data,4+4*index,address)
        dr7=sum(1<<(2*i)for i,address in enumerate(addresses)if address)
        if present_pc and args.trace_publications and serial_manager:dr7|=0xd00000 # Slot1, write4 bytes.
        struct.pack_into('<I',data,20,0);struct.pack_into('<I',data,24,dr7)
        if resume:struct.pack_into('<I',data,192,struct.unpack_from('<I',data,192)[0]|0x10000)
        checked(k.Wow64SetThreadContext(threads[tid],data))
    def emit(row):
        rows.append(row)
        with (home/'events.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True);budget()
    def record_publication(tid,pc,regs,vm):
        assert len(publications)<1024
        blob=read(vm,0x5cc);word=lambda at:struct.unpack_from('<I',blob,at)[0]
        handle=word(0x540);title=u32(0x4db6a4);signature=u32(0x4db668)
        row=dict(ordinal=len(publications)+1,pc=pc,threadId=tid,precedingPresentEntries=present_count,
            handle=handle,serial=handle>>13,poolSlot=word(0x544),handleSlot=handle&8191,
            file=struct.unpack_from('<H',blob,0x36)[0],script=struct.unpack_from('<h',blob,0x4aa)[0],
            layer=word(0x24),idleCounter=u32(0x4f58bc),signatureDraws=u32(signature+0x60c)if signature else None,
            titleState=u32(title+0x1c)if title else None,rngHex=read(0x4db508,16).hex(),
            hostMonotonicNs=time.monotonic_ns(),readOnly=True)
        assert row['serial']==row['ordinal'],row
        publications.append(row)
        with (home/'animation-publications.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
    def record_resource_pump(tid):
        if stage_capture and not u32(0x4db558):return
        assert len(resource_pumps)<1200
        manager=u32(0x4f56cc);owner=u32(0x4db668);slots=[]
        if manager:
            for file in (range(3,22)if stage_capture else (0,1,2)):
                pointer=u32(manager+0xbc7b0c+file*4)
                if pointer:
                    blob=read(pointer,0x13c)
                    slots.append(dict(file=file,address=pointer,words128Through134=list(struct.unpack_from('<4I',blob,0x128))))
        row=dict(ordinal=len(resource_pumps)+1,threadId=tid,precedingPresentEntries=present_count,
            startupWords604Through60c=list(struct.unpack('<3I',read(owner+0x604,12)))if owner else None,
            slots=slots,hostMonotonicNs=time.monotonic_ns(),readOnly=True)
        resource_pumps.append(row)
        with (home/'resource-pump-entries.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
    def snapshot_option_vms():
        manager=u32(0x4f56cc);options=[];visited=set()
        if manager:
            for group,offset in enumerate((0xfe8208,0xfe8210)):
                node=u32(manager+offset)
                while node:
                    assert node not in visited and len(visited)<8192
                    visited.add(node);vm=u32(node);assert vm+0x570==node
                    blob=read(vm,0x5cc)
                    file=struct.unpack_from('<H',blob,0x36)[0]
                    script=struct.unpack_from('<h',blob,0x4aa)[0]
                    if file==9 and script==10:
                        word=lambda at:struct.unpack_from('<I',blob,at)[0]
                        options.append(dict(handle=word(0x540),file=file,script=script,group=group,
                            ageCurrent=word(0x560),timerCurrent=word(0x54c),rawVmHex=blob.hex()))
                    node=u32(node+4)
        return options
    def record_stage_worker_boundary(tid,pc,regs):
        nonlocal stage_worker_index,stage_worker_tid
        assert stage_worker_index<len(stage_worker_pcs)and pc==stage_worker_pcs[stage_worker_index]
        assert not stage_worker_tid or stage_worker_tid==tid
        stage_worker_tid=tid
        controller=u32(0x4db558);options=snapshot_option_vms()
        row=dict(ordinal=len(stage_worker_boundaries)+1,pc=pc,threadId=tid,
            precedingPresentEntries=present_count,hostMonotonicNs=time.monotonic_ns(),
            controller=controller,controllerFrame=u32(controller+0x14)if controller else None,
            controllerFlags=u32(controller+0x80)if controller else None,
            stage=u32(0x4f58a4),gameFlags=u32(0x4f58b8),player=u32(0x4db67c),
            rngHex=read(0x4db508,16).hex(),optionVms=options,readOnly=True,
            hardwareObservationPerturbsScheduling=True)
        stage_worker_boundaries.append(row);stage_worker_index+=1
        with (home/'stage-worker-boundaries.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
        if args.trace_ecl_anm and pc==0x435f03:
            assert startup_phases.get(tid,0x47d0ec)==0x47d0ec
            startup_phases[tid]=0x422565
        elif args.trace_ecl_anm and pc==0x435fba:
            assert startup_phases[tid]==0x422565 and inline_ecl_anm and len(inline_ecl_anm)%3==0
            startup_phases[tid]=0x47d0ec
    def record_inline_ecl_anm(tid,pc,regs):
        assert tid==stage_worker_tid and len(inline_ecl_anm)<48
        phases={0x422565:('cpu-entry',0x42257a),0x42257a:('gpu-published',0x422599),0x422599:('gpu-wait-exit',0x422565)}
        phase,next_pc=phases[pc];pointer=0 if pc==0x422565 else regs['esi']
        file=u32(regs['esp'])if not pointer else u32(pointer)
        filename_address=u32(regs['esp']+4)if not pointer else regs['edi']
        filename=read(filename_address,128).split(b'\0',1)[0].decode('ascii')
        assert 10<=file<22 and filename.endswith('.anm')
        if pointer:
            previous=inline_ecl_anm[-1]
            assert previous['threadId']==tid and previous['file']==file and previous['filename']==filename
            if pc==0x422599:assert previous['resource']==pointer
        assert len(inline_ecl_anm)%3==list(phases).index(pc)
        row=dict(ordinal=len(inline_ecl_anm)+1,pc=pc,phase=phase,threadId=tid,file=file,
            filename=filename,resource=pointer,cursor128=u32(pointer+0x128)if pointer else None,
            precedingPresentEntries=present_count,hostMonotonicNs=time.monotonic_ns(),
            optionVms=snapshot_option_vms(),rngHex=read(0x4db508,16).hex(),readOnly=True,
            hardwareObservationPerturbsScheduling=True)
        inline_ecl_anm.append(row);startup_phases[tid]=next_pc
        with (home/'inline-ecl-anm.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
    def record_startup_boundary(tid,pc,regs):
        assert len(startup_boundaries)<128
        owner=u32(0x4db668)
        row=dict(ordinal=len(startup_boundaries)+1,pc=pc,threadId=tid,precedingPresentEntries=present_count,
            startupWords604Through60c=list(struct.unpack('<3I',read(owner+0x604,12)))if owner else None,
            hostMonotonicNs=time.monotonic_ns(),readOnly=True)
        if pc==0x47d0ec:
            file=u32(regs['esi']);row['queuedFile']=file
            startup_phases[tid]={1:0x4441a8,2:0x444222,17:0x4595e1}.get(file,0x47d0ec)
        elif pc in (0x4441a8,0x444222):
            assert owner==regs['edi'];startup_phases[tid]=0x47d0ec
        elif pc==0x4595e1:startup_phases[tid]=0x459615
        elif pc==0x459615:startup_phases[tid]=0x47d0ec
        else:raise AssertionError(hex(pc))
        startup_boundaries.append(row)
        with (home/'startup-ready-boundaries.jsonl').open('a')as stream:stream.write(json.dumps(row)+'\n')
    def redirect(tid,entry,stack=None):
        nonlocal context_redirects
        data=context(tid);struct.pack_into('<I',data,184,entry)
        if stack is not None:struct.pack_into('<I',data,196,stack)
        struct.pack_into('<I',data,20,0);struct.pack_into('<I',data,24,0)
        struct.pack_into('<I',data,192,struct.unpack_from('<I',data,192)[0]&~0x10100)
        checked(k.Wow64SetThreadContext(threads[tid],data));context_redirects+=1
    def begin_readback(tid,data):
        nonlocal readback_program,readback_phase
        helper=module('native_frame_program',ROOT/'tools/th14-native-frame-readback-program-oct27.py')
        allocated=k.VirtualAllocEx(pi.process,None,0x2000,0x3000,4);checked(allocated)
        assert allocated<0xffff0000
        readback_program=helper.build(allocated,device_pointer,args.d3d9_header)
        def write_owned(address,blob):
            assert allocated<=address and address+len(blob)<=allocated+0x2000
            count=C.c_size_t();checked(k.WriteProcessMemory(pi.process,address,C.create_string_buffer(blob),len(blob),C.byref(count)))
            assert count.value==len(blob)
        write_owned(allocated,readback_program['code'])
        write_owned(readback_program['data'],readback_program['initialData'])
        previous=W.DWORD();checked(k.VirtualProtectEx(pi.process,allocated,0x1000,0x20,C.byref(previous)))
        checked(k.FlushInstructionCache(pi.process,allocated,len(readback_program['code'])))
        (home/'readback-program.x86').write_bytes(readback_program['code'])
        metadata={key:value for key,value in readback_program.items()if key not in ('code','initialData')}
        metadata.update(helperSha256=hashlib.sha256((ROOT/'tools/th14-native-frame-readback-program-oct27.py').read_bytes()).hexdigest(),
            originalThreadId=tid,devicePointer=device_pointer,privateCodePageReadExecute=True,privateDataPageReadWrite=True,
            originalInstructionsPatched=False,diagnosticAllocationOnly=True)
        (home/'readback-program.json').write_text(json.dumps(metadata,indent=2)+'\n')
        (home/'context-before-readback.bin').write_bytes(data.raw)
        stack=struct.unpack_from('<I',data,196)[0]-0x100
        readback_phase='capture';redirect(tid,readback_program['entry'],stack)
    def finish_capture():
        nonlocal readback_phase,readback_result
        program=readback_program
        statuses=list(struct.unpack('<8I',read(program['status'],32)))
        readback_result=dict(statusesAtCaptureStop=statuses,sourceSurface=u32(program['sourceSlot']),systemSurface=u32(program['systemSlot']))
        assert statuses[:5]==[0]*5,readback_result
        desc=list(struct.unpack('<8I',read(program['description'],32)))
        pitch,pointer=struct.unpack('<iI',read(program['lock'],8));width,height=desc[6:8]
        assert desc[0]in (21,22)and (width,height)==(640,480)and width*4<=pitch<=width*16 and pointer
        pixels=b''.join(read(pointer+y*pitch,width*4)for y in range(height))
        name=f'native-before-present-{args.capture_present:04d}.bgra';(home/name).write_bytes(pixels)
        readback_result.update(surfaceDescription=desc,pitch=pitch,pixelPointer=pointer,pixelBytes=len(pixels),
            pixelSha256=hashlib.sha256(pixels).hexdigest(),file=name,allFourBytesPerPixelPreserved=True,
            originalPresentCompleted=False,readBeforeUnlock=True)
        emit(dict(kind='actual-backbuffer-read',presentOrdinal=present_count,description=desc,pixelBytes=len(pixels),pixelSha256=readback_result['pixelSha256'],readOnlyGpuPixels=True))
        readback_phase='cleanup';redirect(present_tid,program['cleanupEntry'])
    try:
        while time.monotonic()-started<args.maximum_seconds and len(rows)<12 and not completed and not exited:
            ev=types.DebugEvent()
            if not k.WaitForDebugEvent(C.byref(ev),250):
                code=C.get_last_error()
                if code!=121:raise C.WinError(code)
                budget();continue
            status=0x10002
            try:
                assert ev.pid==pi.pid
                if ev.kind==3:
                    assert ev.data.create_process.base==0x400000
                    handle=ev.data.create_process.thread;handles.update((handle,ev.data.create_process.process));threads[ev.tid]=handle
                    if ev.data.create_process.file:k.CloseHandle(ev.data.create_process.file)
                    install(ev.tid)
                elif ev.kind==2:
                    handle=ev.data.create_thread.thread;handles.add(handle)
                    if 0x400000<=ev.data.create_thread.start<0x500000:threads[ev.tid]=handle;install(ev.tid)
                elif ev.kind==4:threads.pop(ev.tid,None)
                elif ev.kind==5:exited=True
                elif ev.kind==6:
                    if ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
                elif ev.kind==1:
                    exception=ev.data.exception.record
                    if exception.code in (0x80000003,0x4000001f)and readback_phase and ev.tid==present_tid and int(exception.address or 0)in (readback_program['captureStop'],readback_program['cleanupStop']):
                        if readback_phase=='capture':
                            assert int(exception.address)==readback_program['captureStop'];finish_capture()
                        else:
                            assert readback_phase=='cleanup'and int(exception.address)==readback_program['cleanupStop']
                            cleanup=list(struct.unpack('<3I',read(readback_program['status']+20,12)))
                            readback_result['cleanupResults']=cleanup;assert cleanup[0]==0
                            emit(dict(kind='readback-resources-cleaned',unlockHresult=cleanup[0],systemReleaseCount=cleanup[1],sourceReleaseCount=cleanup[2]))
                            readback_phase='done';completed=True
                    elif exception.code in (0x80000004,0x4000001e)and ev.tid in threads:
                        data=context(ev.tid);pc=struct.unpack_from('<I',data,184)[0]
                        regs=dict(zip(('edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'),struct.unpack_from('<11I',data,156)))
                        dr6=struct.unpack_from('<I',data,20)[0]
                        if present_pc and args.trace_resource_pump and pc==0x47d720:
                            record_resource_pump(ev.tid);install(ev.tid,True)
                        elif present_pc and args.trace_stage_worker and stage_worker_index<len(stage_worker_pcs)and pc==stage_worker_pcs[stage_worker_index]:
                            record_stage_worker_boundary(ev.tid,pc,regs)
                            for other in tuple(threads):install(other,other==ev.tid)
                        elif present_pc and args.trace_ecl_anm and pc in (0x422565,0x42257a,0x422599):
                            record_inline_ecl_anm(ev.tid,pc,regs);install(ev.tid,True)
                        elif present_pc and args.trace_startup_ready and pc in (0x47d0ec,0x4441a8,0x444222,0x4595e1,0x459615):
                            record_startup_boundary(ev.tid,pc,regs);install(ev.tid,True)
                        elif present_pc and args.trace_publications and serial_manager and dr6&2:
                            assert pc in serial_after_to_publish,hex(pc)
                            publish,register=serial_after_to_publish[pc]
                            publication_pending[ev.tid]=dict(publishPc=publish,vm=regs[register],serial=u32(serial_manager+0xff52c8))
                            install(ev.tid,True)
                        elif present_pc and args.trace_publications and ev.tid in publication_pending and pc==publication_pending[ev.tid]['publishPc']:
                            saved=publication_pending.pop(ev.tid);assert u32(saved['vm']+0x540)>>13==saved['serial']
                            record_publication(ev.tid,pc,regs,saved['vm']);install(ev.tid,True)
                        elif present_pc and args.trace_publications and not serial_manager and pc==0x47e938:
                            serial_manager=u32(0x4f56cc);assert serial_manager
                            record_publication(ev.tid,pc,regs,regs['edi'])
                            for other in tuple(threads):install(other,other==ev.tid)
                        elif present_pc and pc==present_pc:
                            assert ev.tid==present_tid
                            present_count+=1
                            normalized_input_samples.append([present_count,u32(0x4d6a90),u32(0x4d6a9c),u32(0x4d6aa0)])
                            controller=u32(0x4db558)if stage_capture else 0
                            stage_frame=u32(controller+0x14)if controller else None
                            if stage_capture:
                                native_stage=u32(0x4f58a4)
                                if controller and (not stage_progress or native_stage!=stage_progress[-1]['stage']or stage_frame%60==0):
                                    stage_progress.append(dict(presentOrdinal=present_count,stage=native_stage,stageFrame=stage_frame,
                                        supervisorWords=list(struct.unpack('<2I',read(0x4d9648,8))),
                                        selectedGlobalWords=list(struct.unpack('<32I',read(0x4f5828,128))),rngHex=read(0x4db508,16).hex()))
                                title=u32(0x4db6a4)
                                if title and u32(title+0x1c)==1 and u32(0x4f58bc)in(20,232)and len(title_reference)<2:
                                    title_reference.append(dict(presentOrdinal=present_count,idle=u32(0x4f58bc),rngHex=read(0x4db508,16).hex()))
                                if controller and native_stage==args.capture_stage and stage_frame==args.capture_stage_frame:
                                    args.capture_present=present_count;plan['capturePresentOrdinal']=present_count
                                    plan['captureStageTriggerObserved']=True
                            if present_count in (1,args.capture_present):
                                title=u32(0x4db6a4)
                                snapshot=dict(kind='native-Present-entry',ordinal=present_count,pc=pc,tid=ev.tid,
                                    stage=u32(0x4f58a4),gameFlags=u32(0x4f58b8),idleCounter=u32(0x4f58bc),
                                    stageFrame=stage_frame,controllerPointer=controller,
                                    selectedGlobalWords=list(struct.unpack('<32I',read(0x4f5828,128)))if stage_capture else None,
                                    originalInitialTicks=u32(0x4d9688),originalProcessCookie=u32(0x4d0cc0),
                                    supervisorWords=list(struct.unpack('<2I',read(0x4d9648,8))),
                                    rngHex=read(0x4db508,16).hex(),titlePointer=title,
                                    titleState=u32(title+0x1c)if title else None,readBeforeDiagnosticCalls=True)
                                emit(snapshot)
                            if present_count==args.capture_present:
                                assert not stage_capture or plan['captureStageTriggerObserved'],'Declared controller frame was not reached before the Present budget'
                                assert not args.trace_stage_worker or stage_worker_index==len(stage_worker_pcs),'Declared stage CPU worker boundaries were not all observed'
                                if args.snapshot_vms:snapshot_live_animations()
                                begin_readback(ev.tid,data)
                            else:install(ev.tid,True)
                        elif pc in groups:
                            selected_groups[ev.tid]=groups[pc]
                            emit(dict(kind='device-function-entry',pc=pc,tid=ev.tid,selectedCallPcs=list(groups[pc]),readOnly=True))
                            install(ev.tid,True)
                        elif pc in all_calls:
                            assert ev.tid not in pending
                            args_=list(struct.unpack('<7I',read(regs['esp'],28)))
                            assert args_[1]==0 and args_[2]in (1,2)and args_[4]in (0x20,0x40)and args_[6]==0x4d8f68
                            assert read(pc,3)in (bytes.fromhex('ff5240'),bytes.fromhex('ff5140'))
                            row=dict(kind='before-CreateDevice',pc=pc,tid=ev.tid,arguments=args_,
                                presentationParameters=list(struct.unpack('<14I',read(args_[5],56))),
                                actualComTarget=u32(u32(args_[0])+0x40),originalInstructionHex=read(pc,3).hex(),
                                hostMonotonicNs=time.monotonic_ns(),readOnly=True)
                            pending[ev.tid]=dict(returnPc=pc+3,parameters=args_[5],outDevice=args_[6],before=row)
                            emit(row);install(ev.tid,True)
                        elif ev.tid in pending and pc==pending[ev.tid]['returnPc']:
                            saved=pending.pop(ev.tid);device=u32(saved['outDevice'])
                            row=dict(kind='after-CreateDevice',pc=pc,tid=ev.tid,hresult=regs['eax'],device=device,
                                presentationParameters=list(struct.unpack('<14I',read(saved['parameters'],56))),
                                beforeCallPc=saved['before']['pc'],hostMonotonicNs=time.monotonic_ns(),readOnly=True)
                            if device:row['deviceVtable']=u32(device)
                            emit(row);device_observed=regs['eax']==0 and device!=0
                            if device_observed and args.capture_present:
                                device_pointer=device;present_tid=ev.tid;present_pc=u32(u32(device)+17*4)
                                for other in tuple(threads):
                                    if other!=ev.tid:install(other)
                            else:completed=device_observed
                            install(ev.tid,True)
                        else:status=0x80010001
                    elif exception.code not in (0x80000003,0x4000001f):
                        debug_errors.append(dict(code=exception.code,address=exception.address));status=0x80010001
            finally:checked(k.ContinueDebugEvent(ev.pid,ev.tid,status))
    except BaseException as exc:
        error=repr(exc);(home/'exception.txt').write_text(traceback.format_exc(),encoding='utf8')
    finally:
        if not exited:
            k.TerminateProcess(pi.process,0);deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                ev=types.DebugEvent()
                if not k.WaitForDebugEvent(C.byref(ev),100):continue
                if ev.kind==6 and ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
                checked(k.ContinueDebugEvent(ev.pid,ev.tid,0x10002))
                if ev.kind==5:exited=True;break
            k.WaitForSingleObject(pi.process,2000)
        for handle in handles:
            if handle:k.CloseHandle(handle)
        report=dict(plan=plan,completedDeviceCreationObservation=device_observed,error=error,debugErrors=debug_errors,
            rows=rows,childExited=exited,pid=pi.pid,files=files,configHex=cfg.hex(),
            sourceSha256=hashlib.sha256((home/'run-tool.py').read_bytes()).hexdigest(),
            originalCodeWrites=0,gameStateWrites=0,inputInjection=False,
            actualSurfaceDescriptorQueried=bool(readback_result.get('surfaceDescription')),
            actualPixelsCaptured=bool(readback_result.get('pixelBytes')),frameReadbackCompleted=bool(args.capture_present and completed),
            readback=readback_result,presentEntriesObserved=present_count,threadContextRedirects=context_redirects,
            normalizedInputSamplesAtPresent=normalized_input_samples,
            normalizedInputAddresses=dict(held=0x4d6a90,pressed=0x4d6a9c,released=0x4d6aa0),
            animationPublications=publications,animationPublicationCounterHardwareWatch=bool(serial_manager),
            mainResourcePumpEntries=resource_pumps,
            startupReadyBoundaries=startup_boundaries,
            stageWorkerBoundaries=stage_worker_boundaries,
            stageWorkerBoundariesComplete=bool(args.trace_stage_worker and stage_worker_index==len(stage_worker_pcs)),
            inlineEclAnmBoundaries=inline_ecl_anm,
            inlineEclAnmBoundariesComplete=bool(args.trace_ecl_anm and inline_ecl_anm and len(inline_ecl_anm)%3==0 and stage_worker_index==len(stage_worker_pcs)),
            nativeStageProgress=stage_progress,nativeTitleReference=title_reference,
            normalizedInputWords='ordinal,held,pressed,released; observed at Present only, not physical input events',
            diagnosticPrivateCodeAllocated=readback_program is not None,gameNeverResumedAfterReadback=bool(readback_program),
            configuredMusicAndSoundVolumeZero=True,
            elapsedSeconds=time.monotonic()-started,completeGame=False,nativeEquivalent=False)
        (home/'report.json').write_text(json.dumps(report,indent=2)+'\n');budget()
        print(json.dumps(dict(completed=completed,error=error,events=len(rows))),flush=True)
    if error or not completed:raise SystemExit(1)

if __name__=='__main__':main()
