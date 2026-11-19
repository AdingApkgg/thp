"""Real previous-state2/request7 Result dispatch through original application.

Complete global fade bytes, dirty/state/priorities and ordered
task deletes/allocation/construct/register requests compare. Fade absent and all
modes/alpha edges, practice and register failure covered. Task/heap/Result services
are controlled; real application registration/deletion bodies and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/gameplay-result-handoff.mjs','shared/th06nc/fade.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{prepareGameplayResult}from'./shared/th06nc/gameplay-result-handoff.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const exists of [false,true])for(const mode of [0,1,2,3,4])for(const alpha of [-1,0,1,128,255,256,2147483647])for(const practice of [false,true])for(const failure of [false,true]){const fade=new NativeFade();fade.state.set(Uint8Array.from({length:56},(_,i)=>(cases.length+i*17)&255));fade.v.setInt32(0x34,mode,true);fade.v.setInt32(0x28,alpha,true);const before=hex(fade.state),events=[],result=prepareGameplayResult(exists?fade:null,{practice},{detachGameplay:()=>events.push({kind:'detach'}),registerResult:plan=>{events.push({kind:'result',...plan});return failure?-1:0;}});cases.push({exists,mode,alpha,practice,failure,before,after:hex(fade.state),events,result});}console.log(JSON.stringify(cases));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;resultptr=n.assets+0x100000;events=[];failure=False;digest=hashlib.sha256()
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x1400126e0:events.append(dict(kind='delete',address=m.reg_read(UC_X86_REG_RDX)))
  elif a==0x1402bcf40:assert m.reg_read(UC_X86_REG_RCX)==0xbb48;m.reg_write(UC_X86_REG_RAX,resultptr)
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes(m.reg_read(UC_X86_REG_R8)));m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
  elif a==0x14006df00:m.reg_write(UC_X86_REG_RAX,resultptr)
  elif a==0x14006dd20:
   events.append(dict(kind='result',state=struct.unpack('<i',m.mem_read(resultptr+0x9e94,4))[0],dirty=bytes(m.mem_read(resultptr+0x9e99,1))[0],updatePriority=m.reg_read(UC_X86_REG_RDX),drawPriority=m.reg_read(UC_X86_REG_R8)));m.reg_write(UC_X86_REG_EAX,0xffffffff if failure else 0)
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1400126e0,0x1402bcf40,0x1402bdee2,0x14006df00,0x14006dd20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for i,c in enumerate(data):
  m.mem_write(n.owner,bytes(0x500));m.mem_write(n.owner+0x428,struct.pack('<3i',2,7,-1));m.mem_write(n.vm,bytes.fromhex(c['before']));m.mem_write(0x140c22158,struct.pack('<Q',n.vm if c['exists']else 0));m.mem_write(0x1404f27b4,bytes([c['practice']]));sp=n.stack+0x8000;m.mem_write(sp+0x28,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_EBX,0);events.clear();failure=c['failure'];m.emu_start(0x140079d7a,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(i,'stop');actual=bytes(m.mem_read(n.vm,56));assert actual==bytes.fromhex(c['after']),(i,'fade');assert m.reg_read(UC_X86_REG_EAX)==c['result'],(i,'return');expected=[]
  for event in c['events']:
   if event['kind']=='detach':expected.extend([dict(kind='delete',address=0x1404f1e20),dict(kind='delete',address=0x1404f1de0)])
   else:expected.append(event)
  assert events==expected,(i,'requests',events,expected);digest.update(actual)
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,cases=len(data),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-gameplay-result-handoff-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data)}))
if __name__=='__main__':main()
