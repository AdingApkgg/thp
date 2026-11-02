"""Execute the original TH14 replay reader to validate the proposed marker breakpoint."""
from pathlib import Path
import argparse,ast,hashlib,importlib,json,struct,tempfile,time,types
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest();obs=R/'tools/th14-native-terminal-marker-observer-nov03.py';baseobs=R/'tools/th14-native-campaign-observer-oct25.py'
def calls(p,name):return [ast.dump(x,include_attributes=False) for x in ast.walk(ast.parse(p.read_text(encoding='utf8'))) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr==name]
for n in ['WriteProcessMemory','SuspendThread','ResumeThread','Wow64SetThreadContext']:assert calls(obs,n)==calls(baseobs,n)
img,*_=importlib.import_module('th-anm-handlers').handlers(14);assert sha(img.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353';m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,addr,size,raw,count in img.sections:
 page=addr&~4095;m.mem_map(page,((addr+size+4095)&~4095)-page);m.mem_write(addr,img.data[raw:raw+count])
BASE=0x70000000;m.mem_map(BASE,0x100000);manager,header,inputs,rates,stack=[BASE+x for x in (0x1000,0x3000,0x4000,0x8000,0xff000)];put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff));get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0];hits=[];pauses=[];exhaustions=[]
def trace(u,pc,size,user):
 if pc==0x45521b:
  ptr=u.reg_read(UC_X86_REG_EAX);hits.append(bytes(u.mem_read(ptr,6)).hex());assert bytes(u.mem_read(pc,10)).hex()=='c705906a4d0000000000'
 if pc==0x4552cd:
  exhaustions.append((u.reg_read(UC_X86_REG_EAX),u.reg_read(UC_X86_REG_ECX)));assert bytes(u.mem_read(pc,10)).hex()=='c705906a4d0000000000'
 if pc==0x448ef0:
  pauses.append(pc);sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EIP,get(sp));u.reg_write(UC_X86_REG_ESP,sp+4);u.reg_write(UC_X86_REG_EAX,1)
for pc in [0x45521b,0x4552cd,0x448ef0]:m.hook_add(UC_HOOK_CODE,trace,begin=pc,end=pc)
rows=[]
for words in [(65535,65535,65535),(65534,65535,65535),(65535,65534,65535),(65535,65535,65534),(0,0,0)]:
 m.mem_write(BASE,bytes(0xfe000));m.mem_write(0x4d6878,bytes(0x240));put(0x4db558,1);m.mem_write(inputs,struct.pack('<3H',*words));m.mem_write(rates,b'\x3c');put(header+4,1);put(manager+0x218,1);slot=manager+40
 for off,value in [(0xd8,header),(0xcc,inputs),(0xd4,rates),(0xdc,0)]:put(slot+off,value)
 put(stack,BASE);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);hits.clear();pauses.clear();exhaustions.clear();m.emu_start(0x455180,BASE,count=10000);assert m.reg_read(UC_X86_REG_EIP)==BASE
 marker=words==(65535,65535,65535);assert len(hits)==int(marker) and len(pauses)==int(marker);assert get(slot+0xdc)==(0 if marker else 1)
 assert not exhaustions
 rows.append(dict(marker=marker,markerBreakpointHits=len(hits),pauseBoundaryCalls=len(pauses),cursorAfter=get(slot+0xdc)))
# Exhausted zero-length stage reaches the second original boundary without requesting pause.
m.mem_write(BASE,bytes(0xfe000));m.mem_write(0x4d6878,bytes(0x240));put(0x4db558,1);put(header+4,0);put(manager+0x218,1);slot=manager+40
for off,value in [(0xd8,header),(0xcc,inputs),(0xd4,rates),(0xdc,0)]:put(slot+off,value)
put(stack,BASE);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,manager);hits.clear();pauses.clear();exhaustions.clear();m.emu_start(0x455180,BASE,count=10000)
assert m.reg_read(UC_X86_REG_EIP)==BASE and not hits and not pauses and exhaustions==[(0,header)] and get(slot+0xdc)==1
# Exercise the actual observer install() against synthetic stopped-thread contexts.
node=next(x for x in ast.parse(obs.read_text(encoding='utf8')).body if isinstance(x,ast.FunctionDef) and x.name=='install')
class K:
 def __init__(self):self.last=None
 def Wow64SetThreadContext(self,h,b):self.last=bytes(b);return 1
