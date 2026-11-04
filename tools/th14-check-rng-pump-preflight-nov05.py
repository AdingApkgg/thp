"""Check a terminated1200-callback native prefix before any stage3 trace."""
from pathlib import Path
import hashlib, json, struct, subprocess, sys, time

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
D=H/'preflight-rotating-pump';N=D/'native';M=D/'comparison'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def main():
    assert not M.exists()and not(D/'verified.json').exists()
    end=json.loads((D/'process-end.json').read_bytes());native=json.loads((N/'report.json').read_bytes())
    prep=json.loads((H/'observer-rotating-pump/prepared.json').read_bytes())
    assert end['exitCode']==1 and end['guardStop']is None
    assert native['callbacks']==1200 and native['childExited']and not native['error']and not native['debugErrors']
    assert native['sourceSha256']==prep['observerSha256']==SHA((N/'observer-source.py').read_bytes())==SHA((H/'observer-rotating-pump/observer.py').read_bytes())
    assert native['configuredMusicAndSoundVolumeZero']and native['gameStateWordWrites']==1 and native['rngOrCounterWrites']==0
    assert not native['scriptRngAccessWatchArmed']and not native['scriptRngRegisterAccessEvents']
    assert native['pendingCrossThreadHardwareStatePreserved']and native['unrecognizedExceptionPolicyUnchanged']
    build=R/'artifacts/th14/scene-camera-read-job-nov04/session-observer-v2/observer-build.json'
    driver=R/'tools/th14-compare-native-scene-word-read-nov04.mjs'
    assert SHA(driver.read_bytes())=='2ab9b608568fa6de14f1a5f3f495d94fd74c773e8f036c87d25cc9040b93d0c1'
    argv=['C:/nvm4w/nodejs/node.exe','--no-warnings',str(driver),'--native',str(N),'--assets',
        str(R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-c48412a95f0f'),'--build',str(build),
        '--output',str(M/'model'),'--prefix','1200','--selection','0,1,1,1','--scheduler-phases','observed']
    M.mkdir();(M/'argv.json').write_text(json.dumps(argv,indent=2)+'\n');start=time.monotonic()
    with(M/'process.log').open('wb')as log:p=subprocess.run(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    (M/'process-end.json').write_text(json.dumps(dict(exitCode=p.returncode,elapsedSeconds=time.monotonic()-start,completeGame=False))+'\n');assert p.returncode==0
    subprocess.run([sys.executable,'-X','utf8',str(R/'tools/th14-verify-native-campaign.py'),'--native',str(N),'--model',str(M/'model'),'--build',str(build),'--prefix','1200','--output',str(D/'raw-verified.json')],cwd=R,check=True)
    model=M/'model';camera=(N/'world-camera.raw').read_bytes();tail=(N/'world-camera-tail.u32').read_bytes();actual=(model/'full-camera.u32').read_bytes()
    assert len(camera)==1200*292 and len(tail)==1200*8 and len(actual)==1199*300
    for i in range(1,1200):assert actual[(i-1)*300:i*300]==camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]
    cursor=(N/'replay-cursor.u32').read_bytes();actual=(model/'replay-cursor.u32').read_bytes();assert len(cursor)==1200*56 and len(actual)==1199*16
    for i in range(1,1200):assert struct.unpack_from('<4I',actual,(i-1)*16)==tuple(struct.unpack_from('<I',cursor,i*56+j*4)[0]for j in [3,7,8,9])
    gate=json.loads((D/'raw-verified.json').read_bytes())
    result=dict(verifiedNativePreflight=True,callbacks=1200,nativeDebugExceptions=0,all32StateFieldsEqual=True,
        all75CameraWordsEqual=True,comparedCameraWords=1199*75,all4CursorFieldsEqual=True,all2HudFieldsEqual=True,
        vm303Rows=gate['vm303Rows'],combatCheckpoints=gate['combatCheckpoints'],orderedPublications=gate['orderedPublications'],
        observerSha256=native['sourceSha256'],nativeReportSha256=SHA((N/'report.json').read_bytes()),
        rawVerifierSha256=SHA((D/'raw-verified.json').read_bytes()),scriptReadWatchNotYetArmed=True,
        pendingDebugContextDeferrals=native['pendingDebugContextDeferrals'],
        originalStartupCauseProven=False,diagnosticPrefixOnly=True,independentTimingAccepted=False,completeGame=False,
        checkerSha256=SHA(Path(__file__).read_bytes()))
    (D/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
