"""Observe one TH14 MarisaB Lunatic native beam caller with two hardware traps.

Only an owned hidden, silent child is used. A private archive carries the
intact replay as demo0; one declared attract-bit clear follows first Player.
No instruction, RNG, score, health or input writes. Existing immutable cache
is required, so this observer never copies the original game assets.
"""
from pathlib import Path
import argparse,ctypes as C,struct,json,os,time,hashlib,importlib.util,shutil,subprocess,traceback
from ctypes import wintypes as W
R=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--config',type=Path,required=True);opt=parser.parse_args();O=opt.output.resolve();assert O.is_relative_to(R/'artifacts/th14');O.mkdir(exist_ok=False);work=O/'work';work.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
types=module('native_types',R/'tools/th14-native-session-capture.py');storage=module('storage',R/'tools/th14-test-storage.py');target=json.loads((R/'runtimes/th14/target.json').read_bytes());original=Path(target['executable']).parent;asset=opt.assets.resolve();assetMeta=json.loads((asset/'manifest.json').read_bytes());assert assetMeta['replaySha256']=='e452a97814aecdb9480540761dfaed979c865be62d57a32a616720a6114913af';assert assetMeta['unchangedEntries']==226 and assetMeta['changedEntries']==['demo0.rpy'];manifest=[]
assert shutil.disk_usage(R).free>4*1024**3
for name in ['th14.exe','th14.dat','thbgm.dat','util.dll']:
 p=asset/name if name=='th14.dat'else original/name;h=sha(p);assert (storage.CACHE/(h+'.bin')).is_file(),'No asset duplication: immutable cache missing '+name;assert storage.clone_immutable(p,work/name)==h;assert not os.path.samefile(original/name,work/name);manifest.append({'name':name,'sha256':h,'bytes':p.stat().st_size,'newAssetBytesCopied':0})
assert manifest[0]['sha256']==types.EXPECTED_EXE
config=bytearray(opt.config.read_bytes());config[0x22]=config[0x23]=0;config[0x39]&=~1;config[0x1f]=3;appdata=work/'appdata';cfg=appdata/'ShanghaiAlice/th14';cfg.mkdir(parents=True);(cfg/'th14.cfg').write_bytes(config)
probe=subprocess.run(['powershell','-NoProfile','-Command','@(Get-CimInstance Win32_Process -Filter "Name = \'th14.exe\'").Count'],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW);assert probe.returncode==0 and probe.stdout.strip()=='0','Existing original game; do not attach or interfere'
k=C.WinDLL('kernel32',use_last_error=True)
sigs={'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),'WaitForDebugEvent':([C.POINTER(types.DebugEvent),W.DWORD],W.BOOL),'ContinueDebugEvent':([W.DWORD,W.DWORD,W.DWORD],W.BOOL),'ReadProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),'WriteProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),'Wow64GetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),'Wow64SetThreadContext':([W.HANDLE,C.c_void_p],W.BOOL),'SuspendThread':([W.HANDLE],W.DWORD),'ResumeThread':([W.HANDLE],W.DWORD),'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),'CloseHandle':([W.HANDLE],W.BOOL)}
for name,(args,res)in sigs.items():getattr(k,name).argtypes=args;getattr(k,name).restype=res
def check(ok):
 if not ok:raise C.WinError(C.get_last_error())
