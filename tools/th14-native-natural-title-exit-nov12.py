"""Prepare and monitor an isolated retail title->Quit run; input uses ordinary UI separately."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,ctypes as C,hashlib,json,os,shutil,struct,subprocess,time
from ctypes import wintypes as W
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-natural-title-exit-nov12';WORK=H/'work'
load=lambda p:json.loads(p.read_bytes())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');parser.add_argument('--output',type=Path);args=parser.parse_args();assert args.prepare!=args.run
if args.output:
 H=args.output.resolve();assert H.is_relative_to(R/'artifacts/th14');WORK=H/'work'
EXPECTED='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
controller_source_bytes=Path(__file__).read_bytes();controller_source_sha256=hashlib.sha256(controller_source_bytes).hexdigest()
CFG=WORK/'appdata/ShanghaiAlice/th14/th14.cfg'
if args.prepare:
 assert not H.exists() and shutil.disk_usage(R).free>=100*1024**3
 source=R/'artifacts/th14/player-entry-end-menu-nov06/campaign/work';cache=R/'artifacts/th14/shared-immutable-native-cache'
 assets=[]
 for name in ['th14.exe','th14.dat','thbgm.dat','util.dll']:
  original=source/name
  if name=='th14.dat':original=cache/'57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233.bin'
  digest=sha(original);canonical=cache/(digest+'.bin')
  assert canonical.exists() and os.path.samefile(original,canonical),name
  assets.append(dict(name=name,bytes=original.stat().st_size,sha256=digest,canonical=canonical.relative_to(R).as_posix()))
 assert assets[0]['sha256']==EXPECTED
 CFG.parent.mkdir(parents=True)
 for a in assets:os.link(R/a['canonical'],WORK/a['name'])
 data=bytearray((source/'appdata/ShanghaiAlice/th14/th14.cfg').read_bytes());assert struct.unpack_from('<I',data)[0]==0x140002
 data[0x22]=data[0x23]=0;data[0x39]&=~1;data[0x1f]=3;CFG.write_bytes(data)
 (H/'initial-config.bin').write_bytes(data)
 prepared=dict(executableSha256=EXPECTED,assets=assets,configSha256=sha(CFG),scoreInitiallyAbsent=True,assetPhysicalBytesCopied=0,noOriginalFilesWritten=True,gameStarted=False,debugger=False,instructionPatches=0,rngOrInputOrMemoryWrites=0,ordinaryUiInputRequired=True,maximumSeconds=180,completeGame=False,toolSha256=controller_source_sha256)
 (H/'prepared.json').write_text(json.dumps(prepared,indent=2)+'\n');print(json.dumps({k:v for k,v in prepared.items() if k!='assets'}));raise SystemExit
prepared=load(H/'prepared.json');assert controller_source_sha256==prepared['toolSha256']
(H/'controller-source-used.py').write_bytes(controller_source_bytes)
assert not (H/'process-start.json').exists()
# The current sequential GPU run must have been independently reaped first.
receipt=load(R/'artifacts/th14/option-call-roles-nov12/current/terminal-receipt.json');assert receipt['reaped'] and receipt['exitCode']==0
for a in prepared['assets']:assert sha(WORK/a['name'])==a['sha256'] and os.path.samefile(WORK/a['name'],R/a['canonical'])
assert sha(CFG)==prepared['configSha256'] and not (CFG.parent/'scoreth14.dat').exists()
other=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter \"Name = 'th14.exe'\").Count"],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert other.returncode==0 and other.stdout.strip()=='0',other.stdout+other.stderr
kernel=C.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];kernel.OpenProcess.restype=W.HANDLE
kernel.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];kernel.ReadProcessMemory.restype=W.BOOL
kernel.CloseHandle.argtypes=[W.HANDLE];kernel.CloseHandle.restype=W.BOOL
env={k:v for k,v in os.environ.items() if k.upper()!='APPDATA'};env['APPDATA']=str(WORK/'appdata')
process=subprocess.Popen([str(WORK/'th14.exe')],cwd=WORK,env=env)
start=dict(pid=process.pid,exe=str(WORK/'th14.exe'),onlyOwnCreatedProcess=True,startedUtc=datetime.now(timezone.utc).isoformat(),debugger=False,patchedInstructions=0,processMemoryWrites=0,threadSuspensions=0,uiInputInjectedByThisController=False)
(H/'process-start.json').write_text(json.dumps(start,indent=2)+'\n');print(json.dumps(start),flush=True)
handle=kernel.OpenProcess(0x1010,False,process.pid)
samples=[];initialization_samples=[];seen_zero=False;timed_out=False;error=None;began=time.monotonic()
def read(addr,size):
 data=C.create_string_buffer(size);count=C.c_size_t()
 if not kernel.ReadProcessMemory(handle,addr,data,size,C.byref(count)):return None
 assert count.value==size;return data.raw
try:
 assert handle,C.get_last_error()
 while process.poll() is None:
  if time.monotonic()-began>=prepared['maximumSeconds']:timed_out=True;process.terminate();break
  config=read(0x4d9134,0x5c);masters=read(0x4fd1ac,8)
  if config is not None and masters is not None and struct.unpack_from('<I',config)[0]==0x140002:
   music,effects=struct.unpack('<2i',masters)
   observation=dict(ms=int((time.monotonic()-began)*1000),musicConfig=config[0x22],effectsConfig=config[0x23],musicMaster=music,effectsMaster=effects)
   gate_path=H/'title-observed.json'
   if gate_path.exists():
    gate=load(gate_path);assert gate['pid']==process.pid and gate['actualTitleMainObserved'] and gate['source']=='CUA'
    assert all(observation[k]==0 for k in ['musicConfig','effectsConfig','musicMaster','effectsMaster']),'Nonzero levels after observed Main title'
    seen_zero=True;samples.append(observation)
   else:
    initialization_samples.append(observation)
  assert seen_zero or time.monotonic()-began<60,'Main-title quiet observation deadline'
  if len(samples)%20==0:(H/'progress.json').write_text(json.dumps(dict(pid=process.pid,live=True,elapsedSeconds=time.monotonic()-began,zeroMasterSamples=len(samples)))+'\n')
  time.sleep(.25)
except BaseException as e:
 error=repr(e)
 if process.poll() is None:process.terminate()
finally:
 code=process.wait(timeout=30)
 if handle:kernel.CloseHandle(handle)
 files={x.name:dict(bytes=x.stat().st_size,sha256=sha(x)) for x in CFG.parent.iterdir() if x.is_file()}
 immutable_exact=all(sha(WORK/a['name'])==a['sha256'] for a in prepared['assets'])
 report=dict(start,initializationLevelSamples=len(initialization_samples),startupDefaultLevelsNotInterpretedAsAppliedSettings=True,quietGateRequiresActualTitleUiObservation=True,immutableAssetsUnchanged=immutable_exact,quietRuntimeMeasured=len(samples)>=2,exitCode=code,reaped=True,elapsedSeconds=time.monotonic()-began,observerTerminationRequested=bool(timed_out or error),timedOut=timed_out,error=error,naturalOsExitObserved=not timed_out and error is None and code==0,actualZeroMasterSamples=len(samples),finalFiles=files,ordinaryQuitUiEvidencePending=True,saveBytesComparisonPending=True,completeGame=False,toolSha256=controller_source_sha256)
 (H/'initialization-level-samples.json').write_text(json.dumps(initialization_samples,indent=2)+'\n')
 (H/'master-samples.json').write_text(json.dumps(samples,indent=2)+'\n');(H/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if not report['naturalOsExitObserved']:raise SystemExit(1)
