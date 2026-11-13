"""Owned silent native replay with a bounded in-process entry logger.

No debugger is attached, and no thread is suspended after initial ResumeThread.
The observer is an explicitly declared six-byte entry detour in the private
process image. Original files remain unchanged. This is not a patch-free run.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,importlib.util,json,os,struct,subprocess,sys,time
from ctypes import wintypes as W
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/ordinary-replay-native-nov13';PRIOR=R/'artifacts/th14/player-entry-logger-v2-nov06';SHA=lambda b:hashlib.sha256(b).hexdigest()
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def run(case):
 logger=module('logger',R/'tools/th14_player_logger_x86_nov06.py');component_path=PRIOR/'component-hud-fixed/verified.json';component_raw=component_path.read_bytes();component=json.loads(component_raw)
 assert component['componentVerified']and component['cases']==40 and component['recorderBase']==0x50000000
 assert SHA((R/'tools/th14_player_logger_x86_nov06.py').read_bytes())==component['generatorSha256']
 boot_logger=None;boot_component=None
 if case=='startup':
  boot_logger=module('bootlogger',R/'tools/th14_boot_counter_logger_x86_nov06.py');boot_component=json.loads((R/'artifacts/th14/player-entry-logger-nov06/boot-component/verified.json').read_bytes())
  assert boot_component['componentVerified']and boot_component['cases']==54 and boot_component['base']==0x50000000
  assert SHA((R/'tools/th14_boot_counter_logger_x86_nov06.py').read_bytes())==boot_component['generatorSha256']
 if case in ('prefix','stage3-prefix','campaign'):assert json.loads((PRIOR/'preflight/verified.json').read_bytes())['nativeEntryLoggerVerified']
 if case in ('stage3-prefix','campaign'):assert json.loads((PRIOR/'prefix/verified.json').read_bytes())['nativeEntryLoggerVerified']
 if case=='campaign':assert json.loads((PRIOR/'stage3-prefix/verified.json').read_bytes())['nativeEntryLoggerVerified']
 home=H/case;home.mkdir();work=home/'work';work.mkdir();observer_source=Path(__file__).read_bytes();(home/'observer-source.py').write_bytes(observer_source);(home/'logger-generator.py').write_bytes((R/'tools/th14_player_logger_x86_nov06.py').read_bytes())
 count,seconds=1500,75
 storage=module('storage',R/'tools/th14-test-storage.py');storage.check_budget(home,100*1024**3,256*1024**2)
 original=Path(json.loads((R/'runtimes/th14/target.json').read_bytes())['executable']).parent
 asset=R/'artifacts/th14/native-campaign-assets'/'57d84a5cbe82-ce8c38538b73';manifest_raw=(asset/'manifest.json').read_bytes();asset_report=json.loads(manifest_raw)
 assert asset_report['passed']and asset_report['changedEntries']==['demo0.rpy']and asset_report['unchangedEntries']==226
 assert storage.sha256_file(original/'th14.dat')==asset_report['originalArchiveSha256']
 assert storage.sha256_file(Path(asset_report['replayPath']))==asset_report['replaySha256']
 files=[]
 for name in ['th14.exe','th14.dat','thbgm.dat','util.dll']:
  source=asset/name if name=='th14.dat'else original/name;target=work/name
  if name=='th14.dat':os.link(source,target);digest=storage.sha256_file(source)
  else:digest=storage.clone_immutable(source,target)
  if source.parent==original:assert not os.path.samefile(source,target)
  files.append(dict(name=name,bytes=target.stat().st_size,sha256=digest))
 assert files[0]['sha256']==component['originalExecutableSha256']
 assert files[1]['sha256']==asset_report['referenceArchiveSha256']
 cfg=bytearray((R/'artifacts/th14/combat-pool-oct25/native-config.bin').read_bytes());cfg[0x22]=cfg[0x23]=0;cfg[0x39]&=~1;cfg[0x1f]=3
 appdata=work/'appdata';cfgdir=appdata/'ShanghaiAlice/th14';cfgdir.mkdir(parents=True);(cfgdir/'th14.cfg').write_bytes(cfg)
 types=module('native_types',R/'tools/th14-native-session-capture.py');k=C.WinDLL('kernel32',use_last_error=True)
 signatures={
  'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(types.Startup),C.POINTER(types.ProcessInfo)],W.BOOL),
  'ReadProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
  'WriteProcessMemory':([W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)],W.BOOL),
  'VirtualAllocEx':([W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,W.DWORD],C.c_void_p),
  'VirtualProtectEx':([W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)],W.BOOL),
  'FlushInstructionCache':([W.HANDLE,C.c_void_p,C.c_size_t],W.BOOL),
  'ResumeThread':([W.HANDLE],W.DWORD),'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),
  'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),'GetExitCodeProcess':([W.HANDLE,C.POINTER(W.DWORD)],W.BOOL),'CloseHandle':([W.HANDLE],W.BOOL)}
 for name,(args,result)in signatures.items():getattr(k,name).argtypes=args;getattr(k,name).restype=result
 def checked(ok):
  if not ok:raise C.WinError(C.get_last_error())
 existing=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter \"Name = 'th14.exe'\").Count"],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert existing.returncode==0 and existing.stdout.strip()=='0','Another original TH14 process exists'
 env={key:value for key,value in os.environ.items()if key.upper()!='APPDATA'};env['APPDATA']=str(appdata)
 block=C.create_unicode_buffer('\0'.join(f'{key}={value}'for key,value in sorted(env.items(),key=lambda p:p[0].upper()))+'\0\0')
 si,pi=types.Startup(),types.ProcessInfo();si.cb=C.sizeof(si);si.flags=1;si.show=0;exe=str(work/'th14.exe')
 checked(k.CreateProcessW(exe,C.create_unicode_buffer('"'+exe+'"'),None,None,False,4|0x400,block,str(work),C.byref(si),C.byref(pi)))
 (home/'process-start.json').write_text(json.dumps(dict(pid=pi.pid,mainThreadId=pi.tid,onlyOwnCreatedProcess=True,createdSuspended=True,debuggerAttached=False,hiddenRequested=True))+'\n')
 print(json.dumps(dict(nativeChildStarted=True,pid=pi.pid,debuggerAttached=False,configuredSilent=True)),flush=True)
 def read(address,size):
  data=C.create_string_buffer(size);got=C.c_size_t();checked(k.ReadProcessMemory(pi.process,address,data,size,C.byref(got)));assert got.value==size;return data.raw
 def write(address,data):
  buf=C.create_string_buffer(data);done=C.c_size_t();checked(k.WriteProcessMemory(pi.process,address,buf,len(data),C.byref(done)));assert done.value==len(data)
 allocation=0;error='';stopped='setup';resumed=False;child_exited=False;counter=0;header=b'';rows=b'';boot_rows=b'';boot=None;started=time.monotonic();end_code=None
 early_profile_saved=False;final_eof_seen=False;final_eof_counter=0;terminal_samples=[];last_terminal_check=0
 try:
  assert read(logger.ENTRY,6)==logger.DISPLACED
  base=0x50000000;size=(logger.ROWS+logger.STRIDE*count+4095)&~4095
  if boot_logger:size=max(size,boot_logger.ROW_OFFSET+boot_logger.CAPACITY*boot_logger.STRIDE)
  allocation=k.VirtualAllocEx(pi.process,base,size,0x3000,4);assert allocation==base,'Qualified recorder address unavailable'
  built=logger.build(base);assert SHA(built['code'])==component['loggerSha256'];write(base,built['code']);write(built['header']+4,struct.pack('<I',count));write(built['header']+16,struct.pack('<I',pi.tid))
  if boot_logger:
   boot=boot_logger.build(base);assert SHA(boot['code'])==boot_component['loggerSha256']and read(boot_logger.ENTRY,6)==boot_logger.DISPLACED
   write(boot['address'],boot['code']);write(built['header']+68,struct.pack('<I',boot['capacity']))
  old=W.DWORD();checked(k.VirtualProtectEx(pi.process,base,logger.HEADER,0x20,C.byref(old)))
  original_page=W.DWORD();checked(k.VirtualProtectEx(pi.process,logger.ENTRY,6,0x40,C.byref(original_page)));write(logger.ENTRY,built['detour'])
  restored=W.DWORD();checked(k.VirtualProtectEx(pi.process,logger.ENTRY,6,original_page.value,C.byref(restored)))
  if boot:
   checked(k.VirtualProtectEx(pi.process,boot['entry'],6,0x40,C.byref(original_page)));write(boot['entry'],boot['detour'])
   checked(k.VirtualProtectEx(pi.process,boot['entry'],6,original_page.value,C.byref(restored)));checked(k.FlushInstructionCache(pi.process,boot['entry'],6))
  checked(k.FlushInstructionCache(pi.process,base,len(built['code'])));checked(k.FlushInstructionCache(pi.process,logger.ENTRY,6))
  if boot:checked(k.FlushInstructionCache(pi.process,boot['address'],len(boot['code'])))
  # In the suspended image, verify that the detour is the only text change.
  image=module('image',R/'tools/th14-loading-lifecycle-evidence-check.py').Image();section=image.sections[0];text_address=image.base+section['rva']
  original_text=image.data[section['raw']:section['raw']+section['rawSize']];expected=bytearray(original_text);offset=logger.ENTRY-text_address;expected[offset:offset+6]=built['detour']
  if boot:expected[boot['entry']-text_address:boot['entry']-text_address+6]=boot['detour']
  assert read(text_address,len(expected))==expected
  plan=dict(maximumCallbacks=count,maximumSeconds=seconds,recorderBytes=size,loggerBytes=len(built['code']),loggerSha256=SHA(built['code']),
   displacedOriginalInstructionsBytes=6,gameStackPreservedByPrivateStack=True,debuggerAttached=False,afterResumeThreadSuspensions=0,
   componentSha256=SHA(component_raw),generatorSha256=component['generatorSha256'],textOnlyChangeVerifiedBeforeResume=True,bootDrawCounterLogger=bool(boot),
   bootGeneratorSha256=boot_component['generatorSha256']if boot else None,physicalAudioRequested=False,
   stopAfterFinalReplayInputEofAndQuiet=False,stopAfterStableForcedReplayEndMenu=True,terminalPredicateSource='tools/th14-native-campaign-observer-oct25.py',terminalSamplesRequired=3,quietSecondsBeforeTerminalReads=3,finalStage=1,finalEofQuietSeconds=2 if case=='campaign'else 0,completeGame=False)
  (home/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
  result=k.ResumeThread(pi.thread);assert result==1;resumed=True;started=time.monotonic();last_progress=0
  last_counter=0;last_counter_change=started
  def first_profile(data,head):
   words=struct.unpack('<132I',data);values=struct.unpack('<16I',head)
   return dict(words=list(words[1:33]),actualInitialTimeGetTimeInput=values[2],actualOriginalSecurityCookie=values[3],
    attractFlags=values[6],caseFlagsAfter=values[7],originalPlayerEntryStack=words[130],clockInputsReadOnly=True,inProcessEntryLogger=True)
  def terminal_sample():
   # Existing qualified native observer's forced Replay End predicate.
   # Read only after Player rows have been quiet; reject changing owners.
   u32=lambda a:struct.unpack('<I',read(a,4))[0]
   owners=[u32(a)for a in(0x4db678,0x4db688,0x4db558)]
   pause,replay,control=owners
   if not all(owners):return None
   words=list(struct.unpack('<2I',read(pause,8)));forced=u32(pause+0x108);disabled_count=u32(pause+0x10c)
   cursor=u32(pause+0x38);menu_count=u32(pause+0x40);flags=u32(control+0x80);mode=u32(replay+0x10)
   if words!=[2,3]or forced!=1 or disabled_count!=3 or cursor!=1 or menu_count!=5 or not(flags&0x10)or mode!=1:return None
   disabled=[u32(pause+0xc8+i*4)for i in range(3)]
   if disabled!=[3,2,0]or owners!=[u32(a)for a in(0x4db678,0x4db688,0x4db558)]:return None
   return dict(hostMonotonicNs=time.monotonic_ns(),callbacks=counter,stage=u32(0x4f58a4),owners=owners,pauseWords=words,forcedExit=forced,disabledCount=disabled_count,disabledEntries=disabled,cursor=cursor,menuCount=menu_count,controlFlags=flags,replayMode=mode)
  while True:
   status=k.WaitForSingleObject(pi.process,0)
   if status==0:stopped='child-exit-before-limit';child_exited=True;break
   assert status==0x102
   header=read(built['header'],64);counter,capacity,ticks,cookie,tid,foreign=struct.unpack_from('<6I',header);assert capacity==count and counter<=count
   assert not foreign,'Unexpected thread called the single-main-thread recorder'
   elapsed=time.monotonic()-started
   if counter and not early_profile_saved:
    first_bytes=(json.dumps(first_profile(read(built['rows'],logger.STRIDE),header),indent=2)+'\n').encode()
    (home/'untouched-first-player.json').write_bytes(first_bytes);early_profile_saved=True
   if counter!=last_counter:
    last_counter=counter;last_counter_change=time.monotonic()
   if case=='campaign' and counter:
    # Read only an already-published private row, never a game's transient
    # pointer graph. End-of-input and quiet callbacks are not a GUI claim.
    tail=struct.unpack('<132I',read(built['rows']+(counter-1)*logger.STRIDE,logger.STRIDE))
    if tail[31]==6 and tail[113]==6 and tail[117]>=tail[119] and tail[119]>0:
     if not final_eof_seen:final_eof_seen=True;final_eof_counter=counter
    # EOF is observed separately, never required for forced Replay End.
    pass
   if counter>=300 and time.monotonic()-last_counter_change>=3 and time.monotonic()-last_terminal_check>=.25:
    last_terminal_check=time.monotonic()
    try:sample=terminal_sample()
    except OSError:sample=None
    if sample is None:terminal_samples.clear()
    else:
     terminal_samples.append(sample)
     recent=terminal_samples[-3:]
     if len(recent)==3 and len({r['callbacks']for r in recent})==1 and len({tuple(r['owners'])for r in recent})==1 and (case!='campaign'or all(r['stage']==6 for r in recent)):
      stopped='stable-forced-replay-end-menu-observed';break
   if counter>=count:stopped='declared-callback-limit';break
   if elapsed>seconds:stopped='declared-wall-limit';break
   if not counter and elapsed>90:stopped='declared-startup-limit';break
   if time.monotonic()-last_progress>=10:
    storage.check_budget(home,100*1024**3,256*1024**2);progress=dict(pid=pi.pid,callbacks=counter,elapsedSeconds=elapsed,terminal=False,completeGame=False)
    (home/'progress.json').write_text(json.dumps(progress)+'\n');print(json.dumps(progress),flush=True);last_progress=time.monotonic()
   time.sleep(.02)
  if not child_exited:
   rows=read(built['rows'],counter*logger.STRIDE)
   if boot:
    boot_count=struct.unpack('<I',read(built['header']+64,4))[0];assert boot_count<=boot['capacity'];boot_rows=read(boot['rows'],boot_count*boot['stride'])
 except BaseException as exc:
  import traceback
  error=repr(exc);(home/'exception.txt').write_text(traceback.format_exc(),encoding='utf8');stopped='observer-failure'
 finally:
  if k.WaitForSingleObject(pi.process,0)==0x102:checked(k.TerminateProcess(pi.process,0));assert k.WaitForSingleObject(pi.process,5000)==0
  code=W.DWORD();checked(k.GetExitCodeProcess(pi.process,C.byref(code)));end_code=code.value;child_exited=True
  k.CloseHandle(pi.thread);k.CloseHandle(pi.process)
 elapsed=time.monotonic()-started
 selected=bytearray();camera=bytearray();tail=bytearray();hud=bytearray();cursor=bytearray();tsc=bytearray();first=None
 for index in range(len(rows)//logger.STRIDE):
  data=rows[index*logger.STRIDE:(index+1)*logger.STRIDE];words=struct.unpack('<132I',data);assert words[0]==index+1 and words[128]==pi.tid
  selected.extend(data[4:33*4]);camera.extend(data[33*4:106*4]);tail.extend(data[106*4:108*4]);hud.extend(data[108*4:110*4]);cursor.extend(data[110*4:124*4]);tsc.extend(data[124*4:128*4])
  if first is None:first=first_profile(data,header)
 assert len(rows)//logger.STRIDE==counter
 payload={'selected-state.u32':selected,'world-camera.raw':camera,'world-camera-tail.u32':tail,'hud-score.u32':hud,'replay-cursor.u32':cursor,'player-tsc-range.u64':tsc,'logger-rows.u32':rows}
 for name,data in payload.items():(home/name).write_bytes(data)
 if boot:(home/'boot-draw-counter.u32').write_bytes(boot_rows)
 if first:
  profile_bytes=(json.dumps(first,indent=2)+'\n').encode();profile_path=home/'untouched-first-player.json'
  if profile_path.exists():assert profile_path.read_bytes()==profile_bytes
  else:profile_path.write_bytes(profile_bytes)
 assert storage.sha256_file(work/'th14.exe')==files[0]['sha256']
 report=dict(schema='th14/native-in-process-player-entry/1',pid=pi.pid,mainThreadId=pi.tid,childExited=child_exited,childExitCode=end_code,error=error,debugErrors=[],callbacks=counter,
  stoppedBy=stopped,elapsedSeconds=elapsed,files=files,executableSha256=files[0]['sha256'],referenceArchiveManifestSha256=SHA(manifest_raw),sourceFullReplaySha256=asset_report['replaySha256'],
  selectedSha256=SHA(selected),worldCameraSha256=SHA(camera),worldCameraTailSha256=SHA(tail),hudScoreSha256=SHA(hud),replayCursorSha256=SHA(cursor),loggerRowsSha256=SHA(rows),
  inProcessPlayerEntryLogger=True,debuggerAttached=False,hardwareBreakpointsOnly=False,instructionBytesPatched=12 if boot else 6,originalDiskFilesChanged=False,
  bootDrawCounterLogger=bool(boot),bootDrawRows=len(boot_rows)//64,bootDrawRowsSha256=SHA(boot_rows)if boot else None,
  privateObserverStack=True,originalDisplacedPrologueReplayed=True,componentSha256=SHA(component_raw),generatorSha256=component['generatorSha256'],
  configuredMusicAndSoundVolumeZero=True,hiddenWindowRequested=True,caseInitialization=dict(attractBitClearOnly=bool(first and first['attractFlags']&0x40 and first['caseFlagsAfter']==first['attractFlags']&~0x40)),
  rngOrCounterWrites=0,worldCameraAll75WordsCaptured=True,transitionSleepRngVmBreakpointsEnabled=False,replayRngStoreEvents=0,
  callbackRowsNotAtomicAcrossThreads=True,originalSchedulingAccepted=False,uninstrumentedTimingAccepted=False,observedForcedReplayEndMenu=stopped=='stable-forced-replay-end-menu-observed',terminalMenuSamples=terminal_samples,observerTerminationAfterStableMenu=True,originalProcessNaturalExitClaimed=False,
  finalReplayInputEofObserved=case=='campaign'and final_eof_seen,finalReplayInputEofFirstCallback=final_eof_counter if case=='campaign'else None,
  finalReplayInputEofQuietSeconds=2 if case=='campaign'and final_eof_seen else 0,earlyOneTimeInputProfilePublished=early_profile_saved,
  sourceSha256=SHA(observer_source),completeGame=False,nativeEquivalent=False)
 (home/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(terminal=True,callbacks=counter,stoppedBy=stopped,childExited=child_exited,error=error,completeGame=False)),flush=True)
 assert not error and stopped=='stable-forced-replay-end-menu-observed'and len(terminal_samples)>=3
 if case=='campaign':assert counter>100000
 else:assert case=='end-menu-preflight'and counter==345
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=['end-menu-preflight','campaign'],required=True);args=p.parse_args();run(args.case)
