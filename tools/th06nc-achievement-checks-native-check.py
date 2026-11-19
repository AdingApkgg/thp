"""Original title post-launch and gameplay-init CATK achievement decision fragments.
Executes comparisons/134-slot loop, stops before native platform calls. Full
fade/task initialization and Steam persistence are separate boundaries.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/achievement-checks.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
 import{titleLaunchAchievement,encounteredAllSpells}from'./shared/th06nc/achievement-checks.mjs';
 const title=Array.from({length:32},(_,launchFrom)=>({launchFrom,result:titleLaunchAchievement(launchFrom)})),spells=[];
 for(const value of [1,32768,65535])for(let missing=-1;missing<134;missing++){
 const attempts=Array.from({length:134},(_,id)=>id===missing?0:value),records=new Map(attempts.map((attempts,id)=>[id,{attempts,captures:65535,practiceAttempts:[999],practiceCaptures:[999]}]));
 spells.push({attempts,result:encounteredAllSpells(records)});
 }
 console.log(JSON.stringify({title,spells}));
 """
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;endpoint=None
 def stop(m,a,size,u):
  nonlocal endpoint
  endpoint=a;m.emu_stop()
 for a in [0x14004c4b8,0x14004cbdf,0x14003b968,0x14003b99b]:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
 digest=hashlib.sha256()
 for c in data['title']:
  m.mem_write(n.owner+0x168cc,struct.pack('<i',c['launchFrom']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);endpoint=None;m.emu_start(0x14004c4ab,n.stack+0xf000,count=20)
  actual='Achievement01'if endpoint==0x14004c4b8 else None;assert actual==c['result'],c;digest.update(str(actual).encode())
 for c in data['spells']:
  raw=bytearray(134*384)
  for i,value in enumerate(c['attempts']):struct.pack_into('<H',raw,i*384+60,value)
  m.mem_write(0x1404f27c8,bytes(raw));endpoint=None;m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003b949,n.stack+0xf000,count=1000);assert endpoint in [0x14003b968,0x14003b99b];assert (endpoint==0x14003b968)==c['result'];digest.update(bytes([c['result']]))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,titleCases=len(data['title']),spellCases=len(data['spells']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-achievement-checks-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,titleCases=report['titleCases'],spellCases=report['spellCases'])))
if __name__=='__main__':main()
