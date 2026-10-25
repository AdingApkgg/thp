"""Independently verify retained full Hard state, camera, HUD and 303-word VMs.

Requires private original-process observations. Publishes only bounded counts,
hash bindings and limitations, never original assets, memory or input bytes.
"""
import array
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/damage-area-snap-oct25'
NATIVE=ROOT/'artifacts/th14/retail-marisab-hard-hud-completion-hardware-oct25'
MODEL=HOME/'ascii-draw-boundary/full-initial-worker-events-retail-marisab-hard-hud-completion-hardware-oct25-cpu-write-bounded-queue'
SHA=lambda b:hashlib.sha256(b).hexdigest()
OFFSETS=[0x534,0x538,0x24,0x1c,0x548,0x54c,0x550,0x55c,0x560,0x564,0x3c,0x40,0x44,0x48,0x4c,0x50,0x54,0x58,0x5c,0x60,0x64,0x68,0x6c,0x78,0x7c,0x88,0x8c,0x3d8,0x3dc,0x80,0x84,*range(0x3b8,0x3d8,4),*range(0x4ac,0x4cc,4)]
INTERP=[(0x9c,3),(0xf4,3),(0x14c,1),(0x17c,3),(0x204,2),(0x2d0,3),(0x328,1),(0x358,1),(0x388,1),(0x248,2),(0x28c,2)]

def vm_words(raw,handles):
    w=lambda off:struct.unpack_from('<I',raw,off)[0]
    h=lambda off:struct.unpack_from('<H',raw,off)[0]
    flags=w(0x18)
    result=[w(0x540),h(0x36),h(0x4aa),w(0x548),w(0x54c),w(0x550),w(0x4a0),w(0x560),flags&1,(flags>>25)&31,*[w(o) for o in OFFSETS],(w(0x28)-w(0x38))&0xffffffff if w(0x28) else 0xffffffff,*[w(o) for o in (0x59c,0x5a0,0x5a4)],(flags>>17)&3,(flags>>5)&15,int(bool(flags&0x2000)),int(bool(flags&0x800)),int(bool(flags&0x1000)),(flags>>21)&3,(flags>>23)&3,flags>>30,int(bool(flags&0x8000)),*[w(o) for o in (0x4cc,0x4d0,0x4d4,0x4d8,0x4dc,0x4e0,0x4e4,0x4e8,0x70,0x74)]]
    assert len(result)==80
    for base,n in INTERP:
        result += [w(base+off) for off in [*range(0,4*n*4,4),*[5*n*4+x for x in (0,4,8,16,20,24)]]]
    assert len(result)==234
    parent=w(0x594);assert not parent or parent in handles
    result += [*[w(o) for o in (0x4ec,0x4f0,0x4f4,0x90,0x94,0x598)],handles[parent] if parent else 0,w(0x558),w(0x56c),*[w(0x3e0+i*4) for i in range(48)]]
    assert len(result)==291
    for i,off in enumerate((0x574,0x578,0x584,0x588)):
        ptr=w(off);address=ptr-(0x570 if i<2 else 0x580)
        assert not ptr or address in handles
        result.append(handles[address] if ptr else 0)
    result += [w(0),w(4),w(8),int(w(12)!=0),w(16),(w(20)-w(0x38))&0xffffffff if w(20) else 0xffffffff,w(0x4a4),w(0x53c)]
    assert len(result)==303
    return result

