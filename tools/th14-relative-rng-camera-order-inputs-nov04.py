"""Derive a relative RNG restore order without guessing the original VM identity."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-rng-template-trace-nov04';SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.parent.mkdir(parents=True,exist_ok=True)
 bindings={}
 def raw(path):
  b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
 def rows(path):return [json.loads(line)for line in raw(path).splitlines()]
 n=H/'native';report=json.loads(raw(n/'report.json'));assert report['callbacks']==35000 and not report['debugErrors'] and not report['error']
 source=raw(n/'observer-source.py');assert source==raw(H/'observer.py') and SHA(source)==report['sourceSha256']
 # This frozen handler logs both rows synchronously at the same456133 stop.
 assert b'replay_store_snapshot(pc,tid,b)\n        if pc!=0x456133:return'in source.replace(b'\r\n',b'\n')
 stores=[x for x in rows(n/'replay-rng-store-events.jsonl')if x['stage']==3];assert [x['pc']for x in stores]==[0x45610f,0x456123,0x456129,0x456133]
 assert all(x['readOnly'] and x['workerInstructionStillPending'] and not x['providedToEngine'] and not x['threadSchedulingControlled']for x in stores)
 transition=next(x for x in rows(n/'transition-events.jsonl')if x['stage']==3 and x['pc']==0x456133)
 assert transition['registers']==stores[-1]['registers'] and transition['threadId']==stores[-1]['threadId'] and transition['rngHex']==stores[-1]['rngHex']
 callback=stores[-1]['precedingPlayerCallbacks'];assert callback==30837 and all(x['precedingPlayerCallbacks']==callback for x in stores)
 rng=[struct.unpack('<4I',bytes.fromhex(x['rngHex']))for x in stores]
 # Native order: script.seed/calls at4db508/50c, visual.seed/calls at510/514.
 assert len({x[1]for x in rng})==1 and len({x[3]for x in rng[:3]})==1 and rng[-1][3]==0
 seed=stores[-1]['replaySeedWord'];assert rng[2][0]&65535==rng[3][0]&65535==seed
 assert rng[1][0]==rng[0][0] and rng[2][0]!=rng[1][0]
 pump=next(x for x in rows(n/'resource-ready-events.jsonl')if x['event']=='main-resource-pump' and stores[1]['hostMonotonicNs']<x['hostMonotonicNs']<stores[2]['hostMonotonicNs'])
 assert pump['pc']==stores[1]['mainThreadContextAtWorkerDebugEvent']['registers']['eip']==0x47d720
 assert stores[2]['mainThreadContextAtWorkerDebugEvent']['registers']['eip']==stores[3]['mainThreadContextAtWorkerDebugEvent']['registers']['eip']==0x473c93
 data=raw(n/'selected-state.u32');before=struct.unpack_from('<32I',data,(callback-1)*128);after=struct.unpack_from('<32I',data,callback*128)
 assert before[21]==rng[0][0]&65535 and before[22]==rng[0][1]
 delta=(after[22]-rng[-1][1])&0xffffffff;assert delta==22
 value=seed
 for _ in range(delta):mixed=((value^0x9630)-0x6553)&65535;value=((mixed<<2)|(mixed>>14))&65535
 assert value==after[21]
 times=raw(n/'player-host-monotonic.u64');previous_time,next_time=struct.unpack_from('<2Q',times,(callback-1)*8)
 assert previous_time<pump['hostMonotonicNs']<stores[-1]['hostMonotonicNs']<=transition['hostMonotonicNs']<next_time
 sys.path.insert(0,str(R/'tools'));image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe');assert SHA(image.data)==report['executableSha256']
 assert image.read(0x473c8c,9)==bytes.fromhex('83be50030000007411')
 assert image.read(0x45610f,6)==bytes.fromhex('66a310b54d00') and image.read(0x456123,6)==bytes.fromhex('66a308b54d00') and image.read(0x456129,10)==bytes.fromhex('c70514b54d0000000000')
 copies=rows(n/'scene-camera-copy-events.jsonl');camera_before=next(x for x in copies if x['stage']==2 and x['event']=='scene-camera-copy-before');camera_after=next(x for x in copies if x['stage']==2 and x['event']=='scene-camera-copy-after')
 camera_callback=camera_before['precedingPlayerCallbacks'];assert camera_callback==camera_after['precedingPlayerCallbacks']==14182
 assert camera_before['sourceRightHex']=='000000000000000000000000' and camera_after['copiedRightHex']=='000080bf0000000000000000'
 boundaries=rows(n/'camera-boundary-events.jsonl');frame=[x for x in boundaries if x['precedingPlayerCallbacks']==camera_callback and x['event']=='world-perspective-right-written']
 first=frame[0];assert first['pc']==0x4465a6 and first['rightHex']==camera_after['copiedRightHex'] and camera_after['hostMonotonicNs']<first['hostMonotonicNs']
 assert camera_before['lastMainCameraBoundary']['event']=='controller-camera-published' and camera_after['lastMainCameraBoundary']==camera_before['lastMainCameraBoundary']
 camera_raw=raw(n/'world-camera.raw');values=struct.unpack_from('<73f',camera_raw,(camera_callback-1)*292)
 f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
 up=values[6:9];direction=values[9:12]
 axis=[f32(f32(direction[1]*up[2])-f32(direction[2]*up[1])),f32(f32(direction[2]*up[0])-f32(direction[0]*up[2])),f32(f32(direction[0]*up[1])-f32(direction[1]*up[0]))]
 assert struct.pack('<3f',*axis).hex()!=camera_after['copiedRightHex'] and axis[0]<0 and axis[1:]==[0,0]
 camera_input=dict(stage=2,callback=camera_callback,ordinal=1,point=5,readyNs=camera_after['hostMonotonicNs'],completionSource='original40d447AfterSceneCopyWithRelativeRightReadOrder',representativePointOnly=True,originalExactSourceReadPcObserved=False)
 result=dict(verifiedRelativeRngRestoreOrderInputs=True,native=n.relative_to(R).as_posix(),callbacks=35000,
  inputs=[dict(stage=3,callback=callback,resourcePumpNs=pump['hostMonotonicNs'],readyNs=transition['hostMonotonicNs'],point='firstScriptRngBeforeReadAfterResourcePump')],
  cameraInputs=[camera_input],copiedRightRequiresNormalizedState=True,normalizationCompletionReceiptAfterCopyReceipt=True,
  observedScriptCallsUnchangedThroughRestore=True,observedVisualCallsUnchangedBeforeClear=True,scriptCallsBeforeNextPlayer=delta,
  mainPcAtCounterClear=0x473c93,originalMainVmIdentityObserved=False,exactInstructionScheduleRecovered=False,
  relativeReadOrderOnly=True,hostClockBoundaryReplayRequired=True,nativeRngValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False,
  bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))
 out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))


if __name__=='__main__':main()
