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
parser=argparse.ArgumentParser(description=__doc__)
for name in ['build','output','scenario','archive','fonts','music','angle-directory','wasmtime-site']:
 parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--initial-save',type=Path)
args=parser.parse_args();B=args.build.resolve();O=args.output.resolve()
assert O.is_relative_to((R/'artifacts/th14').resolve())and not O.exists()
O.mkdir(parents=True);(O/'save/replay').mkdir(parents=True)
spec=importlib.util.spec_from_file_location('test_storage',R/'tools/th14-test-storage.py')
storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(O)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
scenario_raw=args.scenario.read_bytes();scenario=json.loads(scenario_raw)
assert scenario['schema']=='th14/native-application-scenario/1'
assert 0<len(scenario['actions'])<=256
assert sum(action.get('frames',0)for action in scenario['actions'])<=12000
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
(O/'run-tool.py').write_bytes(Path(__file__).read_bytes())
with args.archive.open('rb')as archive_file:archive_sha256=hashlib.file_digest(archive_file,'sha256').hexdigest()
sys.path.insert(0,str(args.wasmtime_site.resolve()));import wasmtime as W
spec=importlib.util.spec_from_file_location('native_gles_context',R/'tools/th14-native-gles-context.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda raw:hashlib.sha256(raw).hexdigest();build=json.loads((B/'build.json').read_bytes());raw=(B/'application.wasm').read_bytes();assert sha(raw)==build['wasmSha256']
for path,row in build['sourceBindings'].items():assert sha((R/path).read_bytes())==row['sha256']
engine=W.Engine();module=W.Module(engine,raw);store=W.Store(engine);wasi=W.WasiConfig();wasi.stdout_file=str(O/'stdout.log');wasi.stderr_file=str(O/'stderr.log')
music=args.music.resolve(strict=True);fonts=args.fonts.resolve(strict=True)
wasi.preopen_dir(str(music),'/music',fs_mutable=False);wasi.preopen_dir(str(O/'save'),'/save');store.set_wasi(wasi);linker=W.Linker(engine);linker.define_wasi();e=g.Context(args.angle_directory.resolve(strict=True))
clock_ns=0;callbacks=[];sequence=0;files={};next_file=10;audio={};calls=collections.Counter();file_events=[];audio_hash=hashlib.sha256();pcm_frames=0;shader_sources=[]
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
 def invoke(caller,*args):
  global sequence,next_file,pcm_frames
  calls[name]+=1
  if name=='th14_clock_ticks':return (clock_ns//1000000)&0xffffffff
  if name=='SDL_GetTicksNS':return clock_ns
  if name=='SDL_GetTicks':return clock_ns//1000000
  if name=='emscripten_async_call':
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
rows=[];result=None;checks=[];completed=False;error=''
try:
 for imported in module.imports:
  if imported.module=='wasi_snapshot_preview1':continue
  assert imported.module=='env' and isinstance(imported.type,W.FuncType)
  callback=gl_host(imported.name)if imported.name.startswith('gl')else platform(imported.name)
  linker.define(store,imported.module,imported.name,W.Func(store,imported.type,callback,access_caller=True))
 instance=linker.instantiate(store,module);api=instance.exports(store);api['_initialize'](store)
 initialized=api['component_initialize'](store)
 assert initialized==1,C.string_at(C.addressof(api['memory'].data_ptr(store).contents)+api['th11_error'](store)).decode()
 table=api['__indirect_function_table'];mem=api['memory']
 frame_index=0;wall_started=time.monotonic();actions=[];captures=[]
 def state_now():
  pointer=api['component_state'](store);return list(struct.unpack('<20I',mem.read(store,pointer,pointer+80)))
 def capture(label):
  assert label.isascii()and label.replace('-','').isalnum()and len(label)<=48
  pointer=api['component_pixels'](store);assert pointer;pixels=bytes(mem.read(store,pointer,pointer+640*480*4));assert g.fn(e.gles,'glGetError',C.c_uint)()==0
  name=label+'.bgra';(O/name).write_bytes(pixels);entry=dict(frame=frame_index,label=label,file=name,sha256=sha(pixels));captures.append(entry);return entry
 def report():
  result=dict(schema='th14/native-application-run/1',completed=completed,error=error,checks=checks,scenarioSha256=sha(scenario_raw),initialSave=initial_save,finalSave=save_files(),buildReportSha256=sha((B/'build.json').read_bytes()),archiveSha256=archive_sha256,frames=frame_index,rows=rows,actions=actions,captures=captures,glCalls=dict(calls),pendingAsyncCallbacks=len(callbacks),deliveredCallbackSequence=sequence,files=file_events,pcmFrames=pcm_frames,pcmSha256=audio_hash.hexdigest(),wasmSha256=sha(raw),toolSha256=sha(Path(__file__).read_bytes()),renderer=e.info,actualProductionApplicationAndDevices=True,platformClockAndIoDeclared=True,physicalAudioDevicesOpened=0,virtualAudioStreamsCreated=calls['SDL_OpenAudioDeviceStream'],appUiControlled=False,browserRun=False,browserAcceptance=False,productionChanged=False,completeGame=False,nativeEquivalent=False)
  (O/'report.json').write_text(json.dumps(result,indent=2)+'\n')
  return result
 print(json.dumps(dict(ready=True,state=state_now(),maximumFrames=12000,maximumWallSeconds=900,output=str(O))),flush=True)
 for command in scenario['actions']:
  assert set(command)<=set(['frames','held','pause','capture','expect'])
  count=int(command.get('frames',0));held=int(command.get('held',0));pause=int(command.get('pause',0));assert 0<=count<=6000 and 0<=held<2**32 and pause in [0,1]
  assert frame_index+count<=12000 and time.monotonic()-wall_started<900
  actions.append(dict(atFrame=frame_index,frames=count,held=held,pause=pause))
  for _ in range(count):
   assert time.monotonic()-wall_started<900,'Native Application wall budget exhausted'
   frame_index+=1;clock_ns=frame_index*1000000000//60;delivered=0
   while callbacks and callbacks[0][0]<=clock_ns:
    _,_,function,argument=heapq.heappop(callbacks);target=table.get(store,function);assert target;target(store,argument);delivered+=1;assert delivered<=256
   ok=api['component_tick'](store,held,pause)
   assert ok==1,C.string_at(C.addressof(api['memory'].data_ptr(store).contents)+api['th11_error'](store)).decode()
   state=state_now();key=state[:2]+state[3:6]+state[7:16]
   if not rows or frame_index%30==0 or key!=rows[-1]['key']:rows.append(dict(frame=frame_index,clockNs=clock_ns,state=state,key=key,callbacksDelivered=delivered))
  image=capture(command['capture'])if command.get('capture')else None
  actual=state_now()
  actions[-1].update(endFrame=frame_index,state=actual)
  for field,wanted in command.get('expect',{}).items():
   index=int(field);assert 0<=index<20
   check=dict(frame=frame_index,index=index,expected=wanted,actual=actual[index],passed=actual[index]==wanted);checks.append(check)
   assert check['passed'],check
  storage.check_budget(O)
  print(json.dumps(dict(frame=frame_index,state=actual,capture=image,pcmFrames=pcm_frames,pendingCallbacks=len(callbacks))),flush=True)
 api['component_audio_close'](store);completed=True;report()
 print(json.dumps(dict(completed=True,frames=frame_index,checks=len(checks),saveFiles=save_files())),flush=True)
except BaseException as failure:
 error=repr(failure)
 if 'frame_index'in globals():report()
 raise
finally:
 for handle in files.values():handle.close()
 e.close()
