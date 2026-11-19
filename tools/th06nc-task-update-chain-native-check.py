"""Actual update chain 3be80 with controlled task callbacks and sound transport.

Finite repeat/restart/delete/stop traces, linked nodes and status compared.
Removal executes 126e0 without heap-owned nodes; destructor is observed.
Not a proof of gameplay task registration, platform delivery or all scheduling.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/task-update-chain.mjs';before=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{runUpdateChain}from'./shared/th06nc/task-update-chain.mjs';const cases=[];
for(const sequence of [[],[1],[0],[2,1],[2,2,0],[6,1],[6,6,1],[3],[4],[5],[7],[-1]])for(const at of [0,1,2])for(const value of [0,42]){const events=[],head={next:null,update:null},nodes=Array.from({length:3},(_,id)=>({id,context:id,next:null,previous:null,update:null}));[head,...nodes].forEach((n,i,a)=>{n.next=a[i+1]??null;n.previous=a[i-1]??null;});const indices=[0,0,0];for(const n of nodes)n.update=sequence.length===0?null:()=>{const i=indices[n.id]++,code=n.id===at?(sequence[i]??1):1;events.push({kind:'task',id:n.id,code});return code;};const status={value},result=runUpdateChain(head,{status,remove:n=>{events.push({kind:'destroy',id:n.id});n.previous.next=n.next;if(n.next)n.next.previous=n.previous;n.next=n.previous=null;n.update=null;},consumeSounds:()=>events.push({kind:'sound'})});cases.push({sequence,at,value,events,result,status:status.value,links:nodes.map(n=>({next:n.next?.id??null,previous:n.previous===head?-1:n.previous?.id??null,active:Boolean(n.update)}))});}console.log(JSON.stringify(cases));
 """
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;head=0x1404f1440;nodeBase=n.vm+0x1000;events=[];indices=[0]*3;current=None;digest=hashlib.sha256()
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x140076a30:events.append(dict(kind='sound'))
  elif a==n.vm+0x9000:
   identity=m.reg_read(UC_X86_REG_RCX);i=indices[identity];indices[identity]+=1;sequence=current['sequence'];code=sequence[i]if identity==current['at']and i<len(sequence)else 1;events.append(dict(kind='task',id=identity,code=code));m.reg_write(UC_X86_REG_EAX,code&0xffffffff)
  elif a==n.vm+0x9010:events.append(dict(kind='destroy',id=m.reg_read(UC_X86_REG_RCX)))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140076a30,n.vm+0x9000,n.vm+0x9010]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for index,c in enumerate(cases):
  current=c;events.clear();indices[:]=[0]*3;m.mem_write(head,bytes(64));m.mem_write(head+0x28,struct.pack('<Q',nodeBase));m.mem_write(n.owner,struct.pack('<i',c['value']))
  for i in range(3):
   raw=bytearray(64);struct.pack_into('<Q',raw,8,n.vm+0x9000 if c['sequence']else 0);struct.pack_into('<Q',raw,0x18,n.vm+0x9010);struct.pack_into('<Q',raw,0x20,head if i==0 else nodeBase+(i-1)*64);struct.pack_into('<Q',raw,0x28,nodeBase+(i+1)*64 if i<2 else 0);struct.pack_into('<Q',raw,0x38,i);m.mem_write(nodeBase+i*64,bytes(raw))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14003be80,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;assert events==c['events'],(index,events,c['events']);assert m.reg_read(UC_X86_REG_RAX)&255==c['result']['value'],(index,'value');assert struct.unpack('<i',m.mem_read(n.owner,4))[0]==c['status'],(index,'status')
  def identity(ptr):return None if ptr==0 else -1 if ptr==head else (ptr-nodeBase)//64
  links=[]
  for i in range(3):
   raw=bytes(m.mem_read(nodeBase+i*64,64));links.append(dict(next=identity(struct.unpack_from('<Q',raw,0x28)[0]),previous=identity(struct.unpack_from('<Q',raw,0x20)[0]),active=bool(struct.unpack_from('<Q',raw,8)[0])))
  assert links==c['links'],(index,links,c['links']);digest.update(json.dumps(events,sort_keys=True).encode())
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==before;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:before},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-task-update-chain-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
