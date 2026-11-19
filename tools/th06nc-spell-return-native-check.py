"""Title spell-return notice producer 55a30..55c4e.

Executes actual catalog traversal, CATK checks and stage-completion query;
catalog lazy initialization and the title-owner memset are controlled services.
Compares the complete cleared title-owner bytes with its declared native entry
fields, launch/resume globals and expected new-capture/completion requests.
Task allocation/registration, ANMs/fonts, audio and application return excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['spell-practice-return','spell-practice-table','spell-record','messagepack']]
 hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-spell-return-cases.mjs'],cwd=ROOT));n=Native();m=n.m;owner=0x140c07240
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);name=r['name'].encode();b[7:7+len(name)]=name;m.mem_write(n.assets+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',n.assets));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])))
 def service(m,a,size,u):
  if a==0x1402bdee2:
   assert m.reg_read(UC_X86_REG_RCX)==owner
   assert m.reg_read(UC_X86_REG_R8)==0x1a728
   m.mem_write(owner,bytes(0x1a728));m.reg_write(UC_X86_REG_RAX,owner)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140076b90,0x1402bdee2]:m.hook_add(UC_HOOK_CODE,service,begin=a,end=a)
 env={'character':0x1404f1e80,'shot':0x1404f1e81,'resumeSpell':0x1404f27b7,'titleLaunchPending':0x140c22138,'lastSpellProfile':0x140c2213c,'lastSpellId':0x140c2213b,'spellPracticeIndex':0x1404f27b8,'spellWasCaptured':0x140c22139,'spellStageWasComplete':0x140c2213a}
 digest=hashlib.sha256();mode=None;noticeCount=completeCount=0
 for index,c in enumerate(data['cases']):
  if mode!=c['mode']:mode=c['mode'];m.mem_write(0x1404f27c8,bytes.fromhex(data['recordSets'][mode]))
  m.mem_write(owner,b'\xa5'*0x1a728);m.mem_write(0x1404f27b4,b'\0');m.mem_write(0x1404f27b0,b'\x01')
  for key,address in env.items():m.mem_write(address,bytes([c['environment'][key]&255]))
  for reg,value in [(UC_X86_REG_RCX,int(c['startup'])),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
  m.emu_start(0x140055a30,0x140055c4e,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x140055c4e
  s=c['state'];expected=bytearray(0x1a728)
  struct.pack_into('<i',expected,0x168b0,27 if s['resumeSpell']else 15 if c['startup']else 0)
  if s['resumeSpell']:expected[0x168d3]=expected[0x168d6]=1
  if s['noticePending']:
   noticeCount+=1;expected[0x16904]=1;expected[0x16910]=s['noticeProfile'];rowIndex=next(i for i,r in enumerate(data['table'])if r['id']==s['noticeRecord']['id']);struct.pack_into('<Q',expected,0x16908,n.assets+rowIndex*40)
  if s['completePending']:completeCount+=1;expected[0x16918]=1;expected[0x16920]=s['completeProfile'];struct.pack_into('<i',expected,0x1691c,s['completeStage'])
  actual=bytes(m.mem_read(owner,len(expected)));assert actual==expected,(index,c,[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,expected))if a!=b][:12])
  for key,address in env.items():assert m.mem_read(address,1)[0]==(c['after'][key]&255),(index,key)
  assert m.mem_read(0x1404f27b0,1)==b'\0';digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),notices=noticeCount,completions=completeCount,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-return-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['passed','cases','notices','completions','stateSha256']}))

if __name__=='__main__':main()
