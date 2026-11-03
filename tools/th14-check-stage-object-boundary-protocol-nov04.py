"""Exercise controlled failures at real detached Stage object VM call and return boundaries."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, time
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();home=a.candidate.resolve(strict=True)
    assert home.is_relative_to(R/'artifacts/th14');out=home/'stage-object-protocol-v2';out.mkdir()
    source=(R/'tools/th14-compare-native-campaign-retained-camera-nov01.mjs').read_text();results=[]
    spec=importlib.util.spec_from_file_location('storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
    for point in(0,1):
        directory=out/('before-call'if point==0 else'after-return');directory.mkdir();text=source
        old="const root=resolve(import.meta.dirname,'..')";assert text.count(old)==1;text=text.replace(old,"const root="+json.dumps(str(R)))
        marker="const resourceEvents=read(resolve(nativeHome,'resource-ready-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x)),phaseInputs=[];"
        assert text.count(marker)==1;text=text.replace(marker,f"assert.equal(c.stage_object_boundary_fail({point}),1);\n"+marker)
        marker=' assert.equal(c.menu_tick(updateNow,0),1);';assert text.count(marker)==1
        text=text.replace(marker,""" const ok=c.menu_tick(updateNow,0);
 if(ok!==1){
  const words=Array.from({length:12},(_,i)=>c.stage_object_boundary_failure_word(i)>>>0);assert.equal(words[0],1);assert(words[1]>100&&words[1]<35000);assert.equal(words[2],POINT);assert.equal(words[3],2);assert.equal(words[4],1);assert.equal(words[7],words[11]);assert.equal(words[8],4);
  const heap=new Uint8Array(c.memory.buffer),ptr=c.error(),end=heap.indexOf(0,ptr);assert(ptr>0&&end>ptr);const error=new TextDecoder().decode(heap.subarray(ptr,end));assert(error.includes('stage object VM'));
  write(resolve(out,'stage-object-protocol.json'),JSON.stringify({controlledFailure:true,words,error,physicalAudioDevicesOpened:0,nativeStateWrites:false,completeGame:false},null,2)+'\\n');process.exit(0);
 }
""".replace('POINT',str(point)))
        driver=directory/'driver.mjs';driver.write_bytes(text.encode())
        command=['C:/nvm4w/nodejs/node.exe',str(driver),'--native',str(R/'artifacts/th14/replay-rng-store-vm-trace-nov04/native'),
            '--assets',str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),'--build',str(home/'stage-object-control-v2/observer-build.json'),
            '--output',str(directory/'model'),'--selection','0,1,1,1','--scheduler-phases','observed','--prefix','35000']
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
        report=json.loads((directory/'model/stage-object-protocol.json').read_bytes());assert report['controlledFailure'];results.append(row);print(json.dumps(row),flush=True)
    result=dict(verifiedRealStageObjectVmFailurePropagation=True,cases=results,toolSha256=sha(Path(__file__).read_bytes()),
        fixtureSha256=sha((R/'runtimes/th12/th12_web/tests/cpp/th14-stage-object-boundary-fixture-nov04.cpp').read_bytes()),
        buildSha256=sha((home/'stage-object-control-v2/observer-build.json').read_bytes()),nativeRngOrStateValuesProvidedToEngine=False,
        physicalAudioDevicesOpened=0,productionIntegrated=False,completeGame=False,nativeEquivalent=False)
    (out/'verified.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())


if __name__=='__main__':main()