def main():
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    load=lambda path:json.loads(read(path))
    native=load(NATIVE/'report.json');report=load(MODEL/'report.json')
    assert native['childExited'] and native['error']=='' and native['observedForcedReplayEndMenu']
    assert native['hardwareBreakpointsOnly'] and native['instructionBytesPatched']==0 and native['gameStateWordWrites']==1 and native['rngOrCounterWrites']==0 and not native['inputInjected']
    assert native['caseInitialization']['attractBitClearOnly']
    assert native['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert native['callbacks']==report['callbacks']==119048 and native['recordedStages']==list(range(1,7))
    assert report['sourceReplaySha256']==native['sourceFullReplaySha256']=='74b5e618a893f8d0d675442cf865158007f74d4f305d1e522e71c9fdddad4f28'
    assert report['asciiBeginDeliveryInferredFromFirstPublication'] and report['noNativePublicationValuesProvidedToEngine'] and report['noPerFrameStateOverrides']
    portable=read(MODEL/'selected-state.u32');raw=read(NATIVE/'selected-state.u32')
    assert len(raw)==119048*128 and raw==portable and SHA(raw)==native['selectedSha256']==report['selectedSha256']
    camera=read(NATIVE/'world-camera.raw');offsets=[*range(0,88,4),0x104,0x108,0x10c]
    selected=array.array('I',(struct.unpack_from('<I',camera,frame*0x124+off)[0] for frame in range(119048) for off in offsets))
    assert selected.itemsize==4 and len(camera)==119048*0x124 and selected.tobytes()==read(MODEL/'portable-camera.u32')
    hud=read(NATIVE/'hud-score.u32');assert len(hud)==119048*8 and hud==read(MODEL/'portable-hud.u32')
    snapshots=[]
    for frame in (1,26000,30000,36000,38900,60000,90000):
        observation=load(NATIVE/f'live-vms-callback-{frame}.json');rows=observation['rows'];actual=load(MODEL/f'portable-live-{frame}.json')
        blobs=[bytes.fromhex(row['rawVmHex']) for row in rows]
        handles={struct.unpack_from('<I',raw,0x570)[0]:struct.unpack_from('<I',raw,0x540)[0] for raw in blobs}
        assert len(handles)==len(rows) and [row['handle'] for row in rows]==[row[0] for row in actual]
        assert [vm_words(raw,handles) for raw in blobs]==actual
        snapshots.append(dict(callback=frame,rows=len(rows),selectedWordsPerVm=303,registryOrderEqual=True))
    pubs=[json.loads(row) for row in read(NATIVE/'allocation-events.jsonl').splitlines()]
    pubs=[row for row in pubs if row['precedingPlayerCallbacks']<30000]
    other=load(MODEL/'portable-allocations-initial-through-30000.json')
    assert len(pubs)==len(other)==269922
    assert [(v['handle'],v['file'],v['script']) for v in pubs]==[(v['handle'],v['file'],v['script']) for v in other]
    live=load(MODEL/'live-report.json');assert live['allLiveValuesEqual'] and live['comparedValues']==303
    assert sum(s['rows'] for s in snapshots)==2142
    for name in ['camera-report.json','hud-report.json','allocation-report.json']:load(MODEL/name)
    ascii_publication=next(v for v in pubs if v['precedingPlayerCallbacks']==0 and v['file']==2 and v['script']==17)
    assert report['extraAsciiDrawBeginBoundaryTimestamp']==ascii_publication['hostMonotonicNs']
    gaps=[v for v in report['observedPhaseInputs'] if v.get('queueObservedDirectly') is False]
    assert [(v['stage'],v['phase']) for v in gaps]==[(2,'Hud'),(2,'Scene')]
    assert all(v['completionSource']=='original42ec6bAfterHudInitializationWrite' for v in report['observedPhaseInputs'] if v['phase']=='Hud')
    browser=load(HOME/'marisab-hard-browser/end-first.json');assert browser['naturalReplayEndObserved'] and browser['quietOutput'] and browser['noInputAfterStart']
    read(HOME/'ascii-draw-boundary/compare.mjs');read(HOME/'ascii-draw-boundary/observer.cpp');read(ROOT/'artifacts/th14/capture-retail-marisab-hard-hud-completion-oct25.py')
    result=dict(verifiedFiniteEvidence=True,productionChange=False,productionSourceCommit='6526182b593605e6d29d814cd5d74629d055b9d7',callbacks=119048,selected32Equal=True,camera25Equal=True,hud2Equal=True,vmSnapshots=snapshots,vm303Rows=2142,orderedPublicationsThroughFirst30000=269922,orderedPublicationsEqual=True,startupAsciiTimestampInferredFromPublication=True,hudCompletionTimestampObservedAtOriginal42ec6b=True,resourceQueueGaps=[dict(stage=v['stage'],phase=v['phase']) for v in gaps],oldCoarseHudFourFailuresRetained=True,currentSdlBrowserFirstNaturalEnd=browser,currentSdlFullRunStableDurationNotVerified=True,selected32CumulativeIncludingRepeatedEnvironment=1328478,strict303CumulativeCheckpoints=43,strict303CumulativeRows=11685,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()),remaining='ReimuA19 raw effect worldZ words; GPU one blue-channel difference; full VM/geometry, ordinary all-mode initialization, PCM and persistence. A finite controlled pass is not whole-game1:1.',completeGame=False,nativeEquivalent=False)
    output=ROOT/'docs/porting/th14-hud-completion-verified-oct25.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k] for k in ['verifiedFiniteEvidence','callbacks','vm303Rows','orderedPublicationsThroughFirst30000','resourceQueueGaps']}))

if __name__=='__main__':main()
