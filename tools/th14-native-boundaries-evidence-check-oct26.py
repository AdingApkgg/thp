"""Bind original UI score bytes, a rejected campaign end, and verifier scope checks."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda data:hashlib.sha256(data).hexdigest()
OUTPUT=ROOT/'docs/porting/th14-native-boundaries-verified-oct26.json'

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    bindings={}
    def read(name):
        path=ROOT/name;data=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data
    def load(name):return json.loads(read(name))
    ui='artifacts/th14/ordinary-menu-ui-oct26/'
    observed=load(ui+'observed.json');score=load(ui+'score-current/report.json');build=load(ui+'score-current/build.json');native=load(ui+'score-current/native/native.json')
    packed=read(ui+'appdata/ShanghaiAlice/th14/scoreth14.dat');raw=read(ui+'score-current/production.raw')
    assert observed['privateScoreFileWritten']and observed['processExitObserved']and observed['noGameMemoryWrites']
    assert observed['originalUserAppdataConfiguredAway']and not observed['ordinaryFullFlowAccepted']
    assert score['passed']and native['passed']and score['actualNativeColdStartFile']
    assert len(packed)==21633==score['inputBytes']==native['inputBytes']==observed['privateScoreBytes']
    assert SHA(packed)==observed['privateScoreSha256']==score['inputSha256']==native['inputSha256']==native['rewrittenSha256']
    assert packed==read(ui+'score-current/production.dat')==read(ui+'score-current/native/retail-rewritten.dat')
    assert len(raw)==149076==score['rawBytes']==native['decodedBytes']
    assert SHA(raw)==score['rawSha256']==native['decodedSha256']and raw==read(ui+'score-current/native/retail-loaded.raw')
    assert SHA(read(ui+'score-current/score.wasm'))==score['wasmSha256']==build['wasmSha256']
    assert SHA(read(ui+'score-current/build.json'))==score['buildSha256']
    assert SHA(read('tools/th14-natural-score-native.py'))==native['toolSha256']
    for path,digest in build['fixtureDependencies'].items():assert SHA(read(Path(path).relative_to(ROOT)))==digest
    for row in build['reusedObjects']:assert SHA(read(Path(row['path']).relative_to(ROOT)))==row['sha256']
    base='artifacts/th14/stage-item-retirement-oct25/'
    engine=load(base+'curve-origin-observer-oct26/observer-build.json')
    for name,digest in {**engine['sourceHashes'],**engine['headerHashes']}.items():
        if name=='th12_web/cpp/game/ResourceCrypt.cpp':
            assert SHA(read('runtimes/th12/'+name))=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
        else:assert SHA(read('runtimes/th12/'+name))==digest,name
    assert build['unrelatedResourceCryptExcluded']
    source_exe='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert SHA(read(ui+'work/th14.exe'))==source_exe==observed['sourceExecutableSha256']==native['nativeExecutableSha256']
    assert SHA(read(ui+'work/th14.dat'))==observed['sourceArchiveSha256']=='57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233'
    sakuya='artifacts/th14/retail-sakuyaa-hard-callback-rng-hardware-oct26/'
    original=load(sakuya+'report.json');prefix=load(base+'sakuyaa-hard-observed-prefix-60393-verified-oct26.json')
    assert original['callbacks']==60393 and original['childExited']and not original['error']
    assert not original['observedForcedReplayEndMenu']and not original['observedReplayTerminalMarker']
    assert prefix['verifiedFiniteEvidence']and prefix['diagnosticPrefixOnly']and prefix['callbacks']==60393
    assert not prefix['originalNaturalReplayEndObserved']and prefix['vm303Rows']==2585 and prefix['combatCheckpoints']==891
    for path,bound in prefix['bindings'].items():assert SHA(read(path))==bound['sha256'],path
    verifier='tools/th14-verify-native-campaign.py';verifier_hash=SHA(read(verifier));assert verifier_hash==prefix['verifierSha256']
    full=load(base+'reimub-normal-verifier-scope-regression-oct26.json')
    assert full['verifiedFiniteEvidence']and full['callbacks']==122537 and not full['diagnosticPrefixOnly']and full['originalNaturalReplayEndObserved']
    assert full['verifierSha256']==verifier_hash
    rejected=ROOT/base/'rejected-full-sakuyaa-oct26.json';assert not rejected.exists()
    command=[sys.executable,str(ROOT/verifier),'--native',str(ROOT/sakuya),'--model',str(ROOT/base/'sakuyaa-hard-curve-origin-observed-prefix-60393-oct26'),'--build',str(ROOT/base/'curve-origin-observer-oct26/observer-build.json'),'--output',str(rejected)]
    result=subprocess.run(command,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode!=0 and 'AssertionError'in result.stderr and not rejected.exists()
    probe='artifacts/th14/retail-exit-event-bounded-probe-oct26/'
    exit_probe=load(probe+'report.json');assert exit_probe['callbacks']==200 and exit_probe['childExited']and not exit_probe['error']
    assert exit_probe['observerTerminationRequested']and not exit_probe['observedForcedReplayEndMenu']
    assert exit_probe['processExitEvent']['observerTerminationRequested']and exit_probe['processExitEvent']['exitCode']==0
    assert exit_probe['processExitEvent']['callbacks']==200
    assert SHA(read(probe+'observer-source.py'))==exit_probe['sourceSha256']==SHA(read('tools/th14-native-campaign-observer-oct25.py'))
    report=dict(schema='th14/native-boundaries/1',productionChanged=False,actualOriginalUiScore=dict(bytes=len(packed),encodedSha256=SHA(packed),decodedBytes=len(raw),decodedSha256=SHA(raw),currentProductionAndOriginalCodecEqual=True,wasmSha256=score['wasmSha256'],ordinaryMenuGameplayUnconfirmed=True,browserPersistenceAccepted=False),sakuyaaHard=dict(capturedCallbacks=60393,stagesObserved=original['recordedStages'],processExited=True,naturalReplayEndObserved=False,previousObserverDidNotRecordExitCode=True,independentlyVerifiedDiagnosticPrefixCallbacks=prefix['callbacks'],vm303Rows=prefix['vm303Rows'],combatCheckpoints=prefix['combatCheckpoints'],nonemptyCombatCheckpoints=prefix['nonemptyCombatCheckpoints'],allStatedPrefixGatesEqual=True,naturalModeInventoryIncrement=0),scopeRegression=dict(unmarkedFullRunRejected=True,previousNormalFullCallbacks=full['callbacks'],previousNormalFullStillAccepted=True),observerExitProbe=dict(callbacks=200,observerRequestedTermination=True,exitCodeObserved=0,notNaturalCompletion=True),sourceHashes={p:SHA(read(p))for p in ['tools/th14-native-campaign-observer-oct25.py',verifier,'tools/th14-natural-score-native.py']},bindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()),limits=['The original UI wrote a private filesystem score; UI gameplay, browser reload and browser persistence remain unproved.','The Sakuya A Hard process exited before a recorded terminal menu. Exit cause and code were not captured; it is excluded from natural-run counts.','Prefix comparison covers only retained selected fields, sampled objects and the initial publication window. It is not whole-run or mode equivalence.','The bounded exit probe deliberately terminates the private child after 200 callbacks. Exit code zero is not a natural-end criterion.'],completeGame=False,nativeEquivalent=False)
    if args.check:assert json.loads(OUTPUT.read_bytes())==report
    else:OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(verified=True,scoreBytes=len(packed),decodedBytes=len(raw),sakuyaaDiagnosticCallbacks=prefix['callbacks'],naturalModeInventoryIncrement=0,fullScopeNegativeCheckPassed=True,exitEventProbePassed=True)))

if __name__=='__main__':main()
