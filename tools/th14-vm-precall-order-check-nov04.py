"""Compare real manager boundaries with the original VM-call ordering component."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();home=a.candidate.resolve(strict=True)
    assert home.is_relative_to(R/'artifacts/th14');out=a.output.resolve()if a.output else home/'precall-order';assert out.is_relative_to(home);out.mkdir()
    native_raw=(home/'native-precall-order.json').read_bytes();native=json.loads(native_raw);assert native['verifiedOriginalPreUpdateInsideVmCall']
    fixture=R/'runtimes/th12/th12_web/tests/cpp/th14-vm-precall-order-fixture-nov04.cpp'
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';builds={}
    for name,path in [('prior',R/'artifacts/th14/normal-vm-boundaries-v2-nov04/build/ordinary/observer-build.json'),('candidate',home/'build/ordinary/observer-build.json')]:
        raw=path.read_bytes();build=json.loads(raw);assert sha(compiler.read_bytes())==build['compilerSha256']
        for row in build['objectBindings']:assert sha(Path(row['path']).read_bytes())==row['sha256']
        target=out/(name+'.wasm');command=[str(compiler),*build['flags'],*build['linkFlags'],str(fixture),*[row['path']for row in build['objectBindings']],'-o',str(target)]
        run=subprocess.run(command,cwd=R,env={**os.environ,'TEMP':str(out),'TMP':str(out)},capture_output=True,timeout=90)
        (out/(name+'.log')).write_bytes(run.stdout+run.stderr);assert run.returncode==0,run.stderr.decode(errors='replace')[-1500:]
        builds[name]=dict(buildPath=path.relative_to(R).as_posix(),buildSha256=sha(raw),wasmSha256=sha(target.read_bytes()))
    driver="""import assert from'node:assert/strict';import{readFileSync as read,writeFileSync as write}from'node:fs';import{WASI}from'node:wasi';import{resolve}from'node:path';
const home=process.argv[2],result={};for(const name of ['prior','candidate']){const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});const{instance}=await WebAssembly.instantiate(read(resolve(home,name+'.wasm')),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports,rows=[];for(const initial of [0,1,0xffffffff])for(const overlay of [0,1]){assert.equal(c.ordering_case(initial,overlay),1);const values=Array.from({length:4},(_,i)=>c.ordering_word(i)>>>0);assert.deepEqual(values,[name==='candidate'?initial:(initial+1)>>>0,(initial+1)>>>0,1,1]);rows.push({initial,overlay,values});}result[name]=rows;}write(resolve(home,'cpp-verified.json'),JSON.stringify({verifiedOriginalAlignedPrecallOrdering:true,priorBeforeCallControlsRejected:6,cases:result,completeGame:false,nativeEquivalent:false},null,2)+'\\n');"""
    (out/'check.mjs').write_bytes(driver.encode());run=subprocess.run(['C:/nvm4w/nodejs/node.exe',str(out/'check.mjs'),str(out)],cwd=R,capture_output=True,timeout=60)
    (out/'check.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,run.stderr.decode(errors='replace')[-2000:]
    result=dict(verifiedOriginalAndCppPrecallOrdering=True,originalCases=3,cppCases=6,priorControlsRejected=6,builds=builds,
        nativeComponentSha256=sha(native_raw),fixtureSha256=sha(fixture.read_bytes()),driverSha256=sha(driver.encode()),
        actualGameManagerExecuted=True,controlledSyntheticInputs=True,completeGame=False,nativeEquivalent=False,toolSha256=sha(Path(__file__).read_bytes()))
    (out/'verified.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)


if __name__=='__main__':main()
