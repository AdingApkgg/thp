"""Real Application/device integration on a silent standalone EGL/WASI host.

This is a native component test, without a browser, DOM or application inputs.
The platform provides explicit clocks, async callback delivery and private files.
"""
from pathlib import Path, PurePosixPath
import argparse
import shutil
import collections
import ctypes as C
import hashlib
import heapq
import importlib.util
import json
import struct
import time
import sys

R=Path(__file__).resolve().parents[1]
tool_raw=Path(__file__).read_bytes()
parser=argparse.ArgumentParser(description=__doc__)
for name in ['build','output','scenario','archive','fonts','music','wasmtime-site']:
 parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--initial-save',type=Path)
parser.add_argument('--backend',choices=['gles','webgpu'],default='gles')
parser.add_argument('--angle-directory',type=Path)
parser.add_argument('--wgpu-site',type=Path)
parser.add_argument('--metadata-epoch',type=int,help='Declared UTC seconds at virtual frame zero; override WASI realtime for reproducible replay metadata')
parser.add_argument('--maximum-frames',type=int,default=12000,help='Explicit bounded scenario budget, at most240000')
parser.add_argument('--maximum-wall-seconds',type=int,default=900,help='Explicit wall budget, at most7200seconds')
parser.add_argument('--declared-process-cookie',type=lambda text:int(text,0),required=True)
parser.add_argument('--declared-initial-game-ticks',type=int,required=True)
parser.add_argument('--observe-creations',action='store_true',help='Read the bounded creation ring after each actual tick; no game state is replaced')
parser.add_argument('--observe-initial-loading',action='store_true',help='Read the initial resource queue at callback/tick boundaries')
parser.add_argument('--initial-worker-pause-kind',choices=['decode','resume','player'],help='Exercise production worker suspend/resume once before the selected pending initial task; component test only')
parser.add_argument('--initial-worker-pause-frames',type=int,default=5)
args=parser.parse_args();B=args.build.resolve();O=args.output.resolve()
assert 1<=args.initial_worker_pause_frames<=30
if args.initial_worker_pause_kind:args.observe_initial_loading=True
assert 0<=args.declared_initial_game_ticks<2**32
initial_game_ticks=args.declared_initial_game_ticks
assert 0<=args.declared_process_cookie<2**32 and args.declared_process_cookie!=0xbb40e64e and args.declared_process_cookie&0xffff0000
assert 1<=args.maximum_frames<=240000 and 1<=args.maximum_wall_seconds<=7200
assert O.is_relative_to((R/'artifacts/th14').resolve())and not O.exists()
O.mkdir(parents=True);(O/'save/replay').mkdir(parents=True)
spec=importlib.util.spec_from_file_location('test_storage',R/'tools/th14-test-storage.py')
storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(O,maximum_case=128*1024**2)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
scenario_raw=args.scenario.read_bytes();scenario=json.loads(scenario_raw)
assert scenario['schema']=='th14/native-application-scenario/1'
assert 0<len(scenario['actions'])<=256
assert sum(action.get('frames',0)for action in scenario['actions'])<=args.maximum_frames
if args.initial_save:
 source=args.initial_save.resolve(strict=True)
 assert source.is_relative_to((R/'artifacts/th14').resolve())and source!=O/'save'
 for file in source.rglob('*'):
  if not file.is_file():continue
  assert not file.is_symlink()and not file.is_junction()
  assert file.resolve(strict=True).is_relative_to(source)
  relative=file.relative_to(source);assert relative.as_posix()in ['th14.cfg','scoreth14.dat']or(relative.parent.as_posix()=='replay'and relative.suffix=='.rpy')
  assert file.stat().st_size<=16*1024**2
  destination=O/'save'/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,destination)
def save_files():
 return {p.relative_to(O/'save').as_posix():dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted((O/'save').rglob('*'))if p.is_file()}
