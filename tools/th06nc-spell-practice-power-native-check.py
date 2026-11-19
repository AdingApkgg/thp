"""Native static Power-map producer and actual gameplay lookup.

Executes 1780..188a with controlled allocation/map insertion/atexit services to
observe all nine original pairs. Then executes 3b018..3b0d4 against a controlled
linked-bucket representation of those pairs, comparing all byte IDs and wraps.
Also compares spell startup globals, cleared live stocks and preserved continue defaults.
Whole startup/task lifecycle is not claimed.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/spell-practice-power.mjs';sources=[source,'shared/th06nc/spell-practice-run.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};n=Native();m=n.m;pairs=[]
 def hook(m,a,size,u):
  if a==0x1402bcf40:m.reg_write(UC_X86_REG_RAX,n.vm)
  elif a==0x1400777a0:
   p=m.reg_read(UC_X86_REG_R8);pairs.append((m.mem_read(p,1)[0],struct.unpack('<I',m.mem_read(p+4,4))[0]))
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1402bcf40,0x140044960,0x1400777a0,0x1402bd1e0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x140001780,n.stack+0xf000,count=10000);assert len(pairs)==9
 script="import{initializeSpellPracticeRun}from'./shared/th06nc/spell-practice-run.mjs';import{spellPracticeStartingPower}from'./shared/th06nc/spell-practice-power.mjs';console.log(JSON.stringify([-1,...Array.from({length:256},(_,i)=>i),256,511].map((id,i)=>{const before={spellPracticeIndex:id,spellEnemyStarted:true,spellRunState:4,spellRunClock:75,spellRunBossLife:-3,spellRunSurvival:true,spellFinished:true,playerPower:999,lives:i&255,bombs:(i*3)&255,defaultLives:(255-i)&255,defaultBombs:7};return{id,power:spellPracticeStartingPower(id),before,after:initializeSpellPracticeRun({...before})};})));";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))
 assert all(next(c['power']for c in cases if c['id']==id)==power for id,power in pairs)
 for i,(id,power)in enumerate(pairs):
  p=n.owner+i*40;b=bytearray(40);struct.pack_into('<QQB',b,0,p-40 if i else n.vm,p+40 if i+1<len(pairs)else n.vm,id);struct.pack_into('<H',b,20,power);m.mem_write(p,bytes(b))
 m.mem_write(n.manager,struct.pack('<2Q',n.owner+(len(pairs)-1)*40,n.owner));m.mem_write(0x140c22198,struct.pack('<Q',n.manager));m.mem_write(0x140c22188,struct.pack('<Q',n.vm));m.mem_write(0x140c221b0,bytes(8));digest=hashlib.sha256()
 fields={'spellEnemyStarted':(0x140aa1e7f,'B'),'spellRunState':(0x140c2217c,'i'),'spellRunClock':(0x140c22178,'i'),'spellRunBossLife':(0x140c22088,'i'),'spellRunSurvival':(0x140aa1e8d,'B'),'spellFinished':(0x140aa1e8e,'B'),'playerPower':(0x1404f1e88,'H'),'lives':(0x1404ff0f0,'B'),'bombs':(0x1404ff0f1,'B'),'defaultLives':(0x140c21de0,'B'),'defaultBombs':(0x140c21de1,'B')}
 for c in cases:
  for key,(address,fmt)in fields.items():m.mem_write(address,struct.pack('<'+fmt,int(c['before'][key])))
  m.mem_write(0x1404f27b8,bytes([c['id']&255]));m.mem_write(0x1404f1e88,b'\xff\xff');m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,128);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003b018,0x14003b0d4,count=10000);actual=struct.unpack('<H',m.mem_read(0x1404f1e88,2))[0];assert actual==c['power'],(c,actual);digest.update(struct.pack('<H',actual))
  for key,(address,fmt)in fields.items():assert struct.unpack('<'+fmt,m.mem_read(address,struct.calcsize(fmt)))[0]==int(c['after'][key]),(c['id'],key)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,producerPairs=pairs,lookups=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-practice-power-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
