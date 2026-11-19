"""Spell state27 post-resource tail 4ca1a..4cb5f and replay-card restoration.

Actual ID lookup and viewport helpers. ANM/profile/info refresh services are
observed boundaries; VM setup and those implementations have separate checks.
Compares declared owner fields, stage global, full fade bytes and request order.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['spell-practice-entry','spell-practice-menu','spell-practice-table','messagepack','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 fields={'state':0x168b0,'frame':0x9638,'totalFrame':0x2c,'pulse':0x30,'menuFadeTicks':0x18,'menuFadePreviousDuration':0x168ac,'menuFadeDuration':0x168a8,'menuFadeStartColor':0,'inputDelay':0x168d8,'spellStage':0x168dc,'spellOrder':0x168e0,'spellScroll':0x168e4,'spellDifficulty':0x168e8}
 script="""
import{readFileSync}from'node:fs';import{readSpellPracticeTable}from'./shared/th06nc/spell-practice-table.mjs';import{finishSpellPracticeEntry}from'./shared/th06nc/spell-practice-entry.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),cases=[];
for(const resumeSpell of [false,true])for(const configuredSpellStage of [-1,0,3,6,7])for(const spellPracticeIndex of (resumeSpell?[-1,...Array.from({length:134},(_,i)=>i),256]:[0]))for(const alpha of [0,99]){
 const initial={state:27,frame:51,totalFrame:71,pulse:12,menuFadeTicks:23,menuFadePreviousDuration:17,menuFadeDuration:60,menuFadeStartColor:0xaabbcc,inputDelay:7,spellStage:3,spellOrder:5,spellScroll:2,spellDifficulty:2,resumeSpell,fastEntry:false,leaving:true},environment={stageIndex:99,configuredSpellStage,spellPracticeIndex},fade=new NativeFade(),calls=[],services=Object.fromEntries(['stage','profile','info'].map(kind=>[kind,(_,direction)=>calls.push(kind==='info'?{kind}:{kind,direction})]));fade.v.setInt32(0x28,alpha,true);const before={initial,environment:{...environment},fade:[...fade.state]},state=finishSpellPracticeEntry(initial,{environment,table,fade,services});cases.push({...before,state,afterEnvironment:environment,afterFade:[...fade.state],calls});
}console.log(JSON.stringify({table,cases}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);name=r['name'].encode();b[7:7+len(name)]=name;m.mem_write(n.assets+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',n.assets));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])));fade=n.vm+0x4000;m.mem_write(0x140c22158,struct.pack('<Q',fade));calls=[]
 def hook(m,a,size,u):
  if a!=0x140076b90:
   kind={0x14004f150:'stage',0x14004f1f0:'profile',0x14004fdd0:'info'}[a];event=dict(kind=kind)
   if kind!='info':event['direction']=m.reg_read(UC_X86_REG_EDX)
   calls.append(event)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140076b90,0x14004f150,0x14004f1f0,0x14004fdd0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 digest=hashlib.sha256()
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(0x20000));m.mem_write(fade,bytes(c['fade']));calls.clear()
  for key,offset in fields.items():m.mem_write(n.owner+offset,struct.pack('<i',c['initial'][key]))
  for key,offset in [('resumeSpell',0x168d6),('fastEntry',0x168d4),('leaving',0x168d5)]:m.mem_write(n.owner+offset,bytes([c['initial'][key]]))
  m.mem_write(0x1404f1e84,struct.pack('<i',99));m.mem_write(0x140c21e5c,struct.pack('<i',c['environment']['configuredSpellStage']));m.mem_write(0x1404f27b8,bytes([c['environment']['spellPracticeIndex']&255]))
  for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R12,28)]:m.reg_write(reg,value)
  m.emu_start(0x14004ca1a,0x14004cbf4,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x14004cbf4
  actual={key:struct.unpack('<i',m.mem_read(n.owner+offset,4))[0]for key,offset in fields.items()};assert actual=={key:c['state'][key]for key in fields},(index,actual,c['state'])
  for key,offset in [('resumeSpell',0x168d6),('fastEntry',0x168d4),('leaving',0x168d5)]:assert bool(m.mem_read(n.owner+offset,1)[0])==c['state'][key],(index,key)
  assert struct.unpack('<i',m.mem_read(0x1404f1e84,4))[0]==c['afterEnvironment']['stageIndex'],(index,'stage');assert struct.unpack('<i',m.mem_read(0x140c21e5c,4))[0]==c['afterEnvironment']['configuredSpellStage'],(index,'configured stage');assert bytes(m.mem_read(fade,56))==bytes(c['afterFade']),(index,'fade');assert calls==c['calls'],(index,'calls',calls,c['calls']);digest.update(json.dumps(actual,sort_keys=True).encode())
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-entry-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':report['cases'],'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