assert len(save_files())<=78
initial_save=save_files()
(O/'run-tool.py').write_bytes(tool_raw)
with args.archive.open('rb')as archive_file:archive_sha256=hashlib.file_digest(archive_file,'sha256').hexdigest()
sys.path.insert(0,str(args.wasmtime_site.resolve()));import wasmtime as W
host_path=R/('tools/th14-native-webgpu-context.py'if args.backend=='webgpu'else'tools/th14-native-gles-context.py')
spec=importlib.util.spec_from_file_location('native_graphics_context',host_path);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda raw:hashlib.sha256(raw).hexdigest();build=json.loads((B/'build.json').read_bytes());raw=(B/'application.wasm').read_bytes();assert sha(raw)==build['wasmSha256']
assert build.get('backend','gles')==args.backend
for path,row in build['sourceBindings'].items():assert sha((R/path).read_bytes())==row['sha256']
engine=W.Engine();module=W.Module(engine,raw);store=W.Store(engine);wasi=W.WasiConfig();wasi.stdout_file=str(O/'stdout.log');wasi.stderr_file=str(O/'stderr.log')
music=args.music.resolve(strict=True);fonts=args.fonts.resolve(strict=True)
wasi.preopen_dir(str(music),'/music',fs_mutable=False);wasi.preopen_dir(str(O/'save'),'/save');store.set_wasi(wasi);linker=W.Linker(engine);linker.define_wasi()
if args.backend=='webgpu':
 for name in ['Th14WebGpu.wgsl','Th14WebGpuResample.wgsl']:
  assert sha((B/'shaders'/name).read_bytes())==build['sourceBindings']['runtimes/th12/portable/sdl/'+name]['sha256']
 e=g.Context(args.wgpu_site,B/'shaders/Th14WebGpu.wgsl')
else:e=g.Context(args.angle_directory.resolve(strict=True))
clock_ns=0;callbacks=[];sequence=0;files={};next_file=10;audio={};calls=collections.Counter();file_events=[];audio_hash=hashlib.sha256();pcm_frames=0;shader_sources=[]
if args.metadata_epoch is not None:
 assert 0<args.metadata_epoch<2**32
 linker.allow_shadowing=True
 def declared_clock(caller,clock_id,precision,pointer):
  calls['declared_wasi_clock_time_get']+=1
  assert clock_id in [0,1],clock_id
  value=clock_ns+(args.metadata_epoch*1000000000 if clock_id==0 else 0)
  memory(caller).write(caller,struct.pack('<Q',value),pointer);return 0
 for imported in module.imports:
  if imported.module=='wasi_snapshot_preview1'and imported.name=='clock_time_get':
   linker.define(store,imported.module,imported.name,W.Func(store,imported.type,declared_clock,access_caller=True))
signatures_raw=(B/'gl-signatures.json').read_bytes();assert sha(signatures_raw)==build['glSignaturesSha256'];signatures=json.loads(signatures_raw)
def memory(caller):return caller['memory']
def string(caller,pointer):return C.string_at(C.addressof(memory(caller).data_ptr(caller).contents)+pointer).decode()
def write32(caller,pointer,value):
 if pointer:memory(caller).write(caller,struct.pack('<I',value&0xffffffff),pointer)
def alloc(caller,data):
 pointer=caller['malloc'](caller,len(data));assert pointer;memory(caller).write(caller,data,pointer);return pointer
def path(virtual,writing=False):
 parts=PurePosixPath(virtual).parts;assert '..'not in parts
 if virtual.startswith('/save/'):
  result=(O/'save'/Path(*parts[2:])).resolve();assert result.is_relative_to((O/'save').resolve());return result
 assert not writing,virtual
 if virtual=='/th11.dat':return args.archive.resolve(strict=True)
 if virtual.startswith('/fonts/'):
  result=(fonts/Path(*parts[2:])).resolve();assert result.is_relative_to(fonts.resolve());return result
 raise AssertionError('Unmapped private component path '+virtual)
def ctype(text):
 text=text.replace('const','').strip()
 if '*'in text:return C.c_void_p
 return {'void':None,'GLenum':C.c_uint,'GLbitfield':C.c_uint,'GLuint':C.c_uint,'GLint':C.c_int,'GLsizei':C.c_int,'GLboolean':C.c_ubyte,'GLfloat':C.c_float,'GLclampf':C.c_float,'GLintptr':C.c_ssize_t,'GLsizeiptr':C.c_ssize_t}[text]
