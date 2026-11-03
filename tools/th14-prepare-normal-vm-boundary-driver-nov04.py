"""Generate the reviewed normal-VM readiness adapter without replacing game state."""
from pathlib import Path
import argparse, hashlib, json
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def driver_source():
    text=(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs').read_text(encoding='utf8')
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new)
    replace("'vm-boundary-baseline']);","'vm-boundary-baseline','normal-vm-inputs']);")
    replace("const root=resolve(import.meta.dirname,'..')","const root="+json.dumps(str(R)))
    marker="const resourceEvents=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x)),phaseInputs=[];"
    replace(marker,"""assert(options.has('normal-vm-inputs')&&prefix===35000&&schedulerPhases==='observed');
assert(!['normal-boundary-observation','normal-vm-boundary-observation','vm-boundary-baseline','scene-copy-observation'].some(key=>options.has(key)));
const vmInputPath=resolve(root,options.get('normal-vm-inputs')),vmInputBytes=read(vmInputPath),vmInputProof=JSON.parse(vmInputBytes);
assert(vmInputProof.verifiedObservedNormalVmReturnInputs&&vmInputProof.callbacks===prefix&&!vmInputProof.completeGame&&!vmInputProof.nativeEquivalent);
assert.equal(resolve(root,vmInputProof.native),nativeHome);
assert.equal(vmInputProof.verifierSha256,sha(read(resolve(root,'tools/th14-observed-normal-vm-inputs-nov04.py'))));
for(const[path,binding]of Object.entries(vmInputProof.bindings)){const bytes=read(resolve(root,path));assert.equal(bytes.length,binding.bytes);assert.equal(sha(bytes),binding.sha256);}
for(const input of vmInputProof.inputs){
 assert.equal(input.sourcePc,0x456133);assert.equal(input.mainPc,0x47e660);assert.equal(input.point,1);assert(input.sameStoppedCpuAndRngState);
 assert.equal(c.observed_vm_boundary_input(input.stage,input.callback,input.file,input.script,input.handle,1,baseNow+BigInt(input.readyNs)-playerOrigin),1);
}
"""+marker)
    marker="write(resolve(out,'report.json'),"
    replace(marker,"""report.hostNormalBoundaryMode='observed-vm-return';
report.normalVmInputObservation={path:relative(root,vmInputPath).replaceAll('\\\\','/'),sha256:sha(vmInputBytes),inputs:vmInputProof.inputs};
report.normalVmBoundaryStates=vmInputProof.inputs.map((_,i)=>Array.from({length:17},(_,j)=>c.observed_vm_boundary_state(i,j)>>>0));
report.normalVmBoundaryFailed=c.observed_vm_boundary_state(16,1);
report.vmBoundaryDriverGeneratorSha256=sha(read(resolve(root,'tools/th14-prepare-normal-vm-boundary-driver-nov04.py')));
report.exactOriginalVmReturnIdentityAccepted=false;
assert.equal(report.normalVmBoundaryFailed,0);assert(report.normalVmBoundaryStates.every((state,i)=>state[0]===1&&state[5]===vmInputProof.inputs[i].handle&&state[6]===vmInputProof.inputs[i].file&&state[7]===vmInputProof.inputs[i].script&&state[8]===vmInputProof.inputs[i].callback&&state[15]===1&&state[16]===1));
"""+marker)
    return text.encode()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14') and not out.exists();out.mkdir(parents=True)
    data=driver_source();(out/'driver.mjs').write_bytes(data)
    result=dict(prepared=True,driverSha256=sha(data),generatorSha256=sha(Path(__file__).read_bytes()),
        baseDriverSha256=sha((R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs').read_bytes()),
        nativeRngOrSerialStateOverridden=False,requiresVerifiedNativeInputs=True,completeGame=False,nativeEquivalent=False)
    (out/'prepared.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result))


if __name__=='__main__':main()
