"""Actual task dispatcher 3be80 and game-owner UI gate 3a210.

Synthetic linked task nodes use original priorities: ASCII1, result3, game4,
player7, enemy9, effect10, projectile11, message16. Actor/UI callback bodies,
viewport/render/time services and the active gameplay body after its gate are
controlled. Actual game-owner prologue, flag gates and return3, dispatcher
traversal/stop and epilogues execute unchanged. This establishes suspension
order, not task allocation/destruction, actor state or visual equivalence.
"""
import hashlib,itertools,json,struct
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['runtimes/th06nc/game.mjs','shared/th06nc/spell-practice-result-menu.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 n=Native();m=n.m;sentinel=0x1404f1440;events=[];cases=[];controlled={}
 def ret(m):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 def hook(m,a,size,u):
  if a in controlled:events.append(controlled[a]);return
  if a==0x14003a210:events.append('game');return
  if a==0x14003a41f:m.reg_write(UC_X86_REG_EAX,1);m.reg_write(UC_X86_REG_RIP,0x14003a7cf);return
  if a==0x140083870:
   for reg in [UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9]:m.mem_write(m.reg_read(reg),bytes(4))
  ret(m)
 for a in [0x14003a210,0x14003a41f,0x14007af40,0x140083870,0x1400953f0,0x14007f720,0x1402bcf20,0x140076a30]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for i,name in enumerate(['ascii','result','player','enemy','effect','projectile','message']):
  address=n.assets+0x20000+i*16;controlled[address]=name;m.mem_write(address,b'\xb8\x01\x00\x00\x00\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 callback={name:a for a,name in controlled.items()};callback['game']=0x14003a210
 priorities={'ascii':1,'result':3,'game':4,'player':7,'enemy':9,'effect':10,'projectile':11,'message':16}
 for pause,gameOver,visible,state,resultPresent in itertools.product([0,1,2,3],[False,True],[False,True],[1,2,8],[False,True]):
  names=[name for name in priorities if name!='result'or resultPresent];nodes=[sentinel]+[n.assets+0x10000+i*64 for i in range(len(names))]
  for i,address in enumerate(nodes):
   b=bytearray(64)
   if i:struct.pack_into('<h',b,0,priorities[names[i-1]]);struct.pack_into('<Q',b,8,callback[names[i-1]]);struct.pack_into('<Q',b,0x38,n.owner)
   struct.pack_into('<Q',b,0x20,nodes[i-1]if i else 0);struct.pack_into('<Q',b,0x28,nodes[i+1]if i+1<len(nodes)else 0);m.mem_write(address,bytes(b))
  m.mem_write(n.owner,bytes(0x20000));m.mem_write(n.owner+0xd418,struct.pack('<i',1));m.mem_write(n.owner+0x950,bytes([pause,gameOver,0,0,0,1,visible]));m.mem_write(0x140c21d9c,struct.pack('<i',state));m.mem_write(0x140c21a70,b'\0');m.mem_write(0x140a6ec60,bytes(8));m.mem_write(0x140c22158,bytes(8));events.clear();m.mem_write(n.vm,bytes(4));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.vm)
  m.emu_start(0x14003be80,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  blocked=pause in [1,2]or gameOver or visible or state!=2;wanted=names[:names.index('game')+1]if blocked else names
  assert events==wanted,(pause,gameOver,visible,state,resultPresent,events,wanted)
  assert m.mem_read(n.owner+0x952,1)[0]==int(not(pause or gameOver or visible))
  assert (m.reg_read(UC_X86_REG_RAX)&255)==0,(pause,gameOver,visible,state,resultPresent,m.reg_read(UC_X86_REG_RAX))
  cases.append(dict(pause=pause,gameOver=gameOver,spellResultVisible=visible,gameState=state,resultPresent=resultPresent,events=events.copy(),blocked=bool(blocked)))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(cases),evidence=cases,sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-task-gate-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(cases),blocked=sum(c['blocked']for c in cases))))

if __name__=='__main__':main()