def gl_host(name):
 signature=signatures[name];f=g.fn(e.gles,name,ctype(signature['result']),*[ctype(v)for v in signature['args']])
 def invoke(caller,*arguments):
  calls[name]+=1;m=memory(caller);address=C.addressof(m.data_ptr(caller).contents)
  if name=='glShaderSource':
   shader,count,strings,lengths=arguments;array=(C.c_char_p*count)();owned=[]
   for i in range(count):
    pointer=struct.unpack('<I',m.read(caller,strings+i*4,strings+i*4+4))[0];length=struct.unpack('<i',m.read(caller,lengths+i*4,lengths+i*4+4))[0]if lengths else -1;data=C.string_at(address+pointer,length)if length>=0 else C.string_at(address+pointer);array[i]=data;owned.append(data)
   shader_sources.append(b''.join(owned).decode());f(shader,count,array,C.c_void_p(address+lengths)if lengths else None);return
  values=[]
  for i,(value,kind)in enumerate(zip(arguments,signature['args'])):
   if '*'in kind:
    offset=(name in ['glVertexAttribPointer','glVertexAttribIPointer']and i==len(arguments)-1)or(name.startswith('glDrawElements')and i==3);values.append(C.c_void_p(value if offset else address+value if value else 0))
   else:values.append(value)
  return f(*values)
 return invoke
def audio_remaining(stream):
 if stream['running']:
  frames=(clock_ns-stream['last_ns'])*44100//1000000000;stream['queued']=max(0,stream['queued']-frames*8);stream['last_ns']+=frames*1000000000//44100
 return stream['queued']