pi=types.ProcessInfo();si=types.Startup();si.cb=C.sizeof(si);si.flags=1;si.show=0;env={a:b for a,b in os.environ.items()if a.upper()!='APPDATA'};env['APPDATA']=str(appdata);envBlock=C.create_unicode_buffer('\0'.join(a+'='+b for a,b in sorted(env.items(),key=lambda x:x[0].upper()))+'\0\0');exe=str(work/'th14.exe');check(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,2|0x400,envBlock,str(work),C.byref(si),C.byref(pi)))
handles={pi.process,pi.thread};threads={};first=None;caller=None;armed=False;exited=False;err=None;started=time.monotonic();lastPrint=0;samples=[];exceptions=[];writes=[];breakpoints=0;stage3ClockObserved=False
(O/'process-start.json').write_text(json.dumps({'pid':pi.pid,'observerPid':os.getpid(),'hidden':True,'silent':True,'maximumSeconds':900,'captureGoal':'first actual original circular beam fallback in stage3 window2140..2200','manifest':manifest,'configHex':config.hex(),'noPerFrameDebugTrace':True,'completeGame':False},indent=2)+'\n');print(json.dumps({'nativePid':pi.pid,'observerPid':os.getpid(),'phase':'started','silent':True}),flush=True)
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t();check(k.ReadProcessMemory(pi.process,p,b,n,C.byref(got)));assert got.value==n;return b.raw
def u32(p):return struct.unpack('<I',read(p,4))[0]
def context(h):
 b=C.create_string_buffer(716);struct.pack_into('<I',b,0,0x10017);check(k.Wow64GetThreadContext(h,b));return b
def setbp(h,address,current=False):
 b=context(h);struct.pack_into('<6I',b,4,address,0,0,0,0,1 if address else 0)
 if current:struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]|0x10000)
 check(k.Wow64SetThreadContext(h,b))
def sample():
 control=u32(0x4db558);stage=u32(0x4f58a4);g=struct.unpack('<32I',read(0x4f5828,128));player=u32(0x4db67c);row={'seconds':time.monotonic()-started,'stage':stage,'frame':u32(control+0x14)if control else None,'controlFlags':u32(control+0x80)if control else None,'scoreUnits':g[2],'graze':g[6],'pointValue':g[9],'lifeFragments':g[16],'lives':g[15],'power':g[12],'player':player}
 if player:
  try:row.update(x=u32(player+0x5ec),y=u32(player+0x5f0),lifeState=u32(player+0x684))
  except OSError:row['playerReadDuringTransition']=True
 return row
