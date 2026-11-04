"""Compare the sealed rotating-pump prefix with the observed-prefix unanchored driver.

Failure is retained. This tool never substitutes a previous-Player clock,
changes the driver, filters VM flags or passes native seed values to C++.
"""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys,time

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
N=H/'prefix-rotating-pump/native'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main(out):
    end=json.loads((N.parent/'process-end.json').read_bytes())
    report=json.loads((N/'report.json').read_bytes())
    assert end['guardStop']is None and end['exitCode']==1
    assert report['callbacks']==35000 and report['childExited']and not report['error']and not report['debugErrors']
    assert not out.exists();out.mkdir(parents=True)
    (out/'run-tool.py').write_bytes(Path(__file__).read_bytes())
    def run(label,argv):
        started=time.monotonic()
        with(out/(label+'.log')).open('wb')as stream:
            p=subprocess.run(argv,cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
        value=dict(argv=argv,exitCode=p.returncode,elapsedSeconds=time.monotonic()-started,
            logSha256=SHA((out/(label+'.log')).read_bytes()))
        (out/(label+'-process.json')).write_text(json.dumps(value,indent=2)+'\n');return p.returncode
    evidence_tool=R/'tools/th14-rng-pump-trace-evidence-nov05.py'
    assert run('native-evidence',[sys.executable,'-X','utf8',str(evidence_tool),'--native',str(N),'--output',str(out/'native-register-proof.json')])==0
    accesses=[json.loads(x)for x in (N/'script-rng-access-events.jsonl').read_bytes().splitlines()]
    first=min(x['precedingPlayerCallbacks']for x in accesses);last=max(x['precedingPlayerCallbacks']for x in accesses)+1
    driver=R/'tools/th14-compare-native-rng-pump-prefix-nov05.mjs'
    assert SHA(driver.read_bytes())=='16b2b68d19fc4d121ddf1eb5b70b89327d9a76e77619b5f92d9c25930fce50dd'
    build=H/'portable-audit-build/observer-build.json';build_info=json.loads(build.read_bytes())
    assert build_info['wasmSha256']=='b129d06717e7e09f0d5fa4e8090993bc3177c88fa74bbc77fa254a52580eefef'
    model=out/'model'
    argv=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(driver),'--native',str(N),'--assets',
        str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),'--build',str(build),
        '--output',str(model),'--prefix','35000','--selection','0,1,1,1','--scheduler-phases','observed',
        '--rng-audit-first',str(first),'--rng-audit-last',str(last)]
    plan=dict(driverSha256=SHA(driver.read_bytes()),buildSha256=SHA(build.read_bytes()),
        nativeReportSha256=SHA((N/'report.json').read_bytes()),nativeEvidenceToolSha256=SHA(evidence_tool.read_bytes()),
        nativeSeedValuesProvidedToEngine=False,inferredFrameEntryFallback=False,vmFlagsUsedToFilter=False,
        auditFirstCallback=first,auditLastCallback=last,argv=argv,completeGame=False)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    code=run('unanchored-comparison',argv)
    if code:
        v=dict(unanchoredComparisonPassed=False,comparisonExitCode=code,inferredFrameEntryFallbackAdded=False,
            failureRetained=True,ordinaryIndependentTimingAccepted=False,completeGame=False)
        (out/'comparison-result.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));return 2
    raw_tool=R/'tools/th14-verify-native-campaign.py'
    raw_code=run('raw-verifier',[sys.executable,'-X','utf8',str(raw_tool),'--native',str(N),'--model',str(model),
        '--build',str(build),'--prefix','35000','--output',str(out/'raw-verified.json')])
    c=(N/'world-camera.raw').read_bytes();tail=(N/'world-camera-tail.u32').read_bytes();pc=(model/'full-camera.u32').read_bytes()
    assert len(c)==35000*292 and len(tail)==35000*8 and len(pc)==34999*300
    camera_differences=sum(sum(a!=b for a,b in zip(struct.unpack('<75I',pc[(i-1)*300:i*300]),struct.unpack('<75I',c[i*292:(i+1)*292]+tail[i*8:(i+1)*8])))for i in range(1,35000))
    nc=(N/'replay-cursor.u32').read_bytes();cc=(model/'replay-cursor.u32').read_bytes();assert len(nc)==35000*56 and len(cc)==34999*16
    cursor_differences=sum(sum(a!=b for a,b in zip(struct.unpack_from('<4I',cc,(i-1)*16),tuple(struct.unpack_from('<I',nc,i*56+j*4)[0]for j in [3,7,8,9])))for i in range(1,35000))
    portable=(model/'rng-register-audit.u32').read_bytes();assert len(portable)%64==0
    # Compare only script-role records, in output order. No VM flags, handles,
    # lifecycle flags, seeds or counter values decide which rows are selected.
    prows=[x for x in struct.iter_unpack('<16I',portable)if x[3]==0]
    differences=dict(callback=0,point=0,actualLoadedOrStoredSeed=0,sampledScriptCalls=0)
    assert len(prows)>=len(accesses)
    for n,p in zip(accesses,prows):
        kind=n['instructionContract']['kind'];assert kind in ['mix32','store32']
        expected=[n['precedingPlayerCallbacks'],1 if kind=='mix32'else 4,n['valueRetainedByTrappedInstruction'],struct.unpack_from('<I',bytes.fromhex(n['rngHexAtObservation']),4)[0]]
        actual=[p[0],p[2],p[4],p[5]]
        for key,a,b in zip(differences,expected,actual):differences[key]+=a!=b
    selected_equal=(N/'selected-state.u32').read_bytes()==(model/'selected-state.u32').read_bytes()
    generic=json.loads((out/'raw-verified.json').read_bytes())if raw_code==0 else None
    passed=not raw_code and selected_equal and not camera_differences and not cursor_differences and not any(differences.values())
    v=dict(verifiedFiniteUnanchoredComparison=passed,comparisonDriverExitCode=code,rawVerifierExitCode=raw_code,
        callbacks=35000,all32StateFieldsEqual=selected_equal,comparedCameraWords=2624925,cameraWordDifferences=camera_differences,
        cursorWordDifferences=cursor_differences,nativeInstructionAccesses=len(accesses),portableScriptRows=len(prows),
        extraPortableRowsNotAccepted=len(prows)-len(accesses),instructionDifferences=differences,
        vm303Rows=generic['vm303Rows']if generic else None,combatCheckpoints=generic['combatCheckpoints']if generic else None,
        nonemptyCombatCheckpoints=generic['nonemptyCombatCheckpoints']if generic else None,
        originalRngValuesProvidedToEngine=False,inferredFrameEntryFallbackAdded=False,flags4000UsedToFilter=False,
        exactOriginalFrameEntryRecovered=False,ordinaryIndependentTimingAccepted=False,completeGame=False,
        verifierSha256=SHA(Path(__file__).read_bytes()))
    (out/'comparison-result.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v));return 0 if passed else 2

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(H)and out!=H
    raise SystemExit(main(out))