def platform(name):
 backend=args.backend
 def invoke(caller,*args):
  global sequence,next_file,pcm_frames
  calls[name]+=1
  if name.startswith('th14_webgpu_')and name!='th14_webgpu_schedule':return e.invoke(name,caller,*args)
  if backend=='webgpu'and(name.startswith('gl')or name=='touhou_clip_control'):
   raise AssertionError('Unexpected GLES call '+name)
  if name=='th14_clock_ticks':return (initial_game_ticks+clock_ns//1000000)&0xffffffff
  if name=='SDL_GetTicksNS':return clock_ns
  if name=='SDL_GetTicks':return clock_ns//1000000
  if name in ['emscripten_async_call','th14_webgpu_schedule']:
   function,argument,delay=args;sequence+=1;heapq.heappush(callbacks,(clock_ns+max(1,delay)*1000000,sequence,function,argument));return
  if name in ['th11_reset_browser_keyboard','SDL_ResetKeyboard','SDL_CloseJoystick','SDL_DestroyWindow','SDL_Quit']:return
  if name=='SDL_free':caller['free'](caller,args[0]);return
  if name=='SDL_GetJoysticks':write32(caller,args[0],0);return 0
  if name=='SDL_OpenJoystick':return 0
  if name=='SDL_PollEvent':return 0
  if name=='SDL_GetVersion':return 3004000
  if name in ['SDL_Init','SDL_InitSubSystem','SDL_SetHint','SDL_SetWindowTitle','SDL_GL_SetAttribute','SDL_SetWindowSize','SDL_GL_SetSwapInterval','SDL_GL_SwapWindow','SDL_GL_DestroyContext']:return 1
  if name in ['SDL_CreateWindow','SDL_GL_CreateContext','SDL_GL_GetCurrentWindow']:return 1
  if name=='touhou_clip_control':return e.clip_control()
  if name=='SDL_GetError':return alloc(caller,b'Explicit native component platform error\0')
  if name=='SDL_IOFromFile':
   virtual,mode=string(caller,args[0]),string(caller,args[1]);target=path(virtual,writing=any(x in mode for x in ['w','a','+']));file_events.append(dict(operation='open',virtual=virtual,mode=mode))
   try:handle=target.open(mode)
   except FileNotFoundError:return 0
   next_file+=1;files[next_file]=handle;return next_file
  if name=='SDL_GetIOSize':
   handle=files[args[0]];position=handle.tell();handle.seek(0,2);size=handle.tell();handle.seek(position);return size
  if name=='SDL_ReadIO':
   handle,pointer,size=args;data=files[handle].read(size);memory(caller).write(caller,data,pointer);return len(data)
  if name=='SDL_WriteIO':
   handle,pointer,size=args;return files[handle].write(bytes(memory(caller).read(caller,pointer,pointer+size)))
  if name=='SDL_CloseIO':files.pop(args[0]).close();return 1
  if name=='SDL_GetPathInfo':
   assert args[1]==0,'Non-null path-info structure needs a real implementation';return int(path(string(caller,args[0])).exists())
  if name=='SDL_LoadFile':
   virtual=string(caller,args[0]);data=path(virtual).read_bytes();write32(caller,args[1],len(data));file_events.append(dict(operation='load',virtual=virtual,bytes=len(data),sha256=sha(data)));return alloc(caller,data+b'\0')
  if name=='SDL_OpenAudioDeviceStream':
   values=struct.unpack('<3i',memory(caller).read(caller,args[1],args[1]+12));assert values[1:]==(2,44100);audio[2]=dict(queued=0,last_ns=clock_ns,running=False,spec=list(values));return 2
  if name=='SDL_GetAudioStreamQueued':return audio_remaining(audio[args[0]])
  if name=='SDL_PutAudioStreamData':
   stream,pointer,size=args;assert size%8==0;audio_remaining(audio[stream]);audio[stream]['queued']+=size;pcm_frames+=size//8;audio_hash.update(bytes(memory(caller).read(caller,pointer,pointer+size)));return 1
  if name in ['SDL_ResumeAudioStreamDevice','SDL_PauseAudioStreamDevice']:
   stream=audio[args[0]];audio_remaining(stream);stream['running']=name=='SDL_ResumeAudioStreamDevice';stream['last_ns']=clock_ns;return 1
  if name=='SDL_DestroyAudioStream':audio.pop(args[0],None);return
  raise AssertionError('Unsupported actual Application import '+name)
 return invoke

# The Application constructor reads std::random_device before game callbacks.
# Declare this environment input explicitly; never patch the C++ cookie, game
# RNG or later collision state. Reject an unobserved entropy protocol.
declared_entropy=[]
linker.allow_shadowing=True
def process_entropy(caller,pointer,size):
 assert size==4,('Unexpected process entropy request',size)
 raw=struct.pack('<I',args.declared_process_cookie)
 memory(caller).write(caller,raw,pointer)
 declared_entropy.append(dict(bytes=size,value=args.declared_process_cookie,beforeGameCallbacks=not globals().get('frame_index',0)))
 assert len(declared_entropy)==1,'Unexpected second process entropy request'
 (O/'declared-process-entropy.json').write_text(json.dumps(dict(events=declared_entropy,externalEnvironmentInputDeclared=True,
  productionProcessCookieForced=False,gameRngStateSupplied=False,clockInputDeclared=True,gameRngComputedByProduction=True,completeGame=False),indent=2)+chr(10))
 return 0
entropy_imports=[i for i in module.imports if i.module=='wasi_snapshot_preview1'and i.name=='random_get']
assert len(entropy_imports)==1
for imported in entropy_imports:
 linker.define(store,imported.module,imported.name,W.Func(store,imported.type,process_entropy,access_caller=True))

rows=[];result=None;checks=[];completed=False;error=''
try:
 for imported in module.imports:
  if imported.module=='wasi_snapshot_preview1':continue
  assert imported.module=='env' and isinstance(imported.type,W.FuncType)
  callback=gl_host(imported.name)if args.backend=='gles'and imported.name.startswith('gl')else platform(imported.name)
  linker.define(store,imported.module,imported.name,W.Func(store,imported.type,callback,access_caller=True))
 instance=linker.instantiate(store,module);api=instance.exports(store);api['_initialize'](store)
 initialized=api['component_initialize'](store)
 assert initialized==1,C.string_at(C.addressof(api['memory'].data_ptr(store).contents)+api['th11_error'](store)).decode()
 table=api['__indirect_function_table'];mem=api['memory']
 frame_index=0;wall_started=time.monotonic();actions=[];captures=[];application_ticks=0
 creation_rows=[];creation_count=0
 initial_loading_rows=[];worker_pause_events=[];worker_paused=False;worker_resume_frame=0;worker_pause_done=False
 replay_construction_transitions=[]
 def replay_construction_state():
  if 'component_replay_construction_state'not in api:return None
  pointer=api['component_replay_construction_state'](store)
  return list(struct.unpack('<10I',mem.read(store,pointer,pointer+40)))
 def observe_replay_construction(before,boundary):
  if before is None:return
  after=replay_construction_state()
  if before[0]==6 and after[0]==1 and after[8]:
   replay_construction_transitions.append(dict(frame=frame_index,clockNs=clock_ns,boundary=boundary,before=before,after=after,readOnly=True))
 if args.observe_creations:assert 'component_births'in api,'Build with the read-only title observer'
 if args.observe_initial_loading:assert 'component_initial_loading_state'in api,'Build with --initial-loading-observer'
 def initial_loading_state():
  pointer=api['component_initial_loading_state'](store)
  return list(struct.unpack('<14I',mem.read(store,pointer,pointer+56)))
 def observe_initial_loading(boundary):
  if not args.observe_initial_loading:return
  words=initial_loading_state()
  if words[1]!=3:return
  pointer=api['component_initial_last_resource'](store)
  name=C.string_at(C.addressof(mem.data_ptr(store).contents)+pointer).decode()
  if not initial_loading_rows or words[3:]!=initial_loading_rows[-1]['words'][3:]or name!=initial_loading_rows[-1]['lastResource']:
   initial_loading_rows.append(dict(frame=frame_index,boundary=boundary,clockNs=clock_ns,words=words,lastResource=name))
 def state_now():
  pointer=api['component_state'](store);return list(struct.unpack('<20I',mem.read(store,pointer,pointer+80)))
 def reference_state():
  if 'component_reference_state'not in api:return None
  pointer=api['component_reference_state'](store)
  return list(struct.unpack('<12I',mem.read(store,pointer,pointer+48)))
 def capture(label):
  assert label.isascii()and label.replace('-','').isalnum()and len(label)<=48
  pointer=api['component_pixels'](store);assert pointer;pixels=bytes(mem.read(store,pointer,pointer+640*480*4))
  if args.backend=='gles':assert g.fn(e.gles,'glGetError',C.c_uint)()==0
  name=label+'.bgra';(O/name).write_bytes(pixels);entry=dict(frame=frame_index,label=label,file=name,sha256=sha(pixels))
  observed=reference_state()
  if observed is not None:entry['referenceState']=observed
  if 'component_live_state'in api:
   pointer=api['component_live_state'](store)
   complete,count,expected,width=struct.unpack('<4I',mem.read(store,pointer,pointer+16))
   if not(complete==1 and count==expected and count<=8192 and width==303):
    failure=dict(frame=frame_index,label=label,complete=complete,count=count,expected=expected,width=width,
     state=state_now(),referenceState=observed,readOnly=True)
    (O/(label+'-live-failure.json')).write_text(json.dumps(failure,indent=2)+'\n')
    raise AssertionError('Live VM observation incomplete: '+json.dumps(failure))
   raw=bytes(mem.read(store,pointer+16,pointer+16+count*width*4))
   assert len(raw)==count*width*4
   live_name=label+'-live.json'
   live=dict(readOnly=True,ordinaryAndOverlayRegistryWalk=True,complete=True,expected=expected,
    comparedValues=width,rows=[list(struct.unpack('<303I',raw[n*width*4:(n+1)*width*4]))for n in range(count)])
   (O/live_name).write_text(json.dumps(live,indent=2)+'\n')
   entry['liveAnimations']=dict(file=live_name,sha256=sha((O/live_name).read_bytes()),count=count)
  captures.append(entry);return entry
 def report():
  result=dict(schema='th14/native-application-run/1',completed=completed,error=error,checks=checks,scenarioSha256=sha(scenario_raw),initialSave=initial_save,finalSave=save_files(),buildReportSha256=sha((B/'build.json').read_bytes()),archiveSha256=archive_sha256,frames=frame_index,rows=rows,actions=actions,captures=captures,glCalls=dict(calls),pendingAsyncCallbacks=len(callbacks),deliveredCallbackSequence=sequence,files=file_events,pcmFrames=pcm_frames,pcmSha256=audio_hash.hexdigest(),wasmSha256=sha(raw),toolSha256=sha(tool_raw),renderer=e.info,actualProductionApplicationAndDevices=True,platformClockAndIoDeclared=True,physicalAudioDevicesOpened=0,virtualAudioStreamsCreated=calls['SDL_OpenAudioDeviceStream'],appUiControlled=False,browserRun=False,browserAcceptance=False,productionChanged=False,completeGame=False,nativeEquivalent=False)
  result.update(backend=args.backend,hostToolSha256=sha(host_path.read_bytes()),metadataEpochAtFrameZero=args.metadata_epoch,declaredInitialGameTicks=initial_game_ticks,
   callbackClockPolicy='queued deadlines between fixed frame starts; callback execution duration declared zero',minimumCallbackDelayMs=1)
  result['applicationTicks']=application_ticks
  if args.observe_initial_loading:result['initialLoadingObservations']=initial_loading_rows
  if 'component_replay_construction_state'in api:
   result['replayConstructionTransitions']=replay_construction_transitions
   result['replayConstructionObservationOnly']=True
  if args.initial_worker_pause_kind:
   result.update(workerPauseEvents=worker_pause_events,workerPauseKind=args.initial_worker_pause_kind,
    workerLifecycleControlledViaProductionMethods=True,workerLifecycleIsNotPhysicalUiAcceptance=True)
  if args.observe_creations:result['animationCreationRecords']=creation_rows
  observed=reference_state()
  if observed is not None:result['finalReferenceState']=observed
  (O/'report.json').write_text(json.dumps(result,indent=2)+'\n')
  return result
 print(json.dumps(dict(ready=True,state=state_now(),maximumFrames=args.maximum_frames,maximumWallSeconds=args.maximum_wall_seconds,output=str(O))),flush=True)
 for command in scenario['actions']:
  assert set(command)<=set(['frames','held','pause','capture','expect','until'])
  count=int(command.get('frames',0));held=int(command.get('held',0));pause=int(command.get('pause',0));assert 0<=count<=args.maximum_frames and 0<=held<2**32 and pause in [0,1]
  assert frame_index+count<=args.maximum_frames and time.monotonic()-wall_started<args.maximum_wall_seconds
  actions.append(dict(atFrame=frame_index,frames=count,held=held,pause=pause))
  until=command.get('until')
  if until is not None:
   assert set(until)=={'index','equals'}and count>0
   assert isinstance(until['index'],int)and 0<=until['index']<20
   assert isinstance(until['equals'],int)and 0<=until['equals']<=0xffffffff
   actions[-1]['until']=until
  for _ in range(count):
   assert time.monotonic()-wall_started<args.maximum_wall_seconds,'Native Application wall budget exhausted'
   frame_index+=1;frame_ns=frame_index*1000000000//60;delivered=0
   if worker_paused and frame_index>=worker_resume_frame:
    api['component_initial_resume'](store);worker_paused=False
    worker_pause_events.append(dict(kind='resume',frame=frame_index,clockNs=clock_ns,words=initial_loading_state()))
   while callbacks and callbacks[0][0]<=frame_ns:
    due,_,function,argument=heapq.heappop(callbacks)
    assert clock_ns<=due<=frame_ns
    # A worker continuation uses its queued delivery time. Assigning every
    # callback the next frame's time incorrectly postpones its successors.
    clock_ns=due
    paused_this_callback=False
    if args.initial_worker_pause_kind and not worker_pause_done:
     before=initial_loading_state();wanted={'decode':1,'resume':2,'player':3}[args.initial_worker_pause_kind]
     if before[0]==6 and before[1]==3 and before[12]and before[5]==wanted:
      api['component_initial_suspend'](store);worker_paused=True;worker_pause_done=True;paused_this_callback=True
      worker_resume_frame=frame_index+args.initial_worker_pause_frames
      preserved=initial_loading_state()
      worker_pause_events.append(dict(kind='suspend',frame=frame_index,clockNs=clock_ns,words=preserved))
    construction_before=replay_construction_state()
    target=table.get(store,function);assert target;target(store,argument);delivered+=1;assert delivered<=256
    observe_replay_construction(construction_before,'callback')
    if paused_this_callback:
     after=initial_loading_state();assert preserved==after,'Stale callback changed a suspended initial worker'
     worker_pause_events.append(dict(kind='stale-callback-returned',frame=frame_index,clockNs=clock_ns,pendingStatePreserved=True))
    observe_initial_loading('callback')
   clock_ns=frame_ns
   if not worker_paused:
    construction_before=replay_construction_state()
    ok=api['component_tick'](store,held,pause);application_ticks+=1
    observe_replay_construction(construction_before,'tick')
    assert ok==1,C.string_at(C.addressof(api['memory'].data_ptr(store).contents)+api['th11_error'](store)).decode()
   observe_initial_loading('paused'if worker_paused else'tick')
   if args.observe_creations:
    pointer=api['component_births'](store);assert pointer,'Creation ring exceeded its4096-record observation budget'
    count,width=struct.unpack('<2I',mem.read(store,pointer,pointer+8))
    assert width==6 and creation_count<=count<=4096
    creation_bytes=mem.read(store,pointer+8+creation_count*24,pointer+8+count*24)
    for n,values in enumerate(struct.iter_unpack('<6I',creation_bytes),creation_count):
     creation_rows.append(dict(record=n,appFrame=frame_index,script=values[0],requestedLayer=values[1],file=values[2],
      hasResource=values[3],depth=values[4],handle=values[5],serial=values[5]>>13,slot=values[5]&8191))
    creation_count=count
   state=state_now();key=state[:2]+state[3:6]+state[7:16]
   if not rows or frame_index%30==0 or key!=rows[-1]['key']:rows.append(dict(frame=frame_index,clockNs=clock_ns,state=state,key=key,callbacksDelivered=delivered))
   if frame_index%3000==0:
    storage.check_budget(O,maximum_case=128*1024**2)
    print(json.dumps(dict(progressFrame=frame_index,state=state,elapsedSeconds=time.monotonic()-wall_started,maximumFrames=args.maximum_frames)),flush=True)
   if until is not None and state[until['index']]==until['equals']:break
  if until is not None:assert state_now()[until['index']]==until['equals'],'Declared state was not reached within the frame budget'
  image=capture(command['capture'])if command.get('capture')else None
  actual=state_now()
  actions[-1].update(endFrame=frame_index,state=actual)
  for field,wanted in command.get('expect',{}).items():
   index=int(field);assert 0<=index<20
   check=dict(frame=frame_index,index=index,expected=wanted,actual=actual[index],passed=actual[index]==wanted);checks.append(check)
   assert check['passed'],check
  storage.check_budget(O,maximum_case=128*1024**2)
  print(json.dumps(dict(frame=frame_index,state=actual,capture=image,pcmFrames=pcm_frames,pendingCallbacks=len(callbacks))),flush=True)
 if args.initial_worker_pause_kind:
  assert worker_pause_done and not worker_paused and [event['kind']for event in worker_pause_events]==['suspend','stale-callback-returned','resume']
 api['component_audio_close'](store);completed=True;report()
 print(json.dumps(dict(completed=True,frames=frame_index,checks=len(checks),saveFiles=save_files())),flush=True)
except BaseException as failure:
 error=repr(failure)
 if 'frame_index'in globals():report()
 raise
finally:
 for handle in files.values():handle.close()
 e.close()
