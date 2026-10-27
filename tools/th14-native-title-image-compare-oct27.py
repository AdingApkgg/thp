"""Strictly compare an actual native backbuffer with one C++ title capture.

Native initial time/cookie are external inputs; no native RNG or pixel is fed
to the engine. This verifier requires matching observed title age and RNG,
keeps all four channels, writes failure details before exiting unsuccessfully.
"""
from pathlib import Path
import argparse,collections,hashlib,json,struct

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True);parser.add_argument('--port',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    native_home=args.native.resolve();port_home=args.port.resolve();output=args.output.resolve()
    assert all(path.is_relative_to(ROOT/'artifacts/th14')for path in (native_home,port_home,output))
    native=json.loads((native_home/'report.json').read_text());port=json.loads((port_home/'report.json').read_text())
    assert native['frameReadbackCompleted']and native['actualPixelsCaptured']and native['childExited']and not native['error']
    assert port['completed']and not port['error']and not port['browserAcceptance']
    ordinal=native['plan']['capturePresentOrdinal'];snapshot=next(row for row in native['rows']if row['kind']=='native-Present-entry'and row['ordinal']==ordinal)
    assert snapshot['supervisorWords']==[4,4]and snapshot['titleState']==1 and snapshot['readBeforeDiagnosticCalls']
    assert len(port['captures'])==1;capture=port['captures'][0];observed=capture['referenceState']
    rng=struct.unpack('<HHIHHI',bytes.fromhex(snapshot['rngHex']))
    assert observed[:3]==[snapshot['originalInitialTicks'],snapshot['originalProcessCookie'],snapshot['idleCounter']]
    assert observed[3:7]==[rng[0],rng[2],rng[3],rng[5]]and observed[7:10]==[0,0,1]
    left=(native_home/native['readback']['file']).read_bytes();right=(port_home/capture['file']).read_bytes()
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    assert len(left)==len(right)==1228800
    assert sha(left)==native['readback']['pixelSha256']and sha(right)==capture['sha256']
    indices=[n for n,(a,b)in enumerate(zip(left,right))if a!=b];pixels=sorted({n//4 for n in indices})
    counts=collections.Counter(n%4 for n in indices)
    report=dict(exactActualNativeBuffer=not indices,nativePresentOrdinal=ordinal,portApplicationFrame=port['frames'],
        titleIdle=snapshot['idleCounter'],externalInitialTimeAndCookieEqual=True,selectedRngWordsEqual=True,
        comparedBytes=len(left),differentBytes=len(indices),differentPixels=len(pixels),differentBytesPerChannel=dict(counts),
        firstDifferences=[dict(x=(n//4)%640,y=n//2560,channel=n%4,native=left[n],port=right[n])for n in indices[:24]],
        differenceBounds=[min(p%640 for p in pixels),min(p//640 for p in pixels),max(p%640 for p in pixels),max(p//640 for p in pixels)]if pixels else None,
        nativePixelSha256=sha(left),portPixelSha256=sha(right),pixelTolerance=0,alphaExcluded=False,
        nativeHasDeclaredDiagnosticAllocationAndContextRedirect=True,originalOrdinaryUiAccepted=False,
        completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        sourceSha256=sha(Path(__file__).read_bytes()))
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    if indices:raise SystemExit(1)

if __name__=='__main__':main()
