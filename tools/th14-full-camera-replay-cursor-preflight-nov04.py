"""Qualify the short original camera/cursor preflight before a full capture."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct,types
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/full-camera-replay-cursor-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()


def verify():
 bindings={}
 def raw(path):
  path=Path(path);data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
 def load(path):return json.loads(raw(path))
 source=raw(H/'prepared/observer.py');prep=load(H/'prepared/prepared.json');assert SHA(source)==prep['observerSha256']
 assert prep['preparerSha256']==SHA(raw(R/'tools/th14-prepare-full-camera-replay-cursor-nov04.py'))
 assert prep['embeddedCursorHelperSha256']==SHA(raw(R/'tools/th14-replay-cursor-readonly-nov04.py'))
 reader=load(H/'native-reader.json');assert reader['verifiedActualNativeReaderBranches'] and reader['terminalMarkerHandlerNotExecuted']
 assert reader['readOnlyHelperSha256']==prep['embeddedCursorHelperSha256'] and reader['toolSha256']==SHA(raw(R/'tools/th14-replay-cursor-native-nov04.py'))
 native=H/'preflight-retry1/native';report=load(native/'report.json');assert report['callbacks']==1200 and not report['error'] and not report['debugErrors']
 assert raw(native/'observer-source.py')==source and report['sourceSha256']==SHA(source)
 assert report['configuredMusicAndSoundVolumeZero'] and report['instructionBytesPatched']==0 and report['rngOrCounterWrites']==0 and report['caseInitialization']['attractBitClearOnly']
 assert report['worldCameraAll75WordsCaptured'] and not report['actualDeclaredInputExhaustionBranchObserved'] and not report['actualAllFfffMarkerBranchObserved']
 camera=raw(native/'world-camera.raw');tail=raw(native/'world-camera-tail.u32');cursors=raw(native/'replay-cursor.u32')
 assert len(camera)==1200*292 and len(tail)==1200*8 and len(cursors)==1200*56
 assert SHA(camera)==report['worldCameraSha256'] and SHA(tail)==report['worldCameraTailSha256'] and SHA(cursors)==report['replayCursorSha256']
 corpus=R/'artifacts/th14/royalflare-coverage-matrix-oct16/inputs';meta=load(corpus/'reimub-normal-source.json');decoded=raw(corpus/'reimub-normal-decoded.bin')
 assert meta['actualNativeCodecVerified'] and meta['decodedSha256']==SHA(decoded)
 assert report['sourceFullReplaySha256']==meta['sha256']==SHA(raw(corpus/'reimub-normal.rpy'))
 offset=0x94;number,seed,frames,payload=struct.unpack_from('<HHII',decoded,offset);assert number==1 and frames==14211
 packed=(seed<<16)|number;data=decoded[offset+0xdc:offset+0xdc+payload]
 for index,row in enumerate(struct.iter_unpack('<14I',cursors),1):
  assert row[0]==31 and row[2:4]==(1,1) and row[7:12]==(index,index,frames,packed,payload)
  assert row[5]==row[4]+0xdc+index*6
  assert row[6]==row[4]+0xdc+frames*6+(index+29)//30
  assert struct.pack('<2I',*row[12:])[:6]==data[index*6:index*6+6]
 model=H/'preflight-retry1/comparison-75-camera/model';full=load(model/'full-camera-report.json')
 assert full['comparedFieldsPerCallback']==75 and full['nativeWordIndices']==list(range(75)) and full['counts']=={} and not full['nativeTrailingWordsNotCaptured']
 combined=b''.join(camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]for i in range(1200))
 assert full['nativeAll75CameraSha256']==SHA(combined) and full['nativeTailSha256']==SHA(tail)
 assert raw(model/'full-camera.u32')==combined[300:] and full['portableSha256']==SHA(combined[300:])
 driver=R/'tools/th14-compare-native-75-camera-nov04.mjs';path=R/'tools/th14-prepare-75-camera-driver-nov04.py';raw(path);spec=importlib.util.spec_from_file_location('camera_driver',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 assert raw(driver)==m.source()
 model_report=load(model/'report.json');assert model_report['comparisonToolSha256']==SHA(raw(driver)) and model_report['allRaw32ByteIdentical'] and not model_report['ordinaryIndependentThreadTimingAcceptance']
 proof=load(H/'preflight-raw-verified.json');assert proof['verifiedFiniteEvidence'] and proof['callbacks']==1200
 for name,item in proof['bindings'].items():
  data_=raw(R/name);assert len(data_)==item['bytes'] and SHA(data_)==item['sha256']
 # Exercise the actual generated install() function. EOF must never steal DR3
 # from the resource pump while transition tracing is active, or run on workers.
 tree=ast.parse(source);install=next(node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name=='install');written=[]
 k=types.SimpleNamespace(Wow64SetThreadContext=lambda handle,buffer:written.append(bytes(buffer))or 1)
 env=dict(struct=struct,confirmed_thread_ended=lambda tid:False,context=lambda handle:bytearray(716),threads={1:1,2:2},pending_publications={},
  first_snapshot={},callback_count=1200,opt=types.SimpleNamespace(publication_cutoff=1000,scene_camera_events=True,controller_phase_events=True,camera_write_events=True,exit_boundary_events=True,stage_object_vm_window_events=True),
  serial_watch_manager=0,sleep_pcs={},pi=types.SimpleNamespace(tid=1),hud_score_pc={},pending_worker_rng=set(),worker_store_pc={},
  transition_trace=False,main_camera_phase='update',stage_object_vm_window_tid=None,camera_pub_pending=False,camera_source_read_tid=None,
  ascii_create_invocations=[{}],worker_phase_pcs={},replay_eof_watch_pc=0x4552cd,k=k)
 exec(compile(ast.Module(body=[install],type_ignores=[]),'<generated-install>','exec'),env)
 env['install'](1,True);assert struct.unpack_from('<I',written[-1],16)[0]==0x4552cd
 env['transition_trace']=True;env['install'](1,True);assert struct.unpack_from('<I',written[-1],16)[0]==0x47d720
 env['transition_trace']=False;env['install'](2,True);assert struct.unpack_from('<I',written[-1],16)[0]not in (0x4552cd,0x45521b)
 env['replay_eof_watch_pc']=0;env['install'](1,True);assert struct.unpack_from('<I',written[-1],16)[0]==0x469c48
 return dict(verifiedFullCameraCursorPreflight=True,callbacks=1200,cameraFields=75,cameraComparedWords=1199*75,cameraWrongWords=0,
  vm303Rows=proof['vm303Rows'],combatCheckpoints=proof['combatCheckpoints'],liveCursorRowsMatchDecodedReplay=1200,
  inputAndFpsPointersMatchNativeRules=True,hardwareSlotRotationCases=4,transitionResourcePumpWatchPreserved=True,
  configuredOriginalSilent=True,originalEofObserved=False,originalWholeReplayAccepted=False,independentSchedulingAccepted=False,
  observerSha256=SHA(source),bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)


if __name__=='__main__':
 output=H/'preflight-verified.json';assert not output.exists();result=verify();output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
