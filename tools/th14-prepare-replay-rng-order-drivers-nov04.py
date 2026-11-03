"""Freeze a read-only order driver and an explicitly unaccepted clock candidate."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--callback',type=int,default=30772);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists() and a.callback>0
    base=R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs';raw=base.read_bytes();text=raw.decode()
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
    replace("const root=resolve(import.meta.dirname,'..')","const root="+json.dumps(str(R)))
    marker='assert(entry);assert.equal(c.public_replay_observations(),1);'
    replace(marker,marker+f'\nassert.equal(c.replay_rng_order_install({a.callback},{a.callback}),1);')
    replace('assert(report.allRaw32ByteIdentical);',
        "const rngRows=Array.from({length:c.replay_rng_order_count()},(_,i)=>Array.from({length:18},(_,j)=>c.replay_rng_order_value(i,j)>>>0));\n"+
        "write(resolve(out,'replay-rng-order.json'),JSON.stringify({rows:rngRows,overflow:!!c.replay_rng_order_overflow(),readOnly:true,hostClockOverridesAdded:false,completeGame:false,nativeEquivalent:false},null,2)+'\\n');\n"+
        'assert.equal(c.replay_rng_order_finish(),1);\nassert(report.allRaw32ByteIdentical);')
    control=text;marker="const resourceEvents=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x)),phaseInputs=[];"
    replace(marker,
        'const candidateInit=transition.find(x=>x.stage===3&&x.pc===0x456133);assert(candidateInit);\n'+
        'assert.equal(c.observed_initialization_clock(candidateInit.precedingPlayerCallbacks,baseNow+BigInt(candidateInit.hostMonotonicNs)-playerOrigin),1);\n'+marker)
    text=text.replace('hostClockOverridesAdded:false','hostClockOverridesAdded:true')
    marker="write(resolve(out,'report.json'),"
    replace(marker,
        "report.hostNormalBoundaryMode='proposed';report.normalBoundaryTimestampAssumptionDeclared=true;report.exactOriginalInstructionBoundaryAccepted=false;\n"+
        'report.unacceptedInitializationBoundaryHypothesis={callback:candidateInit.precedingPlayerCallbacks,file:2,script:16,parentFile:2,parentScript:17,workerClockSourcePc:0x456133,originalExactVmIdentityNotProven:true,acceptedOriginalEquivalence:false};\n'+marker)
    out.mkdir();(out/'driver.mjs').write_bytes(control.encode());(out/'hypothesis-driver.mjs').write_bytes(text.encode())
    result=dict(baseDriverSha256=sha(raw),readOnlyDriverSha256=sha(control.encode()),hypothesisDriverSha256=sha(text.encode()),
        preparerSha256=sha(Path(__file__).read_bytes()),observedCallback=a.callback,vmCallbacksWrapped=False,
        candidateChangesOnlyHostClockPlacement=True,exactOriginalInstructionBoundaryAccepted=False,
        nativeRngValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False)
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))


if __name__=='__main__':main()
