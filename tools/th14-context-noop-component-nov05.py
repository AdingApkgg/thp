"""Execute the complete derived install() with owned context/API boundaries."""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,itertools,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-native-nov05'
source=H/'observer-slots-v2/observer.py';tree=ast.parse(source.read_bytes())
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='install')
code=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec')
out=H/'context-noop-component';assert not out.exists();out.mkdir()
results=[]
for main,current,pending,same in itertools.product([False,True],repeat=4):
    tid=1 if main else 2
    wanted=[0x44dbd0,0x444890,0x47d720,0]if main else[0x44dbd0,0x435b0f,0x47d0ec,0x42ec65]
    b=bytearray(716);struct.pack_into('<I',b,0,0x10017)
    for i,a in enumerate(wanted if same else [0,0,0,0]):struct.pack_into('<I',b,4+4*i,a)
    struct.pack_into('<I',b,20,int(pending));struct.pack_into('<I',b,24,0x15 if main else 0x55)
    struct.pack_into('<I',b,192,0x202);before=bytes(b);calls=[]
    def set_context(handle,data):calls.append(bytes(data));return 1
    env=dict(struct=struct,json=json,home=out,context=lambda handle:bytearray(before),
        confirmed_thread_ended=lambda value:False,threads={tid:77},first_snapshot={},
        callback_count=31064,opt=SimpleNamespace(publication_cutoff=1000,camera_write_events=False,
            scene_camera_events=False,controller_phase_events=False,exit_boundary_events=False,
            stage_object_vm_window_events=False),pending_publications={},pending_worker_rng=set(),
        worker_store_pc={},worker_phase_pcs={},sleep_pcs={},hud_score_pc={},serial_watch_manager=0,
        pi=SimpleNamespace(tid=1),transition_trace=False,stage_object_vm_window_tid=None,
        camera_source_read_tid=None,stage_object_vm_active=None,main_camera_phase='draw',
        camera_pub_pending=False,replay_eof_watch_pc=0,ascii_create_invocations=[],
        startup_title_ready=False,script_rng_access_active=False,
        pending_debug_context_deferrals=[],context_noop_skips=[],observation_clock_ns=lambda:123,
        event_json=lambda row:json.dumps(row),k=SimpleNamespace(Wow64SetThreadContext=set_context),
        C=SimpleNamespace(get_last_error=lambda:5,WinError=lambda err:PermissionError(err,'owned API failure')))
    exec(code,env);env['install'](tid,current=current)
    expected_calls=int(current or (not pending and not same))
    assert len(calls)==expected_calls,(main,current,pending,same,len(calls))
    expected_defer=not current and pending
    assert bool(env['pending_debug_context_deferrals'])==expected_defer
    assert bool(env['context_noop_skips'])==(not current and not pending and same)
    if calls:
        assert list(struct.unpack_from('<4I',calls[0],4))==wanted
        assert struct.unpack_from('<I',calls[0],20)[0]==0
        assert bool(struct.unpack_from('<I',calls[0],192)[0]&0x10000)==current
    results.append(dict(main=main,current=current,pendingHardwareStatus=pending,
        sameDesiredContext=same,writes=len(calls),pendingEventPreserved=expected_defer))
    if expected_calls:
        env['k']=SimpleNamespace(Wow64SetThreadContext=lambda handle,data:0)
        try:env['install'](tid,current=current)
        except PermissionError:pass
        else:raise AssertionError('Non-no-op API failure was ignored')
        failure=json.loads((out/'hardware-context-write-failure.json').read_bytes())
        assert failure['error']==5 and failure['errorNotIgnored']
report=dict(passed=True,fullInstallCases=len(results),allRequiredMigrationsStillWrite=True,
    pendingHardwareEventsStillDeferred=True,unchangedNoncurrentContextSkipsOnly=True,
    otherApiFailuresStillFatal=True,sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    rows=results,originalProcessNotRunByComponent=True,completeGame=False,
    toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='rows'}))