k=K();opt=types.SimpleNamespace(publication_cutoff=1000,scene_camera_events=True,controller_phase_events=True,camera_write_events=False,exit_boundary_events=True,normal_vm_window_events=False)
ns=dict(struct=struct,k=k,opt=opt,C=types.SimpleNamespace(get_last_error=lambda:0,WinError=OSError),confirmed_thread_ended=lambda tid:False,context=lambda h:bytearray(716),threads={10:10,20:20},pi=types.SimpleNamespace(tid=10),pending_publications={},first_snapshot={'present':True},callback_count=1500,serial_watch_manager=0,sleep_pcs={},transition_trace=False,hud_score_pc={},pending_worker_rng=set(),main_camera_phase='draw',normal_vm_window_tid=None,ascii_create_invocations=[1],terminal_marker_events=[],observed_exhaustion_stages=set(),u32=lambda address:1)
exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(obs),'exec'),ns)
def slots(tid,transition,events,callback):
 ns.update(transition_trace=transition,terminal_marker_events=events,callback_count=callback);ns['install'](tid,current=True);return struct.unpack_from('<4I',k.last,4),struct.unpack_from('<I',k.last,24)[0]
armed,dr7=slots(10,False,[],1500);assert armed[1]==0x45521b and armed[2]==0x4552cd and dr7&(1<<2) and dr7&(1<<4)
assert 0x45521b not in slots(10,True,[],1500)[0]
assert 0x45521b not in slots(20,False,[],1500)[0]
assert 0x45521b not in slots(10,False,[],500)[0]
assert 0x45521b not in slots(10,False,[{}],1500)[0]
ns['observed_exhaustion_stages']={1};assert 0x4552cd not in slots(10,False,[],1500)[0]
ns['u32']=lambda address:2;assert 0x4552cd in slots(10,False,[],1500)[0]
# Execute the actual marker-handler AST with controlled read-only memory.
tree=ast.parse(obs.read_text(encoding='utf8'))
def marker_test(test):
 return isinstance(test,ast.Compare) and isinstance(test.left,ast.Name) and test.left.id=='pc' and len(test.comparators)==1 and isinstance(test.comparators[0],ast.Constant) and test.comparators[0].value==0x45521b
handler=next(x for x in ast.walk(tree) if isinstance(x,ast.If) and marker_test(x.test))
handler_code=compile(ast.fix_missing_locations(ast.Module(body=handler.body,type_ignores=[])),str(obs),'exec')
with tempfile.TemporaryDirectory(prefix='marker-handler-',dir=R/'artifacts/th14') as tmp:
 manager=0x100000;ptr=0x200000;header=0x300000;index=6;cursor=122;framecount=123;slot=manager+index*40;memory={manager+0x218:index,slot+0xd8:header,slot+0xdc:cursor,slot+0xcc:ptr,header+4:framecount,0x4f58a4:6};marker=[b'\xff'*6];context=bytearray(716);struct.pack_into('<11I',context,156,0,manager,0,0,0,ptr,0,0x45521b,0,0,0)
 def read(address,size):
  if address==ptr and size==6:return marker[0]
  if address==0x45521b and size==10:return bytes.fromhex('c705906a4d0000000000')
  if address==header and size==2:return struct.pack('<H',6)
  raise AssertionError((address,size))
 observed=[];env=dict(struct=struct,json=json,time=time,read=read,u32=lambda addr:memory[addr],pc=0x45521b,b=context,ev=types.SimpleNamespace(tid=77),callback_count=10000,terminal_marker_events=observed,home=Path(tmp))
 exec(handler_code,env);assert len(observed)==1 and observed[0]['recordedStage']==6 and observed[0]['stageInputCursor']==122 and observed[0]['markerAtLastRecordedInput'] and observed[0]['readOnly'] and not observed[0]['nativeValuesProvidedToEngine']
 assert json.loads((Path(tmp)/'replay-terminal-marker-events.jsonl').read_text())==observed[0]
 for kind in ['marker','pointer','cursor']:
  observed.clear();marker[0]=b'\x00'+b'\xff'*5 if kind=='marker' else b'\xff'*6;memory[slot+0xcc]=ptr+2 if kind=='pointer' else ptr;memory[slot+0xdc]=framecount if kind=='cursor' else cursor
  try:exec(handler_code,env)
  except AssertionError:pass
  else:raise AssertionError('handler accepted invalid '+kind)
  assert not observed
