"""Recompute all raw32 core words against an independent warm retail stage case.

Visual RNG differences stay in raw streams. A data-only stage slice does not
prove an uninterrupted transition or a complete original game.
"""
import argparse,hashlib,json,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','report','label','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();native_path,report_path,output=[(ROOT/x).resolve() for x in (a.native,a.report,a.output)]
    assert native_path.is_relative_to(ROOT/'artifacts/th14') and report_path.is_relative_to(ROOT/'docs/porting') and output.is_relative_to(ROOT/'docs/porting')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    bind=lambda path:dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=SHA(path.read_bytes()))
    native,report=read(native_path),read(report_path);init=native['caseInitialization']
    assert native['error']=='' and native['noInputInjection'] and native['childGameStateOverrides']==1 and not native['ordinaryMenuLoaderVerified']
    assert (init['address'],init['before'],init['after'],init['wordWrites'],init['replayManagerMode'])==('0x4f58b8',0x44,4,1,1)
    assert init['afterReadOnlyBootstrap'] and init['beforeFirstPlayerInstruction']
    assert SHA((ROOT/'tools/th14-native-stored-stage-bootstrap-capture.py').read_bytes())==native['warmReplayCaptureToolSha256']
    assert report['passed'] and report['physicalInvocationOrder'] and not report['absentPlayerObservations'] and not report['nativeEquivalent'] and not report['completeGame']
    assert report['nativeTraceSha256']==SHA(native_path.read_bytes()) and report['nativeCaseInitialization']==init
    assert report['nativeWarmCaptureToolSha256']==native['warmReplayCaptureToolSha256']
    assert SHA((ROOT/'tools/th14-physical-replay-reference-trace-check.mjs').read_bytes())==report['toolSha256']
    assert SHA((ROOT/'tools/th14-physical-warm-case-check.mjs').read_bytes())==report['physicalWarmWrapperSha256']
    artifact=ROOT/'artifacts/th14/custom-replay-reference'/a.label
    actual_bytes,expected_bytes=[(artifact/name).read_bytes() for name in ('portable-state.u32','native-state.u32')]
    count=len(native['frames']);assert count==native['capturedFrames']==report['comparedFrames']
    assert len(actual_bytes)==len(expected_bytes)==count*32*4
    assert SHA(actual_bytes)==report['portableStateSha256'] and SHA(expected_bytes)==report['nativeStateSha256']
    words=[]
    for index,row in enumerate(native['frames']):
        assert row['index']==index and row['selection']==native['frames'][0]['selection']
        assert (row['stageFrame']==1 if index==0 else row['stageFrame'] in (native['frames'][index-1]['stageFrame'],native['frames'][index-1]['stageFrame']+1))
        g,p=row['globals'],row['player']
        words.extend(v&0xffffffff for v in [row['stageFrame'],row['held'],row['pressed'],*p[:9],g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],row['scriptRng'][0],row['scriptRng'][2],row['replayRng'][0],row['replayRng'][2],row['enemyCount'],row['shots'],*row['selection'],row['scaleFlags']])
    assert expected_bytes==struct.pack('<'+'I'*len(words),*words)
    actual=struct.unpack('<'+'I'*len(words),actual_bytes)
    differences=[(index//32,index%32,x,y) for index,(x,y) in enumerate(zip(actual,words)) if x!=y]
    assert all(field in (21,22) for _,field,_,_ in differences)
    runtime=ROOT/'runtimes/th12/th12_web'
    for name,digest in report['engineBuild']['sourceHashes'].items():assert SHA((runtime/name).read_bytes())==digest,name
    assert len(report['engineBuild']['sourceHashes'])==265
    assert SHA((artifact/'reference.wasm').read_bytes())==report['wasmSha256']
    for name,key in (('th14-physical-replay-reference-fixture.cpp','fixtureSha256'),('th14-custom-replay-reference-fixture.cpp','customFixtureSha256'),('th14-session-reference-fixture.cpp','includedFixtureSha256')):
        assert SHA((runtime/'tests/cpp'/name).read_bytes())==report[key]
    result=dict(passed=True,completeGame=False,nativeEquivalent=False,ordinaryMenuLoaderVerified=False,stage=native['frames'][0]['selection'][3],
        comparedFrames=count,rawWords=count*32,gameplayDifferences=0,retainedStartupVisualWords=len(differences),sourceFilesVerified=265,
        capturedObjectDifferencesReportedByProducer=len(report['detailDifferences']),nativeCaseInitialization=init,
        nativeSelectionChanged=native['selectionChanged'],nativeNextSelection=native.get('nextSelection'),nativeCaptureTimedOut=native['timedOut'],physicalInvocationOrder=True,repeatedStageClockRows=sum(i>0 and r['stageFrame']==native['frames'][i-1]['stageFrame'] for i,r in enumerate(native['frames'])),
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=[bind(path) for path in (native_path,report_path,artifact/'reference.wasm')],
        scope='Independent recomputation of every raw32 production word versus every warm retail callback in physical order, including repeated stage clocks; no rows trimmed or merged. Only two startup visual RNG columns differ, with all raw differences retained. Native keeps later-stage flag4 and clears attract bit40 once; no stock/health/input/RNG edits. Captured object windows are producer checks. This does not certify original backend64, uninterrupted loading/transition, full original clear or graphics/audio/browser storage.')
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('passed','stage','comparedFrames','rawWords','gameplayDifferences','retainedStartupVisualWords')}))


if __name__=='__main__':main()
