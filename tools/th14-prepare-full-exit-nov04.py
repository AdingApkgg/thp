"""Prepare a bounded current-core six-stage replay, ordinary menu exit and save.

This relinks the exact retained Application objects to expose its production save
entry point. It adds no game-state override and does not operate an app window.
"""
from pathlib import Path
import hashlib,json,subprocess

R=Path(__file__).resolve().parents[1]
K=R/'artifacts/th14/scene-camera-read-job-nov04'
H=K/'ordinary-full-exit';B=H/'build'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
assert not H.exists();B.mkdir(parents=True)
base_raw=(K/'gles-build/build.json').read_bytes();base=json.loads(base_raw)
assert base['wasmSha256']=='b3c57c9451b0c98a5681b42b11a7e769a63f0bd3dc1a0bf063e81683a1808788'
objects=[]
for name,digest in base['newObjects'].items():
    path=K/'gles-build'/name;assert SHA(path.read_bytes())==digest;objects.append(str(path))
for row in base['coreObjects']:
    path=Path(row['path']);assert SHA(path.read_bytes())==row['sha256'];objects.append(str(path))
assert len(base['coreObjects'])==141
for name,row in base['sourceBindings'].items():assert SHA((R/name).read_bytes())==row['sha256']
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert SHA(compiler.read_bytes())==base['compilerSha256']
linkflags=base['linkFlags']+['-Wl,--export=th11_save_scores']
command=[str(compiler),*base['flags'],*linkflags,*objects,'-o',str(B/'application.wasm')]
(B/'link-argv.json').write_text(json.dumps(command,indent=2)+'\n')
run=subprocess.run(command,cwd=R,capture_output=True,timeout=180)
(B/'link.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,run.stderr.decode(errors='replace')[-2000:]
(B/'gl-signatures.json').write_bytes((K/'gles-build/gl-signatures.json').read_bytes())
build=dict(base);build.update(wasmSha256=SHA((B/'application.wasm').read_bytes()),
    linkFlags=linkflags,exports=base['exports']+['th11_save_scores'],
    toolSha256=SHA(Path(__file__).read_bytes()),reusedApplicationObjects=base['newObjects'],
    relinkOnly=True,parentBuild=(K/'gles-build/build.json').relative_to(R).as_posix(),parentBuildSha256=SHA(base_raw),
    scope='Exact retained 141 core and five Application/device objects, relinked only to export production th11_save_scores for normal exit flushing. No new game implementation or state override; no browser acceptance.')
(B/'build.json').write_text(json.dumps(build,indent=2)+'\n')

source=R/'tools/th14-native-application-process-host-oct27.py';raw=source.read_bytes()
assert SHA(raw)=='4b64f9f41a5a44a72be659de0912c5c0ec777778f903c5eec006c1d05817ecd6'
host=raw.decode()
def replace(old,new):
    global host
    assert host.count(old)==1,old
    host=host.replace(old,new)
replace('R=Path(__file__).resolve().parents[1]',"R=Path('H:/code/thp')")
replace("parser.add_argument('--observe-creations'", "parser.add_argument('--flush-on-exit',action='store_true',help='Call the production save ABI after ordinary menu Quit reaches phase4')\nparser.add_argument('--observe-creations'")
replace("  result['applicationTicks']=application_ticks", "  result['exitSaveRequested']=args.flush_on_exit\n  result['exitSaveCompleted']=exit_save_completed\n  result['applicationTicks']=application_ticks")
replace(' frame_index=0;wall_started=', ' exit_save_completed=False\n frame_index=0;wall_started=')
replace(" api['component_audio_close'](store);completed=True;report()", " if args.flush_on_exit:\n  assert state_now()[0]==4,'Normal menu Quit did not reach finished'\n  assert api['th11_save_scores'](store)==1,'Production exit save failed'\n  exit_save_completed=True\n api['component_audio_close'](store);completed=True;report()")
(H/'host.py').write_bytes(host.encode())

scenario=json.loads((R/'runtimes/th12/th12_web/tests/fixtures/th14-native-application-full-replay.json').read_bytes())
scenario['scope']='Current production C++ Application: cold normalized menu selection, intact ReimuB Normal replay through six stages, stable natural end, return to Replay list and Main, ordinary Quit, then normal production score/config save ABI. No stage/seed/health override. Declared platform clocks and async delivery; not original UI or browser acceptance.'
for action in scenario['actions']:
    expected=action.get('expect',{})
    for name,value in [('13',0),('14',1),('15',1)]:
        if name in expected:expected[name]=value
    if '7' in expected:expected['7']=8
for action in scenario['actions'][-2:]:action['expect']['9']=91452576
scenario['actions'] += [
    dict(frames=1,held=1),
    dict(frames=120,until=dict(index=0,equals=0)),
    dict(frames=60,capture='returned-replay-list',expect={'0':0,'3':11,'5':2}),
    dict(frames=1,held=2),
    dict(frames=60,capture='returned-main',expect={'0':0,'3':1,'5':2}),
    dict(frames=1,held=2),dict(frames=2),dict(frames=1,held=2),
    dict(frames=60,until=dict(index=0,equals=4),expect={'0':4}),
]
(H/'scenario.json').write_text(json.dumps(scenario,indent=2)+'\n')
initial=H/'initial-save/replay';initial.mkdir(parents=True)
replay=R/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs/reimub-normal.rpy';replay_raw=replay.read_bytes()
assert SHA(replay_raw)=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
(initial/'th14_01.rpy').write_bytes(replay_raw)
argv=json.loads((K/'application-argv.json').read_bytes())
argv[3]=str(H/'host.py')
for option,value in [('--build',B),('--output',H/'gles'),('--scenario',H/'scenario.json'),('--initial-save',H/'initial-save'),('--maximum-frames',240000),('--maximum-wall-seconds',3600)]:argv[argv.index(option)+1]=str(value)
argv+=['--flush-on-exit']
(H/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
plan=dict(sourceCoreCommit='51fcb47992be0af65777d2ea87e9e409be6cc641',
    parentApplicationBuildSha256=SHA(base_raw),wasmSha256=build['wasmSha256'],
    sourceReplay=str(replay.relative_to(R)),sourceReplaySha256=SHA(replay_raw),
    hostSourceParent=str(source.relative_to(R)),hostSourceParentSha256=SHA(raw),hostSha256=SHA(host.encode()),
    scenarioSha256=SHA((H/'scenario.json').read_bytes()),scenarioUpperBoundFrames=sum(a.get('frames',0)for a in scenario['actions']),
    maximumFrames=240000,maximumWallSeconds=3600,minimumFreeBytes=100*1024**3,maximumOutputBytes=128*1024**2,
    gameStateOverrides=False,productionSourcesModified=False,physicalAudioDevicesOpened=0,browserAcceptance=False,completeGame=False)
(H/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(plan))
