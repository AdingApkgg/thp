"""Actual application dispatch from previous state 10 to requested state 7.

Runs 79d7a table selection through Result registration. Allocation, zeroing,
Result construction and registration are controlled services; the native branch
chooses dirty=1, ordinary state9 / stage-practice state17 and priorities13/16.
This proves the handoff choice, not complete application task lifecycle.
"""
import hashlib,json,struct
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 n=Native();m=n.m;result=n.assets+0x100000;events=[];states=[]
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x1402bcf40:assert m.reg_read(UC_X86_REG_RCX)==0xbb48;events.append('allocate');m.reg_write(UC_X86_REG_RAX,result)
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes(m.reg_read(UC_X86_REG_R8)));m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
  elif a==0x14006df00:assert m.reg_read(UC_X86_REG_RCX)==result;events.append('construct');m.reg_write(UC_X86_REG_RAX,result)
  elif a==0x14006dd20:
   assert m.reg_read(UC_X86_REG_RCX)==result;events.append(dict(kind='register',state=struct.unpack('<i',m.mem_read(result+0x9e94,4))[0],dirty=bytes(m.mem_read(result+0x9e99,1))[0],updatePriority=m.reg_read(UC_X86_REG_RDX),drawPriority=m.reg_read(UC_X86_REG_R8)));m.reg_write(UC_X86_REG_RAX,0)
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1402bcf40,0x1402bdee2,0x14006df00,0x14006dd20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for practice in [0,1,255]:
  for counter in [0,0x7fffffff,0xffffffff]:
   m.mem_write(n.owner,bytes(0x500));m.mem_write(n.owner+0x428,struct.pack('<3i',10,7,-1));m.mem_write(n.owner+0x290,struct.pack('<I',counter));m.mem_write(0x1404f27b4,bytes([practice]));sp=n.stack+0x8000;m.mem_write(sp+0x28,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_EBX,0);events.clear();m.emu_start(0x140079d7a,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;expected=['allocate','construct',dict(kind='register',state=17 if practice else 9,dirty=1,updatePriority=13,drawPriority=16)];assert events==expected,events;assert struct.unpack('<3i',m.mem_read(n.owner+0x428,12))==(7,7,10);assert struct.unpack('<I',m.mem_read(n.owner+0x290,4))[0]==(counter+1)&0xffffffff;assert m.reg_read(UC_X86_REG_EAX)==1;states.append(dict(practice=practice,counter=counter,events=list(events)))
 source='tools/th06nc-ending-result-handoff-native-check.py';report=dict(scope=__doc__,cases=len(states),states=states,sourceSha256={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ending-result-handoff-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(states)}))
if __name__=='__main__':main()
