"""Reload a retained nondefault browser score through the current Application."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/config-startup-fallback-nov04'
O=H/'persisted-score-readback';SHA=lambda raw:hashlib.sha256(raw).hexdigest()
assert not O.exists();initial=O/'initial-save';initial.mkdir(parents=True)
source=R/'artifacts/th14/native-frame-readback-oct28/browser-startup/persisted-score/browser-export.dat'
score=source.read_bytes();assert len(score)==21656 and SHA(score)=='ed92a752b5fc74288a87d74588a94b5292fbc2a69ef1b5394590693012dce50d'
config_source=H/'application-cases/valid-user-options-input/th14.cfg';config=config_source.read_bytes();assert len(config)==92 and config[0x22:0x24]==bytes([37,53])
(initial/'scoreth14.dat').write_bytes(score);(initial/'th14.cfg').write_bytes(config)
argv=json.loads((H/'application-cases/valid-user-options/argv.json').read_bytes())
for option,value in [('--output',O/'gles'),('--initial-save',initial)]:argv[argv.index(option)+1]=str(value)
(O/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
started=time.monotonic()
with (O/'process.log').open('wb')as log:
    child=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    (O/'process-start.json').write_text(json.dumps(dict(pid=child.pid,startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),maximumSeconds=140))+'\n')
    try:code=child.wait(timeout=140)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=20);code=-1
(O/'process-end.json').write_text(json.dumps(dict(exitCode=code,elapsedSeconds=time.monotonic()-started))+'\n');assert code==0
run=json.loads((O/'gles/report.json').read_bytes());assert run['completed'] and not run['error'] and run['exitSaveCompleted']
assert run['actions'][-1]['state'][0]==4 and run['frames']==444 and run['physicalAudioDevicesOpened']==0
assert run['initialSave']==run['finalSave']
assert (O/'gles/save/scoreth14.dat').read_bytes()==score and (O/'gles/save/th14.cfg').read_bytes()==config
assert source.read_bytes()==score and config_source.read_bytes()==config
assert any(row.get('mode')=='rb' and row['virtual']=='/save/scoreth14.dat'for row in run['files'])
result=dict(verifiedActualApplicationNondefaultScoreReadback=True,applicationSourceCommit='ae284631c2ebaf4006eb8b17662bc5caeeb6da5c',
    wasmSha256=run['wasmSha256'],frames=444,scoreBytes=len(score),scoreSha256=SHA(score),configBytes=92,configSha256=SHA(config),
    sourceScore=source.relative_to(R).as_posix(),sourceConfig=config_source.relative_to(R).as_posix(),
    initialAndFinalScoreAndConfigByteUnchanged=True,productionSaveAfterOrdinaryQuit=True,physicalAudioDevicesOpened=0,
    reportSha256=SHA((O/'gles/report.json').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
    scope='Current C++ Application cold load and ordinary normalized Main/Quit/save of a retained real browser score containing nondefault ReimuA Normal records, with nondefault volume config. No browser or IndexedDB execution in this run.',
    browserAcceptance=False,completeGame=False,nativeEquivalent=False)
(O/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
