"""Audit two private browser scheduling controls; no UI or game is driven."""
from pathlib import Path
import argparse,hashlib,json,statistics
ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()

def verify(home):
    bindings={};rows=[]
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]={'bytes':len(raw),'sha256':SHA(raw)};return raw
    for name,source in [('result.json','server.mjs'),('animated-result.json','animated-server.mjs')]:
        report=json.loads(read(home/name));read(home/source)
        assert report['schema']=='th14/browser-scheduling-control/1'
        assert 15000<=report['elapsed']<16000
        assert not report['gameLoaded']and not report['wasmLoaded']and not report['audioOpened']
        assert not report['gpuRequested']and not report['completeGame']and not report['browserAcceptance']
        assert all(s['visible']=='visible'and s['focus']for s in report['states'])
        assert len(report['states'])>=15 and not report['longTasks']
        raf,timer,worker=report['raf'],report['timer'],report['worker']
        assert raf and 850<len(timer)<1000 and 850<len(worker)<1000
        assert [row['count']for row in worker]==list(range(1,len(worker)+1))
        gaps=[b-a for a,b in zip(raf,raf[1:])]
        late=[gap for at,gap in zip(raf[1:],gaps)if at-raf[0]>=6000]
        assert late and statistics.median(late)>900
        rows.append(dict(profile='continuous-canvas2d'if report.get('canvas2dAnimation')else'no-canvas',
                         elapsedMs=report['elapsed'],rafCallbacks=len(raf),
                         overallRafHz=len(raf)*1000/report['elapsed'],lateRafMedianGapMs=statistics.median(late),
                         timerCallbacks=len(timer),timerHz=len(timer)*1000/report['elapsed'],
                         workerCallbacks=len(worker),workerHz=len(worker)*1000/report['elapsed'],
                         observedLongTasks=0,allRecordedDocumentVisibleAndFocused=True))
    assert [row['profile']for row in rows]==['no-canvas','continuous-canvas2d']
    return dict(schema='th14/browser-scheduling-controls/1',actualChromeBrowserRuns=2,rows=rows,
                gameLoaded=False,wasmLoaded=False,explicitWebGlOrWebGpuRequested=False,
                physicalAudioDevicesOpened=0,gameTimingOrBrowserSettingsChanged=False,
                uniqueBrowserPolicyOrOsCauseProven=False,stable60FpsAccepted=False,
                browserAcceptance=False,completeGame=False,nativeEquivalent=False,
                scope='No-game controls reproduce ~1Hz late RAF while16ms main and worker timers keep running. Canvas2D can use internal GPU acceleration; no WebGL/WebGPU device was requested. DOM visibility/focus is not an OS occlusion measurement. No claim that all game frame costs are explained.',
                verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/browser-scheduling-control-oct30')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    home=args.home.resolve();output=args.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    result=verify(home)
    if args.check:assert json.loads(output.read_bytes())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(actualChromeBrowserRuns=2,profiles=result['rows'],stable60FpsAccepted=False)))
