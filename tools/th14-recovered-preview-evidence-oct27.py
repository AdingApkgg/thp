"""Bind the recovered TH14 candidate and retained failed ordinary-UI attempt.

Only metadata and hashes are written. HTTP serving is not browser acceptance;
storage recovery is not gameplay evidence. No UI, audio or original process is
launched by this verifier.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/initial-replay-restore-oct27'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    bindings={}
    def read(path):
        raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        return raw
    def load(path):return json.loads(read(path))
    build=load(HOME/'browser-candidate-recovered/build.json')
    package=load(HOME/'browser-runtime-recovered/package-report.json')
    routes=load(HOME/'launcher-recovered/launcher-report.json')
    transport=load(HOME/'launcher-recovered/transport.json')
    served=load(HOME/'served-current.json')
    commit='1d9999a47ea1c8510d4983d47ff22c50a544fad6'
    wasm=read(HOME/'browser-candidate-recovered/th14-sdl.wasm')
    checksum=hashlib.sha256(wasm).hexdigest()
    assert build['compiled'] and build['compiledUnits']==146 and build['basePublishedCommit']==commit and build['title']==14
    assert len(wasm)==2700286
    assert checksum==build['wasmSha256']==package['wasmSha256']==routes['wasmSha256']==transport['wasmSha256']==served['wasmSha256']
    assert served['compiledCppUnits']==146 and served['basePublishedCommit']==commit
    assert served['quietByDefault'] and served['actualServedWasmAndShaderAndHostBytesEqual']
    assert transport['verifiedTransport'] and transport['routes']==133 and len(transport['requests'])==21
    assert served['generatedResourceAliases']==28 and served['generatedResourceBytesAliased']==414850582
    for path,row in build['sourceBindings'].items():
        assert hashlib.sha256(read(HOME/'browser-candidate-recovered/source'/path)).hexdigest()==row['sha256'],path
    courier=ROOT/'tools/tmp/github-source-release'
    for relative in ('th12_web/cpp/game/GameSession.cpp','th12_web/cpp/game/Replay.cpp'):
        name='runtimes/th12/'+relative
        published=subprocess.check_output(['git','-C',str(courier),'show',commit+':'+name])
        assert published==read(ROOT/name)==read(HOME/'browser-candidate-recovered/source'/relative)
    refusal=load(HOME/'browser-candidate/storage-limit.json')
    assert refusal['storageBudgetExceeded'] and refusal['freeBytes']<refusal['minimumFreeBytes']
    assert refusal['minimumFreeBytes']==100*1024**3
    compressed=load(HOME/'shared-input-compression/verified.json')
    assert len(compressed['files'])==11 and compressed['allContentsPathsSizesMtimesReadonlyAndAliasesUnchanged']
    assert compressed['deletedFiles']==0 and not compressed['originalGameFilesChanged']
    dedupe=load(HOME/'bgm-input-dedupe/verified.json')
    manifest=load(HOME/'bgm-input-dedupe/manifest.json')
    restore=load(HOME/'bgm-input-dedupe/restore-probe.json')
    assert len(manifest['files'])==dedupe['replacedIndependentWorkingCopies']==23
    assert dedupe['workingInputLogicalBytes']==23*397831536
    for field in ('allWorkingPathsAndContentHashesPreserved','workingPathsNowReadOnlyCacheAliases',
                  'originalWorkingMetadataRecoverable','actualIndependentCopyRestoreProbePassed','allReferenceReportsHashesUnchanged'):
        assert dedupe[field]
    assert dedupe['observationOrFailureFilesRemoved']==0 and not dedupe['originalGameFilesChanged']
    assert restore['verified'] and restore['independentCopy'] and restore['originalMtimeBirthtimeAndReadonlyRestored']
    assert restore['temporaryProbeRemoved'] and restore['sha256']==manifest['sha256']
    for name in ('restore.py','run-tool.py','manifest.json','plan.json'):
        read(HOME/'bgm-input-dedupe'/name)
    canonical=ROOT/manifest['canonical']
    original=Path(json.loads((ROOT/'runtimes/th14/target.json').read_text())['executable']).parent/'thbgm.dat'
    assert not os.path.samefile(canonical,original)
    for row in manifest['files']:
        assert os.path.samefile(ROOT/row['path'],canonical)
        assert (ROOT/row['reference']).stat().st_size>0
    failed=load(HOME/'ordinary-native-menu/report.json')
    ui=load(HOME/'ordinary-native-menu/ui-attempt.json')
    frozen=read(HOME/'ordinary-native-menu/run-tool.py')
    assert hashlib.sha256(frozen).hexdigest()==failed['sourceSha256']
    assert frozen==read(ROOT/'tools/th14-ordinary-replay-observer-oct27.py')
    assert failed['callbacks']==0 and failed['firstPlayer']is None and not failed['observedForcedReplayEndMenu']
    assert failed['instructionWrites']==failed['gameStateWrites']==0
    assert not ui['ordinaryMenuReplayEntered'] and ui['confirmedInputDrivenMenuTransitions']==0
    assert not ui['inputDeliveryCauseProven'] and not ui['browserControlled']
    assert bytes.fromhex(failed['configHex'])[0x22:0x24]==bytes(2)
    report=dict(verifiedRecoveredCandidate=True,basePublishedCommit=commit,compiledCppUnits=146,
        wasmBytes=len(wasm),wasmSha256=checksum,routes=133,httpRequests=21,
        servedUrl=served['url'],quietByDefault=True,servedBytesVerified=True,
        generatedAssetAliases=28,generatedAssetLogicalBytes=414850582,
        independentWorkingBgmCopiesDeduplicated=23,workingBgmLogicalBytes=23*397831536,
        independentCopyRestoreProbePassed=True,workingOriginalMetadataRecoverable=True,
        referenceHashesUnchangedAtDeduplication=True,observationsOrFailuresRemoved=0,originalGameFilesChanged=False,
        compressedInputGroups=11,reportedCompressedBytesSaved=compressed['reportedCompressedBytesBefore']-compressed['reportedCompressedBytesAfter'],
        initialCapacityRefusalRetained=True,minimumFreeBytes=100*1024**3,
        ordinaryNativeUiAttemptRetained=True,ordinaryNativeUiPlayerCallbacks=0,ordinaryNativeUiAccepted=False,
        physicalAudioMeasured=False,browserRun=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),bindings=bindings)
    output=ROOT/'docs/porting/th14-recovered-preview-verified-oct27.json'
    if args.check:assert json.loads(output.read_text())==report
    else:output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items()if k!='bindings'}))

if __name__=='__main__':main()
