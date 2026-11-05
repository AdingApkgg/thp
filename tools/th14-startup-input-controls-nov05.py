"""Private startup time/cookie controls over an unchanged frozen TH14 model.

This is a diagnostic sensitivity experiment, not a relaxed acceptance driver.
Only the existing public host time and cookie inputs vary. Raw private input
values and generated drivers are not publication artifacts.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,struct,subprocess,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/original-pair-audit-nov05/controls-retry1'
S=R/'artifacts/th14/supervisor-pass-rng-nov05';A=R/'artifacts/th14/script-rng-read-generation-nov05/prefix-player-pump/native'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(case):
    assert shutil.disk_usage(R).free>100*1024**3
    base=S/'comparison-pump-enabled';plan=json.loads((base/'plan.json').read_bytes())
    driver=Path(plan['argv'][2]);original=driver.read_bytes();assert SHA(original)==plan['driverSha256']=='d9247f1c8889063065dfd3c8a895b9ea2e504f29902fe58f364e23e5970ce67c'
    previous=json.loads((base/'model/report.json').read_bytes());assert previous['allRaw32ByteIdentical'] and previous['firstScriptReadWindows']==[]
    native=Path(plan['argv'][plan['argv'].index('--native')+1]);a=json.loads((A/'untouched-first-player.json').read_bytes());b=json.loads((native/'untouched-first-player.json').read_bytes())
    selected={'baseline':(b,b),'time-only':(a,b),'cookie-only':(b,a),'both':(a,a)}[case]
    inputs=dict(timeGetTime=selected[0]['actualInitialTimeGetTimeInput'],cookie=selected[1]['actualOriginalSecurityCookie'])
    if case!='baseline':
        transparency=json.loads((H/'baseline/result.json').read_bytes());assert transparency['baselineSelectedStateByteIdentical']
    out=H/case;assert not out.exists();out.mkdir(parents=True)
    (out/'startup-inputs.json').write_text(json.dumps(inputs)+'\n')
    source=original.decode()
    marker='const archive=read(resolve(assetHome,\'th14.dat\'));';assert source.count(marker)==1
    source=source.replace(marker,"const startupInputs=JSON.parse(read(new URL('./startup-inputs.json',import.meta.url)));assert.deepEqual(Object.keys(startupInputs).sort(),['cookie','timeGetTime']);\n"+marker)
    for old,new in [('c.cold_begin(initial.actualInitialTimeGetTimeInput)','c.cold_begin(startupInputs.timeGetTime)'),('c.reference_environment(initial.actualOriginalSecurityCookie,0x1aec84)','c.reference_environment(startupInputs.cookie,0x1aec84)')]:
        assert source.count(old)==1;source=source.replace(old,new)
    # The accepted baseline explicitly installed no first-read handoff. Do not
    # classify a new control's delivery from native RNG outcome values.
    start=source.index("const replayStoreEvents=stageEvents('replay-rng-store-events.jsonl');")
    end=source.index('let normalBoundary=null;',start)
    source=source[:start]+"// No native-outcome-derived first-script-read windows are installed.\n"+source[end:]
    start=source.index('function compare(index){');end=source.index('initialCreationCount=c.observed_creation_count();compare(0);',start)
    source=source[:start]+'''function compare(index){
 const row=Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32));rows.push(...row);
}
'''+source[end:]
    end=source.index("const raw=Buffer.from(new Uint32Array(rows).buffer);write(resolve(out,'selected-state.u32')")
    source=source[:end]+'''const raw=Buffer.from(new Uint32Array(rows).buffer);
assert.equal(raw.length,limit*128);write(resolve(out,'diagnostic-state.u32'),raw,{flag:'wx'});
write(resolve(out,'driver-result.json'),JSON.stringify({diagnosticOnly:true,callbacks:rows.length/32,wasmSha256:sha(wasm),firstReadWindowsInstalled:0,ordinaryIndependentTimingAccepted:false,completeGame:false})+'\\n',{flag:'wx'});
'''
    dest=out/'driver.mjs';dest.write_text(source,encoding='utf8',newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(dest)],check=True,capture_output=True,timeout=30)
    argv=list(plan['argv']);argv[2]=str(dest);argv[argv.index('--output')+1]=str(out/'model')
    started=time.monotonic()
    with(out/'run.log').open('wb')as log:result=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    result_record=dict(case=case,diagnosticOnly=True,exitCode=result.returncode,elapsedSeconds=time.monotonic()-started,
        parentDriverSha256=SHA(original),diagnosticDriverSha256=SHA(dest.read_bytes()),
        inputFileSha256=SHA((out/'startup-inputs.json').read_bytes()),
        timeInputDiffersFromBaseline=inputs['timeGetTime']!=b['actualInitialTimeGetTimeInput'],
        cookieInputDiffersFromBaseline=inputs['cookie']!=b['actualOriginalSecurityCookie'],
        productionOrFixtureRecompiled=False,acceptanceGatesReplaced=False,ordinaryIndependentTimingAccepted=False,completeGame=False)
    if result.returncode==0:
        raw=(out/'model/diagnostic-state.u32').read_bytes();expected=(base/'model/selected-state.u32').read_bytes();assert len(raw)==len(expected)==35000*128
        differences={};first={}
        for index,(left,right)in enumerate(zip(struct.iter_unpack('<32I',expected),struct.iter_unpack('<32I',raw))):
            for field,(x,y)in enumerate(zip(left,right)):
                if x!=y:
                    differences[field]=differences.get(field,0)+1
                    first.setdefault(field,dict(callback=index+1,stage=right[30],stageFrame=right[0]))
        result_record.update(callbacks=35000,selectedSha256=SHA(raw),baselineSelectedStateByteIdentical=raw==expected,
            differencesFromSameClockBaseline=differences,firstDifferences=first)
        if case=='baseline':assert raw==expected,'Diagnostic collector changed selected-state trajectory'
    size=sum(path.stat().st_size for path in out.rglob('*')if path.is_file());assert size<50*1024**2
    result_record['outputBytes']=size
    (out/'result.json').write_text(json.dumps(result_record,indent=2)+'\n');print(json.dumps(result_record))
    if result.returncode:raise SystemExit(result.returncode)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['baseline','time-only','cookie-only','both'],required=True);main(p.parse_args().case)