try:
 while time.monotonic()-started<900 and caller is None and not exited:
  ev=types.DebugEvent()
  if not k.WaitForDebugEvent(C.byref(ev),100):
   code=C.get_last_error()
   if code!=121:raise C.WinError(code)
   if first is None:
    if time.monotonic()-started>180:raise TimeoutError('No first Player within180sec')
    continue
   try:row=sample()
   except OSError:continue
   if row['stage']==3 and row['frame']is not None and row['frame']<1000:stage3ClockObserved=True
   if stage3ClockObserved and row['stage']==3 and row['frame']is not None and 2140<=row['frame']<=2200 and not armed:
    assert k.SuspendThread(pi.thread)!=0xffffffff
    try:setbp(pi.thread,0x45286f)
    finally:assert k.ResumeThread(pi.thread)!=0xffffffff
    armed=True;row['beamBreakpointArmed']=True;print(json.dumps(row),flush=True)
   if row['stage']>=4 or(stage3ClockObserved and row['stage']==3 and row['frame']is not None and row['frame']>2200):raise RuntimeError('Passed requested native window without caller observation')
   if time.monotonic()-lastPrint>=30:
    lastPrint=time.monotonic();samples.append(row);(O/'progress.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
   continue
  status=0x10002
  try:
   assert ev.pid==pi.pid
   if ev.kind==3:
    assert ev.data.create_process.base==0x400000;h=ev.data.create_process.thread;threads[ev.tid]=h;handles.update([h,ev.data.create_process.process]);setbp(h,0x44dbd0)
    if ev.data.create_process.file:k.CloseHandle(ev.data.create_process.file)
   elif ev.kind==2:
    h=ev.data.create_thread.thread;handles.add(h)
    if 0x400000<=ev.data.create_thread.start<0x500000:threads[ev.tid]=h;setbp(h,0x44dbd0 if first is None else 0)
   elif ev.kind==4:threads.pop(ev.tid,None)
   elif ev.kind==6:
    if ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
   elif ev.kind==5:exited=True
   elif ev.kind==1:
    x=ev.data.exception.record;pc=int(x.address or 0)
    if x.code in (0x80000004,0x4000001e) and pc==0x44dbd0 and first is None:
     breakpoints+=1;first=sample();g=struct.unpack('<4I',read(0x4f5828,16));assert(g[0],g[1],g[3],first['stage'])==(1,1,3,1);flags=u32(0x4f58b8);replay=u32(0x4db688);assert flags&0x40 and u32(replay+0x10)==1;payload=C.create_string_buffer(struct.pack('<I',flags&~0x40));written=C.c_size_t();check(k.WriteProcessMemory(pi.process,0x4f58b8,payload,4,C.byref(written)));assert written.value==4;writes.append({'address':0x4f58b8,'before':flags,'after':flags&~0x40,'attractBitClearOnly':True})
     for tid,h in threads.items():
      if k.WaitForSingleObject(h,0)==0x102:setbp(h,0,current=tid==ev.tid)
     (O/'first-player.json').write_text(json.dumps(first,indent=2)+'\n');print(json.dumps({'phase':'first-player','sample':first,'perFrameDebuggingDisabled':True}),flush=True)
    elif x.code in (0x80000004,0x4000001e) and pc==0x45286f and armed:
     breakpoints+=1;b=context(threads.get(ev.tid,pi.thread));regs={name:struct.unpack_from('<I',b,at)[0]for name,at in [('edi',156),('esi',160),('ebp',180),('eip',184),('esp',196)]};shot=regs['edi'];area=u32(shot+0xc0);caller={'sample':sample(),'pc':pc,'threadId':ev.tid,'registers':regs,'scratchBits':u32(regs['esp']+0x2c),'scratchAddress':regs['esp']+0x2c,'shotHex':read(shot,0xd0).hex(),'areaHex':read(area,0xa4).hex(),'targetHex':read(regs['esi'],12).hex(),'stackHex':read(regs['esp'],128).hex(),'readOnly':True};setbp(threads.get(ev.tid,pi.thread),0,True);(O/'native-caller.json').write_text(json.dumps(caller,indent=2)+'\n');print(json.dumps({'phase':'captured-caller','frame':caller['sample']['frame'],'scratchBits':caller['scratchBits']}),flush=True)
    elif x.code in (0x80000003,0x4000001f):pass
    else:status=0x80010001;exceptions.append({'code':int(x.code),'pc':pc,'firstChance':ev.data.exception.first_chance})
  finally:check(k.ContinueDebugEvent(ev.pid,ev.tid,status))
 if caller is None and not err:err='Requested caller not observed before time/process bound'
except BaseException as e:err=repr(e);(O/'exception.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
 if not exited:
  k.TerminateProcess(pi.process,0);deadline=time.monotonic()+5
  while time.monotonic()<deadline:
   ev=types.DebugEvent()
   if not k.WaitForDebugEvent(C.byref(ev),100):continue
   if ev.kind==6 and ev.data.dll.file:k.CloseHandle(ev.data.dll.file)
   k.ContinueDebugEvent(ev.pid,ev.tid,0x10002)
   if ev.kind==5:exited=True;break
 for h in handles:
  if h:k.CloseHandle(h)
 q={'passed':caller is not None and not err and exited,'error':err,'childExited':exited,'firstPlayerObserved':first is not None,'callerObserved':caller is not None,'breakpointHits':breakpoints,'stage3ClockObserved':stage3ClockObserved,'writes':writes,'rngScoreHealthOrInputWrites':0,'originalInstructionsPatched':0,'silent':True,'hidden':True,'elapsedSeconds':time.monotonic()-started,'samples':samples,'exceptions':exceptions,'diagnosticTermination':True,'naturalReplayEndClaimed':False,'sourceReplaySha256':assetMeta['replaySha256'],'originalExeSha256':types.EXPECTED_EXE,'sourceSha256':sha(Path(__file__)),'maximumCaptureBytes':1024*1024,'newAssetBytesCopied':0,'originalCallerStackValidated':caller is not None,'completeGame':False};(O/'report.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items()if k not in ['samples','exceptions']}),flush=True)

raise SystemExit(0 if q["passed"] else 1)
