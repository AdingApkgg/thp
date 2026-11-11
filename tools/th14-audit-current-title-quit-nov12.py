"""Qualify current ordinary title Quit without accepting the unlike native trigger."""
from pathlib import Path
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/current-title-quit-nov12'
A=H/'run'
N=R/'artifacts/th14/native-natural-title-exit-nov12-v2'
bindings={}
def read(p):
 b=p.read_bytes();bindings[p.relative_to(R).as_posix()]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
report=load(A/'report.json');receipt=load(H/'terminal-receipt.json')
assert receipt['reaped'] and receipt['exitCode']==0 and receipt['pid']==report['pid']
assert report['terminal'] and report['closed'] and report['stage']=='finished'
assert report['exitSaveExecuted'] and report['ordinaryInputOnly'] and report['quiet']
assert not report['exception'] and not report['errors']
assert not report['nativeUiOrSaveEqualityAccepted']
assert all(w['returned'] and not w['error'] for w in report['workers'])
assert all(w['closed'] and w['exitCode']==0 for w in report['physicalWorkers'])
clock=report['processClockResolution'];assert clock['beginCalls']==clock['endCalls']==1 and not clock['active']
platform=load(A/'platform.json')
assert platform['gpuContextClosed'] and not platform['audibleOutput']
assert not any(platform[k] for k in ['stream','window','context','pendingTimers','openFiles'])
assert not any(platform['actualNativeGles']['liveObjects'].values())
build=load(H/'component/build.json')
assert hashlib.sha256(read(H/'component/candidate.wasm')).hexdigest()==build['wasmSha256']==report['wasmSha256']
assert hashlib.sha256(read(H/'component/fixture.cpp')).hexdigest()==build['fixtureSha256']
assert hashlib.sha256(read(A/'run-host.mjs')).hexdigest()==report['driverSha256']
for name,digest in {**build['sourceBindingsByMode']['candidate'],**build['objectBindings']}.items():
 assert hashlib.sha256(read(R/name)).hexdigest()==digest,name
actions=load(A/'actions.json');states=load(A/'states.json')
assert [x['held'] for x in actions]==[2,0,2,0]
assert [x['label'] for x in actions]==['escape-select-Quit','release-first-Escape','escape-confirm-Quit','release-second-Escape']
assert actions[0]['state'][:5]==[0,1,1,2,0] and actions[2]['state'][:5]==[0,1,1,2,9]
assert states[-1]['words'][0]==4 and all(s['words'][8]==0 for s in states)
mirror_path=R/'tools/th-replay-container.py';read(mirror_path)
spec=importlib.util.spec_from_file_location('quit_score_codec',mirror_path)
mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
encoded=read(A/'save/scoreth14.dat')
magic,total,version,flags,packed,unpacked=struct.unpack_from('<6I',encoded)
assert magic==0x31344854 and version==5 and total==len(encoded)==packed+24 and unpacked==149076
plain=mirror.Lzss(mirror.crypt(encoded[24:],0xac,0x35,0x10,packed)).decode(unpacked)
assert plain is not None and len(plain)==unpacked
offset=0
for i in range(8):
 kind,checksum,size=struct.unpack_from('<3I',plain,offset)
 assert (kind,size)==((0x15243,0x5298) if i<7 else (0x15453,0x42c))
 record=plain[offset:offset+size];assert len(record)==size and sum(record[8:])&0xffffffff==checksum
 offset+=size
assert offset==len(plain)
cfg=read(A/'save/th14.cfg');initial=read(N/'initial-config.bin')
assert len(cfg)==92 and struct.unpack_from('<I',cfg)[0]==0x140002 and cfg[0x22:0x24]==b'\0\0'
native=load(N/'report.json');native_ui=load(N/'ui-observed.json');native_receipt=load(N/'terminal-receipt.json')
assert native['reaped'] and native['naturalOsExitObserved'] and native_receipt['reaped']
assert not native_ui['ordinaryTitleQuitObserved'] and native_ui['windowCloseActionIssued']
assert native['quietRuntimeMeasured'] and native['actualZeroMasterSamples']>=2
assert native['quietGateRequiresActualTitleUiObservation']
gate=load(N/'title-observed.json');assert gate['pid']==native['pid'] and gate['actualTitleMainObserved']
native_prepared=load(N/'prepared.json')
assert hashlib.sha256(read(N/'controller-source-used.py')).hexdigest()==native_prepared['toolSha256']==native['toolSha256']
native_cfg=read(N/'work/appdata/ShanghaiAlice/th14/th14.cfg')
native_config_diffs=[i for i,(a,b) in enumerate(zip(native_cfg,cfg)) if a!=b]
failure=R/'artifacts/th14/native-natural-title-exit-nov12'
failed=load(failure/'report.json');failed_receipt=load(failure/'terminal-receipt.json')
assert failed_receipt['reaped'] and failed['observerTerminationRequested'] and not failed['naturalOsExitObserved']
read(failure/'controller-source-used.py');read(failure/'initialization-level-samples.json');read(failure/'master-samples.json')

out=dict(currentSource=build['productionGameSource'],wasmSha256=build['wasmSha256'],
 actualCppOrdinaryTitleQuitPassed=True,gameplayCallbacks=0,hostFrames=report['frames'],
 scoreFileWritten=True,scoreEncodedBytes=len(encoded),scoreDecodedBytes=len(plain),allEightRecordChecksumsValid=True,
 configFileWritten=True,configBytes=len(cfg),configVolumesZero=True,
 changedConfigOffsetsFromInitial=[i for i,(a,b) in enumerate(zip(initial,cfg)) if a!=b],
 allOwnedResourcesRetired=True,audibleOutput=False,productionChanged=False,
 nativeOrdinaryTitleQuitAccepted=False,nativeWindowCloseObserved=True,
 nativeAndCppSameTrigger=False,wholeSaveBytesEqualityAccepted=False,nativeConfigDifferentOffsets=native_config_diffs,
 originalStartupMonitorFalseZeroFailurePreserved=True,completeGame=False,bindings=bindings)
p=H/'qualified.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}))
