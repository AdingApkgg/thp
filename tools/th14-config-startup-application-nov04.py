"""Run twelve bounded actual Application startup/Quit/save cases, then reload."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/config-startup-fallback-nov04'
K=R/'artifacts/th14/scene-camera-read-job-nov04/ordinary-full-exit'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
assert (H/'build/build.json').is_file() and not (H/'application-cases').exists()
home=H/'application-cases';home.mkdir()
native=json.loads((H/'native/native.json').read_bytes());default=bytes.fromhex(next(row['outputHex']for row in native['cases']if row['missing']))
cases=[('missing',None,default),('invalid-signature',b'\0'+default[1:],default),
       ('truncated',default[:-1],default),('oversized',default+b'\0',default),('empty',b'',default)]
for offset,limit in zip(range(0x1c,0x22),[2,3,2,6,3,3]):
    candidate=bytearray(default);candidate[offset]=limit;cases.append((f'option-{offset:02x}',bytes(candidate),default))
valid=bytes.fromhex(next(row['inputHex']for row in native['cases']if row['case']=='valid-user-options'))
cases.append(('valid-user-options',valid,valid));assert len(cases)==12
base=json.loads((H/'baseline-invalid-signature/argv.json').read_bytes());scenario=(H/'scenario.json').resolve();rows=[]

def execute(name,initial,expected,profile_present,invalid):
    folder=home/name;folder.mkdir()
    argv=list(base)
    for option,value in [('--build',H/'build'),('--output',folder/'gles'),('--scenario',scenario),('--initial-save',initial)]:argv[argv.index(option)+1]=str(value)
    (folder/'argv.json').write_text(json.dumps(argv,indent=2)+'\n')
    started=time.monotonic()
    with (folder/'process.log').open('wb')as log:
        child=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        (folder/'process-start.json').write_text(json.dumps(dict(pid=child.pid,startedUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),maximumWallSeconds=140))+'\n')
        try:code=child.wait(timeout=140)
        except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=20);code=-1
    (folder/'process-end.json').write_text(json.dumps(dict(exitCode=code,elapsedSeconds=time.monotonic()-started))+'\n')
    assert code==0,(name,(folder/'process.log').read_text(encoding='utf8')[-2000:])
    report=json.loads((folder/'gles/report.json').read_bytes());assert report['completed'] and not report['error'] and report['exitSaveCompleted']
    assert report['actions'][-1]['state'][0]==4 and report['physicalAudioDevicesOpened']==0
    actual=(folder/'gles/save/th14.cfg').read_bytes();assert actual==expected,name
    assert not any(p.name.endswith('.tmp')for p in (folder/'gles/save').iterdir())
    stdout=(folder/'gles/stdout.log').read_text(encoding='utf8');assert ('[config14] Invalid' in stdout)==invalid,name
    if profile_present:assert any(row.get('mode')=='rb'and row['virtual']=='/save/th14.cfg'for row in report['files'])
    row=dict(case=name,frames=report['frames'],configurationSha256=SHA(actual),
        configurationMatchesNativeResetOrValidInput=True,exitSaveCompleted=True,
        invalidConfigFallbackLogged=invalid,reportSha256=SHA((folder/'gles/report.json').read_bytes()),
        finalFiles=report['finalSave'],physicalAudioDevicesOpened=0)
    rows.append(row);print(json.dumps(dict(case=name,frames=row['frames'],passed=True)),flush=True)
    return folder

for name,candidate,expected in cases:
    initial=home/(name+'-input');initial.mkdir()
    if candidate is not None:(initial/'th14.cfg').write_bytes(candidate)
    execute(name,initial,expected,candidate is not None,candidate is not None and candidate!=valid)
    if candidate is not None:assert (initial/'th14.cfg').read_bytes()==candidate

initial=home/'valid-user-options/gles/save'
reload=execute('fresh-process-reload',initial,valid,True,False)
previous=json.loads((home/'valid-user-options/gles/report.json').read_bytes())
current=json.loads((reload/'gles/report.json').read_bytes())
assert current['initialSave']==previous['finalSave']==current['finalSave']
result=dict(verifiedActualApplicationConfigStartup=True,cases=rows,caseCount=len(rows),
    nativeComponentCases=len(native['cases']),freshProcessReloadAllFilesByteUnchanged=True,
    buildSha256=SHA((H/'build/build.json').read_bytes()),toolSha256=SHA(Path(__file__).read_bytes()),
    browserRun=False,browserAcceptance=False,ordinaryOriginalUiAcceptance=False,completeGame=False,nativeEquivalent=False)
(home/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(verifiedActualApplicationConfigStartup=True,cases=len(rows),freshProcessReload=True)),flush=True)
