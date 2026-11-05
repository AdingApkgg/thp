"""Run the native-bound per-store host and its deliberate before-read negative."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
OLD = R / 'artifacts/th14/original-nine-shot-native-nov05'
H = R / 'artifacts/th14/natural-store-boundaries-nov05'
SHA = lambda data: hashlib.sha256(data).hexdigest()


def main(case):
    if case in ['on','negative']:
        prior = json.loads((H / 'off/result.json').read_bytes())
        assert prior['strictDriverExitCode'] == prior['rawVerifierExitCode'] == 0
    parent = OLD / 'comparison-driver/driver-off.mjs'
    raw = parent.read_bytes()
    assert SHA(raw) == '8e7d54cf1dd3899abcb7f581905ea7fe19b8366c761468c0c2254636a9cf1d5e'
    source = raw.decode()
    changes = []

    def replace(before, after):
        nonlocal source
        assert source.count(before) == 1, (before[:100],source.count(before))
        source = source.replace(before,after)
        changes.append((before,after))

    replace('let normalBoundary=null;', '''const naturalBoundaryPath=resolve(root,'artifacts/th14/natural-store-boundaries-nov05/native-boundaries.json');
const naturalBoundaryBytes=read(naturalBoundaryPath),naturalBoundary=JSON.parse(naturalBoundaryBytes);
assert(naturalBoundary.verifiedNativeAcknowledgementEdges&&naturalBoundary.logicalAcknowledgementBoundariesOnly);
assert(naturalBoundary.noNativeRngOrVmValuesProvidedToEngine&&!naturalBoundary.independentTimingAccepted);
assert.equal(naturalBoundary.verifierSha256,sha(read(resolve(root,'tools/th14-natural-store-boundaries-nov05.py'))));
for(const[name,row]of Object.entries(naturalBoundary.evidenceBindings))assert.equal(sha(read(resolve(root,name))),row.sha256);
assert.equal(naturalBoundary.evidenceBindings[relative(root,resolve(nativeHome,'report.json')).replaceAll('\\\\','/')]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
const naturalBoundaryTimes=naturalBoundary.storeReceiptNs.map(now=>baseNow+BigInt(now)-playerOrigin);
assert.equal(c.natural_store_configure(naturalBoundary.stage,naturalBoundary.callback,naturalBoundary.ownerStage,
 naturalBoundary.objectIndex,naturalBoundary.firstPrimitive,naturalBoundary.firstAnimation,
 naturalBoundary.nextPrimitive,naturalBoundary.nextAnimation,naturalBoundary.file,naturalBoundary.script,
 ...naturalBoundaryTimes,NEGATIVE_BEFORE_READ),1);
let normalBoundary=null;'''.replace('NEGATIVE_BEFORE_READ','1' if case=='negative' else '0'))
    if case == 'on':
        replace('c.shot_lifetime_install(0)','c.shot_lifetime_install(1)')
    anchor='const report={schedulerPhases,'
    replace(anchor, '''const naturalStoreState=Array.from({length:8},(_,i)=>c.natural_store_state(i)>>>0);
assert.deepEqual(naturalStoreState,[1,0,15,4,1,1,1,0]);
const naturalStoreObservations=Array.from({length:4},(_,row)=>Array.from({length:12},(_,word)=>c.natural_store_observation(row,word)>>>0));
assert.deepEqual(naturalStoreObservations.map(row=>row[0]),[0,1,2,3]);
assert(naturalStoreObservations.every(row=>row[1]===naturalBoundary.callback&&row[2]===naturalBoundary.stage));
const naturalNativeStores=stageEvents('replay-rng-store-events.jsonl').filter(row=>row.stage===naturalBoundary.stage);
const naturalNativeAccess=stageEvents('script-rng-access-events.jsonl');
const naturalRngWords=row=>Array.from({length:4},(_,i)=>Buffer.from(row.rngHex??row.rngHexAtObservation,'hex').readUInt32LE(i*4));
const naturalExpected=[naturalRngWords(naturalNativeStores[0]),naturalRngWords(naturalNativeAccess[0]),naturalRngWords(naturalNativeStores[2]),naturalRngWords(naturalNativeStores[3])];
assert.equal(naturalExpected[1][0]&65535,naturalNativeStores[1].registers.eax&65535);
const naturalDifferences=[];
for(let row=0;row<4;row++)for(let word=0;word<4;word++)if(naturalStoreObservations[row][3+word]!==naturalExpected[row][word])naturalDifferences.push({point:row,word});
write(resolve(out,'natural-store-observations.u32'),Buffer.from(new Uint32Array(naturalStoreObservations.flat()).buffer),{flag:'wx'});
assert.equal(c.natural_store_finish(),1);assert.equal(c.natural_store_state(6),0);
write(resolve(out,'natural-store-report.json'),JSON.stringify({separateRealWorkerStores:true,allFourObservedRngStatesEqual:naturalDifferences.length===0,
 differences:naturalDifferences,observations:4,comparedRngWords:16,realReplayRngRestoreJobUsed:true,realSnapshotReadinessUsed:true,
 activeEffectsRestored:true,lateInstalledAuditorPreserved:true,legacyInitializeMetadataOverriddenByPerStoreHost:true,
 nativeSeedsOrVmWordsProvidedToEngine:false,logicalAcknowledgementBoundariesOnly:true,exactExecutionTimesRecovered:false,
 proofSha256:sha(naturalBoundaryBytes),completeGame:false})+'\\n',{flag:'wx'});
''' + anchor)
    source += "\nassert.equal(naturalDifferences.length,0,'Per-store observed RNG state differs');\n"
    restored = source.removesuffix("\nassert.equal(naturalDifferences.length,0,'Per-store observed RNG state differs');\n")
    for before,after in reversed(changes):
        assert restored.count(after) == 1
        restored = restored.replace(after,before)
    assert restored.encode() == raw
    out = H / case
    assert not out.exists()
    out.mkdir()
    driver = out / 'driver.mjs'
    driver.write_text(source,encoding='utf8',newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(driver)],check=True,capture_output=True,timeout=30)
    argv = list(json.loads((OLD / 'comparison-off/plan.json').read_bytes())['argv'])
    argv[2] = str(driver)
    argv[argv.index('--output')+1] = str(out / 'model')
    argv[argv.index('--build')+1] = str(H / 'build-retry1/observer-build.json')
    (out / 'plan.json').write_text(json.dumps(dict(argv=argv,driverSha256=SHA(driver.read_bytes()),
        parentDriverSha256=SHA(raw),allOriginalFinalGatesPreserved=True,exactReversalRestoresParent=True,
        perStoreAndSnapshotAckHostAdded=True,negativeBeforeRead=(case=='negative'),
        nativeValuesProvidedToEngine=False,productionChanged=False,completeGame=False),indent=2)+'\n')
    start=time.monotonic()
    with(out / 'driver.log').open('wb')as log:
        process=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
    code=None
    if(out / 'model/report.json').exists():
        with(out / 'verify.log').open('wb')as log:
            verifier=subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),
                '--native',argv[argv.index('--native')+1],'--model',str(out/'model'),
                '--build',argv[argv.index('--build')+1],'--prefix','35000',
                '--output',str(out/'raw-verified.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,
                timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        code=verifier.returncode
    result=dict(case=case,strictDriverExitCode=process.returncode,rawVerifierExitCode=code,
        elapsedSeconds=time.monotonic()-start,logicalAcknowledgementBoundariesOnly=True,
        productionChanged=False,completeGame=False)
    if case=='on'and process.returncode==code==0:
        for name in ['selected-state.u32','full-camera.u32','replay-cursor.u32','portable-hud.u32']:
            assert(out/'model'/name).read_bytes()==(H/'off/model'/name).read_bytes()
        result['readonlyProbeTransparentForCapturedState']=True
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if process.returncode==code==0 else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=['off','on','negative'],required=True)
    raise SystemExit(main(parser.parse_args().case))
