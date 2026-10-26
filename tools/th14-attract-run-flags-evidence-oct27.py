"""Verify production mode-flag propagation and bounded actual Application probes.

The ECL554 guard is an original-code component. No ECL554 call or corrected
pixel is claimed in the observed Application prefixes. The original first
Player record precedes its explicitly declared warm-case attract-bit clear.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,re,struct,subprocess

ROOT=Path(__file__).resolve().parents[1]
HOME=ROOT/'artifacts/th14/attract-run-flags-oct27'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');args=parser.parse_args();bindings={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());return raw
    def load(path):return json.loads(read(path))
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    native=load(HOME/'native-guard-budgeted/native.json')
    assert len(native['cases'])==28 and native['stopsBeforeResourceAndCreation'] and not native['realOriginalProcessLaunched']
    assert native['minimumFreeBytes']==100*1024**3 and native['maximumObservationBytes']==128*1024**2
    assert native['sourceSha256']==sha(read(ROOT/'tools/th14-attract-run-flags-native-oct27.py'))==sha(read(HOME/'native-guard-budgeted/run-tool.py'))
    spec=importlib.util.spec_from_file_location('flag_image',ROOT/'tools/th14-loading-lifecycle-evidence-check.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);image=helper.Image()
    assert sha(image.data)==native['originalExecutableSha256']
    assert image.bytes(0x425577,5).hex()==native['callBytesHex']
    assert image.bytes(0x434e10,0x25).hex()==native['guardBytesHex']
    for row in native['cases']:
        wanted=row['mode']!=8 and not row['flags']&64
        assert row['entersCreationBody']==wanted and row['stopPc']==(0x434e35 if wanted else 0x434edb)
    original_home=ROOT/'artifacts/th14/retail-sakuyab-hard-exit-boundary-hardware-oct26'
    first=load(original_home/'untouched-first-player.json');original=load(original_home/'report.json')
    assert first['attractFlags']==64 and first['replayManagerMode']==1
    assert original['gameStateWordWrites']==1 and original['caseInitialization']['attractBitClearOnly']
    assert original['caseInitialization']['beforeFlags']==64 and original['caseInitialization']['afterFlags']==0
    assert original['sourceSha256']==sha(read(original_home/'observer-source.py'))
    assert original['executableSha256']==native['originalExecutableSha256']
    assert struct.unpack('<32I',read(original_home/'selected-state.u32')[:128])==tuple(first['words'])
    current='runtimes/th12/th12_web/cpp/game/GameSession.cpp'
    current_raw=read(ROOT/current)
    assert b'th14_run_flags=state.demo?0x40u:'in current_raw
    assert b'(state.spell_practice_id>=0?0x20u:state.practice?0x10u:0u)|(state.replay?2u:0u);'in current_raw
    old=read(ROOT/'artifacts/th14/initial-replay-restore-oct27/core-build-v2/GameSession.cpp')
    assert b'th14_run_flags=state.spell_practice_id>=0?32:state.practice?16:0;'in old
    courier=ROOT/'tools/tmp/github-source-release'
    assert old==subprocess.check_output(['git','-C',str(courier),'show','1d9999a47ea1c8510d4983d47ff22c50a544fad6:'+current])
    core=load(HOME/'core-build/observer-build.json')
    assert core['engineSourcesRecompiledForThisLink']==1 and core['engineObjectsReusedForThisLink']==140
    assert core['recompiledSources']=={'th12_web/cpp/game/GameSession.cpp':sha(current_raw)}
    assert current_raw==read(HOME/'core-build/GameSession.cpp')
    for row in core['objectBindings']:assert sha(read(Path(row['path'])))==row['sha256']
    pairs=[]
    for name,before_name,after_name,old_flags,new_flags,frames in (
        ('attract','before-state','after-state',16,64,2264),
        ('ordinary','before-ordinary','after-ordinary',0,2,722)):
        old_report=load(HOME/before_name/'report.json');new_report=load(HOME/after_name/'report.json')
        for report,folder,flags,build_folder in ((old_report,before_name,old_flags,'before-state-build'),(new_report,after_name,new_flags,'after-state-build')):
            assert report['completed'] and not report['error'] and report['frames']==frames
            assert not report['physicalAudioDevicesOpened'] and not report['browserAcceptance']
            raw=read(HOME/folder/'run-tool.py');assert sha(raw)==report['toolSha256']
            build=load(HOME/build_folder/'build.json')
            assert build['readOnlyStateAndLogoCallProbes'] and report['buildReportSha256']==sha(read(HOME/build_folder/'build.json'))
            assert report['wasmSha256']==build['wasmSha256']==sha(read(HOME/build_folder/'application.wasm'))
            for path,row in build['sourceBindings'].items():assert sha(read(ROOT/path))==row['sha256'],path
            text=read(HOME/folder/'stdout.log').decode()
            matches=re.findall(r'TH14_RUN_FLAGS flags=(\d+) demo=(\d+) replay=(\d+) practice=(\d+) stage=(\d+) frame=(\d+)',text)
            assert len(matches)==1
            values=list(map(int,matches[0]));assert values[0]==flags
            assert values[1:]==([1,1,1,3,1]if name=='attract'else[0,1,0,1,1])
            assert 'TH14_LOGO_CALL'not in text
        for key in ('rows','actions','checks','captures','initialSave','finalSave','pcmFrames','pcmSha256'):
            assert old_report[key]==new_report[key],(name,key)
        for capture in old_report['captures']:
            assert read(HOME/before_name/capture['file'])==read(HOME/after_name/capture['file'])
        pairs.append(dict(case=name,frames=frames,checks=len(new_report['checks']),journalRows=len(new_report['rows']),
            images=len(new_report['captures']),pcmFrames=new_report['pcmFrames'],oldRunFlags=old_flags,newRunFlags=new_flags,
            logsImagesPcmAndFilesPreserved=True,actualEcl554CallObserved=False))
    assert b'missing terminating'in read(HOME/'before-build/fixture.compile.log')
    read(HOME/'before-build/run-tool.py')
    result=dict(schema='th14/attract-run-flags-repair/1',verifiedModeFlagPropagation=True,
        actualProductionGameSessionCompiled=True,coreSourcesRecompiled=1,coreObjectsReused=140,
        originalGuardCases=28,originalUntouchedAttractFlags=64,originalRecordPrecedesDeclaredWarmBitClear=True,
        previousAttractFlags=16,currentAttractFlags=64,previousOrdinaryReplayFlags=0,currentOrdinaryReplayFlags=2,
        pairs=pairs,actualEcl554CallObserved=False,correctedPixelClaimed=False,
        oldFullReplayFailureAttributedToThisChange=False,oldFailuresRetained=True,
        originalOrdinaryUiAccepted=False,browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=sha(Path(__file__).read_bytes()),bindings=bindings)
    output=ROOT/'docs/porting/th14-attract-run-flags-verified-oct27.json'
    if args.check:assert json.loads(output.read_text())==result
    else:output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='bindings'}))

if __name__=='__main__':main()