# Exercise the input-exhaustion handler without a live debuggee.
exhaust_handler=next(x for x in ast.walk(tree) if isinstance(x,ast.If) and isinstance(x.test,ast.Compare) and isinstance(x.test.left,ast.Name) and x.test.left.id=='pc' and len(x.test.comparators)==1 and isinstance(x.test.comparators[0],ast.Constant) and x.test.comparators[0].value==0x4552cd)
exhaust_code=compile(ast.fix_missing_locations(ast.Module(body=exhaust_handler.body,type_ignores=[])),str(obs),'exec')
with tempfile.TemporaryDirectory(prefix='exhaust-handler-',dir=R/'artifacts/th14') as tmp:
 manager=0x100000;header=0x300000;index=6;framecount=123;slot=manager+index*40;memory={manager+0x218:index,slot+0xd8:header,slot+0xdc:framecount,header+4:framecount,0x4f58a4:6};context=bytearray(716);struct.pack_into('<11I',context,156,0,manager,0,0,header,framecount,0,0x4552cd,0,0,0)
 def read_exhaust(address,size):
  if address==0x4552cd and size==10:return bytes.fromhex('c705906a4d0000000000')
  if address==header and size==2:return struct.pack('<H',6)
  raise AssertionError((address,size))
 observed=[];seen=set();env=dict(struct=struct,json=json,time=time,read=read_exhaust,u32=lambda addr:memory[addr],pc=0x4552cd,b=context,ev=types.SimpleNamespace(tid=77),callback_count=10000,stage_input_exhaustion_events=observed,observed_exhaustion_stages=seen,home=Path(tmp))
 exec(exhaust_code,env);assert len(observed)==1 and observed[0]['recordedStage']==6 and observed[0]['exactFirstExhaustedCursor'] and observed[0]['readOnly'] and seen=={6}
 assert json.loads((Path(tmp)/'replay-stage-input-exhaustion-events.jsonl').read_text())==observed[0]
 for kind in ['cursor','header','already-seen']:
  observed.clear();seen.clear();memory[slot+0xdc]=framecount-1 if kind=='cursor' else framecount;memory[slot+0xd8]=header+4 if kind=='header' else header
  if kind=='already-seen':seen.add(6)
  try:exec(exhaust_code,env)
  except AssertionError:pass
  else:raise AssertionError('handler accepted invalid '+kind)
  assert not observed
result=dict(verifiedOriginalTerminalMarkerInstruction=True,originalReaderCases=len(rows)+1,originalInputExhaustionCasePassed=True,syntheticDebugRegisterInstallCases=7,syntheticExhaustionHandlerPositiveCases=1,syntheticExhaustionHandlerNegativeCases=3,syntheticHandlerPositiveCases=1,syntheticHandlerNegativeCases=3,markerPositiveCases=1,negativeControls=4,allCasesMatched=True,originalInstructionsPatched=False,gameProcessLaunched=False,liveObserverValidated=False,sourceReplayEofProved=False,completeGame=False,nativeEquivalent=False,rows=rows,observerSha256=sha(obs.read_bytes()),baseObserverSha256=sha(baseobs.read_bytes()),verifierSha256=sha(Path(__file__).read_bytes()))
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path,default=R/'artifacts/th14/replay-candidates-second-nov03/terminal-marker-unit.json');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14') or out.is_relative_to(R/'docs/porting');data=(json.dumps(result,indent=2)+'\n').encode()
if a.check:assert out.read_bytes()==data
else:out.write_bytes(data)
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
