"""Run the current renderer in the unchanged silent Application scenarios."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/gles-clip-portable-nov04'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['short','full'],required=True);a=p.parse_args()
D=H/('application-'+a.case+'-nov05');assert not D.exists();D.mkdir();sha=lambda raw:hashlib.sha256(raw).hexdigest()
parent=R/('artifacts/th14/scene-camera-read-job-nov04/application-argv.json'if a.case=='short'else'artifacts/th14/config-startup-fallback-nov04/full-flow/argv.json');argv=json.loads(parent.read_bytes());argv[argv.index('--build')+1]=str(H/'application-build-v2-nov05');argv[argv.index('--output')+1]=str(D/'gles')
host=Path(argv[3]);build=H/'application-build-v2-nov05/build.json';b=json.loads(build.read_bytes());assert b['compiled'] and b['coreObjectsReused']==141 and b['applicationObjectsRecompiled']==5
if a.case=='full':
    preflight=json.loads((H/'application-short-nov05/process-end.json').read_bytes());assert preflight['exitCode']==0
    report=json.loads((H/'application-short-nov05/gles/report.json').read_bytes());assert report['completed'] and not report['error'] and all(x['passed']for x in report['checks'])
(D/'argv.json').write_text(json.dumps(argv,indent=2)+'\n');(D/'plan.json').write_text(json.dumps(dict(case=a.case,parentArgvSha256=sha(parent.read_bytes()),wasmSha256=b['wasmSha256'],buildSha256=sha(build.read_bytes()),hostSha256=sha(host.read_bytes()),gameStateOverrides=False,physicalAudioDevicesOpened=0,browserAcceptance=False,completeGame=False),indent=2)+'\n')
start=time.monotonic();limit=340 if a.case=='short' else 3620
with(D/'process.log').open('wb')as log:
    child=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    (D/'process-start.json').write_text(json.dumps(dict(pid=child.pid,startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),timeoutSeconds=limit))+'\n')
    try:code=child.wait(timeout=limit)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=20);code=-1
result=dict(exitCode=code,elapsedSeconds=time.monotonic()-start);(D/'process-end.json').write_text(json.dumps(result)+'\n');print(json.dumps(result));sys.exit(code)
