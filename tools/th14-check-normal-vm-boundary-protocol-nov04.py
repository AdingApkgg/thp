"""Exercise failure propagation at actual VM call/return hooks on the new core."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, time
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();home=a.candidate.resolve(strict=True)
    assert home.is_relative_to(R/'artifacts/th14');out=a.output.resolve()if a.output else home/'protocol-controls';assert out.is_relative_to(home);out.mkdir()
    proof_path=home/'observed-inputs.json';proof=json.loads(proof_path.read_bytes());native=R/proof['native']
    spec=importlib.util.spec_from_file_location('vm_input_proof',R/'tools/th14-observed-normal-vm-inputs-nov04.py');verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier);assert verifier.verify(native)==proof
    target=proof['inputs'][0];assert target['callback']>100
    base=R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs';source=base.read_text(encoding='utf8')
    spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);results=[]
    for point in (0,1):
        directory=out/('before-call'if point==0 else'after-return');directory.mkdir();text=source
        old="const root=resolve(import.meta.dirname,'..')";assert text.count(old)==1;text=text.replace(old,"const root="+json.dumps(str(R)))
        marker="const resourceEvents=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x)),phaseInputs=[];";assert text.count(marker)==1
        text=text.replace(marker,f"assert.equal(c.observed_vm_boundary_input({target['stage']},{target['callback']},{target['file']},{target['script']},{target['handle']},{point},baseNow+1000000n),1);\n"+marker)
        marker=' assert.equal(c.menu_tick(updateNow,0),1);';assert text.count(marker)==1
        text=text.replace(marker,""" const protocolOk=c.menu_tick(updateNow,0);
 if(protocolOk!==1){
  assert.equal(c.observed_vm_boundary_state(16,1),1);assert.equal(c.observed_vm_boundary_state(0,0),0);
  const heap=new Uint8Array(c.memory.buffer),ptr=c.error(),end=heap.indexOf(0,ptr);assert(ptr>0&&end>ptr);const error=new TextDecoder().decode(heap.subarray(ptr,end));assert(error.includes('loading at normal VM boundary'));
  write(resolve(out,'protocol.json'),JSON.stringify({expectedClockFailure:true,callback:c.public_replay_observations(),point:POINT,failed:1,delivered:0,error,physicalAudioDevicesOpened:0,completeGame:false,nativeEquivalent:false},null,2)+'\\n');process.exit(0);
 }
""".replace('POINT',str(point)))
        driver=directory/'driver.mjs';driver.write_bytes(text.encode())
        command=['C:/nvm4w/nodejs/node.exe',str(driver),'--native',str(native),'--assets',str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),
            '--build',str(home/'build/typed/observer-build.json'),'--output',str(directory/'model'),'--selection','0,1,1,1','--scheduler-phases','observed','--prefix','35000']
        (directory/'argv.json').write_bytes((json.dumps(command,indent=2)+'\n').encode());start=time.monotonic();guard=None
        with(directory/'run.log').open('wb')as stream:
            child=subprocess.Popen(command,cwd=R,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            while child.poll()is None:
                try:storage.check_budget(directory,100*1024**3,128*1024**2)
                except RuntimeError:guard='storage-budget'
                if time.monotonic()-start>90:guard='wall-budget'
                if guard:child.terminate();child.wait(timeout=30);break
                time.sleep(1)
        row=dict(point=point,exitCode=child.returncode,guardStop=guard,elapsedSeconds=time.monotonic()-start,driverSha256=sha(driver.read_bytes()))
        (directory/'end.json').write_bytes((json.dumps(row,indent=2)+'\n').encode());assert row['exitCode']==0 and guard is None
        report=json.loads((directory/'model/protocol.json').read_bytes());assert report['expectedClockFailure'] and report['failed']==1 and report['delivered']==0 and report['callback']==target['callback']
        assert 'loading at normal VM boundary'in report['error'];results.append(row);print(json.dumps(row),flush=True)
    result=dict(verifiedBeforeCallAndAfterReturnFailurePropagation=True,cases=results,nativeRngOrStateValuesProvidedToEngine=False,physicalAudioDevicesOpened=0,
        coreBuildSha256=sha((home/'build/typed/observer-build.json').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),completeGame=False,nativeEquivalent=False)
    (out/'verified.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())


if __name__=='__main__':main()
