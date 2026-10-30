"""Audit the private IAB scheduling control and ordinary short recording export.

UI observations are manually captured screenshots, not automated assertions
about original-game pixels or an entire browser playthrough.
"""
from pathlib import Path
import argparse,hashlib,json,statistics
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
def verify():
    bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    home=ROOT/'artifacts/th14/browser-scheduling-crosshost-oct30'
    report=json.loads(read(home/'result.json'));read(home/'server.mjs');read(home/'result.png');read(home/'game-initial.png')
    assert report['schema']=='th14/browser-scheduling-control/1'and 15000<=report['elapsed']<16000
    for key in ['gameLoaded','wasmLoaded','gpuRequested','audioOpened','completeGame','browserAcceptance']:assert not report[key]
    assert all(row['visible']=='visible'and row['focus']for row in report['states'])and not report['longTasks']
    raf,timer,worker=report['raf'],report['timer'],report['worker'];assert len(raf)==2702 and len(timer)==938 and len(worker)==937
    assert all(a<b for a,b in zip(raf,raf[1:]))and [r['count']for r in worker]==list(range(1,len(worker)+1))
    gaps=[b-a for a,b in zip(raf,raf[1:])];assert 5<statistics.median(gaps)<6 and max(gaps)<30
    ui=ROOT/'artifacts/th14/iab-ordinary-replay-oct30'
    observations=json.loads(read(ui/'ui-actions.json'));assert observations['ordinaryKeyboardAndUiOnly']and not observations['hiddenRuntimeMutation']and not observations['fileUploadUsed']
    assert observations['bytes']==828 and not observations['fullGameCompleted']
    first=read(ui/'before-refresh.rpy');after=read(ui/'after-refresh.rpy')
    assert first==after and len(first)==828 and first[:6]==b't13r\x02\0'
    native=json.loads(read(ui/'native-read.json'));assert native['passed']and native['files']==2
    assert all(row['sha256']==SHA(first)for row in native['rows'])
    assert read(ui/'before-refresh-decoded.bin')==read(ui/'after-refresh-decoded.bin')
    read(ui/'native-read.py');read(ROOT/'tools/th14-replay-native-decode.py')
    assert native['nativeExecutableSha256']==SHA((Path('H:/Games/th/14')/'th14.exe').read_bytes())
    ax=read(ui/'after-refresh.ax.txt').decode();assert 'th14_01.rpy'in ax and '2 个文件'in ax
    for shot in observations['observedSequence']:read(ui/(shot['shot']+'.png'))
    runtime=ROOT/'artifacts/th14/replay-construction-oct30/runtime'
    wasm=read(runtime/'th14-sdl.wasm');assert SHA(wasm)=='da8e1bf5a2ae674df9c6299a2feeacd5029f0148ecf4d6b57e129e03d0be842a'
    return dict(schema='th14/browser-crosshost-and-short-recording/1',
        iabControlElapsedMs=report['elapsed'],iabRafCallbacks=len(raf),iabRafHz=len(raf)*1000/report['elapsed'],
        iabMainTimerHz=len(timer)*1000/report['elapsed'],iabWorkerTimerHz=len(worker)*1000/report['elapsed'],
        iabRafMedianGapMs=statistics.median(gaps),iabLongTasks=0,
        uniqueExternalChromeLowRafCauseProven=False,gameTimingOrBrowserSettingsChanged=False,
        ordinaryFreshReimuBNormalStage1RecordingObserved=True,wholePageReloadAndManagerRediscoveryObserved=True,
        twiceOrdinaryDownloadedReplayBytes=828,allDownloadedBytesEqual=True,replaySha256=SHA(first),
        actualOriginalDecryptDecompressAccepted=True,originalReplayParserOrPlaybackAccepted=False,
        existingOtherReplayOriginReaudited=False,browserRuntimeWasmSha256=SHA(wasm),
        browserRuntimeUsesNewInstancing=False,observedTitleAndDemo60Fps=True,stableAllScenes60FpsAccepted=False,
        uiObservationNotOriginalPixelComparison=True,browserOutputGainZero=True,physicalAudioDeviceAbsenceProven=False,
        fullBrowserSixStageAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'artifacts/th14')or out.is_relative_to(ROOT/'docs/porting')
    result=verify()
    if a.check:assert json.loads(out.read_bytes())==result
    else:out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))
