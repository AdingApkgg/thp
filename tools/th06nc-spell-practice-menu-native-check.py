"""Spell menu controller 52370..532d9, including actual catalog queries.

Compares declared owner fields, gameplay launch globals, sound slots, full fade
bytes, music globals/transport requests and synchronous presentation-service requests. Catalog initialization and
ANM/text refresh helpers are controlled; their visual work is not proved here.
No title integration, gameplay initializer or audible output is asserted.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

FIELDS={'state':(0x168b0,'i'),'frame':(0x9638,'i'),'selection':(0x28,'i'),'spell':(0x168d3,'B'),'fastEntry':(0x168d4,'B'),'leaving':(0x168d5,'B'),'inputDelay':(0x168d8,'i'),'spellStage':(0x168dc,'i'),'spellOrder':(0x168e0,'i'),'spellScroll':(0x168e4,'i'),'spellDifficulty':(0x168e8,'i'),'stageTransition':(0x168ec,'i'),'orderTransition':(0x168f4,'i'),'difficultyTransition':(0x168fc,'i'),'profileTransition':(0x16900,'i'),'noticePending':(0x16904,'B'),'noticeProfile':(0x16910,'B'),'noticeClock':(0x16914,'i'),'completePending':(0x16918,'B'),'completeStage':(0x1691c,'i'),'completeProfile':(0x16920,'B'),'completeClock':(0x16924,'i')}
ENV={'character':(0x1404f1e80,'B'),'shot':(0x1404f1e81,'B'),'stageIndex':(0x1404f1e84,'i'),'difficulty':(0x1404f27c0,'i'),'practice':(0x1404f27b4,'B'),'spellPractice':(0x1404f27b5,'B'),'spellPracticeIndex':(0x1404f27b8,'B'),'lifeProtection':(0x1404f27c4,'B'),'replayPlayback':(0x1404f278c,'B'),'gameState':(0x140c21d9c,'i'),'titleLaunchPending':(0x140c22138,'B'),'spellWasCaptured':(0x140c22139,'B'),'spellStageWasComplete':(0x140c2213a,'B'),'lastSpellId':(0x140c2213b,'B'),'lastSpellProfile':(0x140c2213c,'B'),'configuredSpellStage':(0x140c21e5c,'i')}

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['spell-practice-menu','spell-practice-table','messagepack','spell-record','sound-queue','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{readFileSync}from'node:fs';import{readSpellPracticeTable}from'./shared/th06nc/spell-practice-table.mjs';import{createSpellMenuState,updateSpellPracticeMenu}from'./shared/th06nc/spell-practice-menu.mjs';import{createSpellRecord}from'./shared/th06nc/spell-record.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),cases=[],recordSets=[];
for(let mode=0;mode<2;mode++){const records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord();r.attempts=mode;r.practiceCaptures.fill(mode);return[id,r];}));recordSets.push(Buffer.concat([...records.values()].map(r=>r.bytes)).toString('hex'));
for(const state of [28,29,30])for(let stage=0;stage<7;stage++)for(const last of [false,true])for(const frame of [9,30])for(const held of [0,16,32,48,64,128,192,256,512,768])for(const repeat of [0,1]){
 const rows=table.filter(r=>r.stageIndex===stage),order=last?Math.max(...rows.map(r=>r.order)):0,row=rows.find(r=>r.order===order),initial=createSpellMenuState({state,frame,fastEntry:true,spellStage:stage,spellOrder:order,spellDifficulty:stage===6?0:row.difficulty,spellScroll:last?20:0,stageTransition:1,orderTransition:10,difficultyTransition:-1,profileTransition:0,noticeClock:1,completeClock:2}),environment={character:last?1:0,shot:last?1:0,stageIndex:3,difficulty:1,practice:true,spellPractice:false,spellPracticeIndex:0,lifeProtection:true,replayPlayback:true,gameState:9,titleLaunchPending:false,spellWasCaptured:false,spellStageWasComplete:false,lastSpellId:0,lastSpellProfile:0,configuredSpellStage:3},keys={held,previous:repeat?held:0,repeat};
 const fade=new NativeFade(),calls=[],soundSlots=[-1,-1,-1],services=Object.fromEntries(['stage','profile','info'].map(kind=>[kind,(_,direction)=>calls.push(kind==='info'?{kind}:{kind,direction})]));
 const music={handle:last?7:-1,playing:Boolean(stage%2),fading:true,fadeStart:99,fadeFrame:66,pendingValue:4,requestActive:true},before={initial,environment:{...environment},keys,fade:[...fade.state],music:{...music},mode};const result=updateSpellPracticeMenu(initial,keys,{table,records,environment,fade,soundSlots,services,music});cases.push({...before,expected:result,afterEnvironment:environment,afterFade:[...fade.state],afterMusic:music,calls});
}
}
const records=new Map(Array.from({length:134},(_,id)=>[id,createSpellRecord()]));
for(const state of [28,29,30,31])for(const fadeMode of [0,1,2,3])for(const leaving of [false,true])for(const fastEntry of [false,true]){
 const initial=createSpellMenuState({state,frame:54,leaving,fastEntry,noticeClock:7,noticePending:true,noticeRecord:table[0],noticeProfile:0,completePending:true,completeFlags:[true,true,true,true,true,true,true],completeStage:0,completeProfile:0}),environment={character:0,shot:0,stageIndex:3,difficulty:1,practice:true,spellPractice:true,spellPracticeIndex:0,lifeProtection:true,replayPlayback:true,gameState:9,titleLaunchPending:false,spellWasCaptured:false,spellStageWasComplete:false,lastSpellId:0,lastSpellProfile:0,configuredSpellStage:3},keys={held:0,previous:0,repeat:0},fade=new NativeFade();fade.v.setInt32(0x34,fadeMode,true);const music={handle:fastEntry?7:-1,playing:true,fading:true,fadeStart:99,fadeFrame:66,pendingValue:4,requestActive:true},before={initial,environment:{...environment},keys,fade:[...fade.state],music:{...music},mode:0},calls=[];const result=updateSpellPracticeMenu(initial,keys,{table,records,environment,fade,music,services:{info:()=>calls.push({kind:'info'})}});cases.push({...before,expected:result,afterEnvironment:environment,afterFade:[...fade.state],afterMusic:music,calls});
}
console.log(JSON.stringify({table,cases,recordSets}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);name=r['name'].encode();b[7:7+len(name)]=name;m.mem_write(n.assets+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',n.assets));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])));fade=n.vm+0x4000;m.mem_write(0x140c22158,struct.pack('<Q',fade));m.mem_write(0x14050966c,struct.pack('<i',-1));m.mem_write(0x140509675,b'\0');m.mem_write(0x140509694,b'\0');calls=[];effects=[]
 musicFields={'handle':(0x50966c,'i'),'playing':(0x50967c,'B'),'fading':(0x509668,'B'),'fadeStart':(0x509660,'i'),'fadeFrame':(0x509664,'i'),'pendingValue':(0x509690,'i'),'requestActive':(0xc21c0c,'B')}
 def hook(m,a,size,u):
  if a==0x140052afe:effects.append(dict(kind='musicFade',frames=30));return
  if a in [0x1400cce50,0x14007f9c0]:
   event=dict(kind='stopMusic'if a==0x1400cce50 else'releaseMusic',handle=m.reg_read(UC_X86_REG_ECX))
   if a==0x1400cce50:event['mode']=m.reg_read(UC_X86_REG_EDX)
   effects.append(event)
  elif a!=0x140076b90:
   kind={0x14004f150:'stage',0x14004f1f0:'profile',0x14004fdd0:'info'}[a];entry={'kind':kind}
   if kind!='info':v=m.reg_read(UC_X86_REG_EDX);entry['direction']=v-0x100000000 if v>=0x80000000 else v
   calls.append(entry)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140076b90,0x14004f150,0x14004f1f0,0x14004fdd0,0x140052afe,0x1400cce50,0x14007f9c0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 digest=hashlib.sha256()
 for index,c in enumerate(data['cases']):
  calls.clear();effects.clear();m.mem_write(n.owner,bytes(0x20000));initial=c['initial'];m.mem_write(fade,bytes(c['fade']));m.mem_write(0x1404f27c8,bytes.fromhex(data['recordSets'][c['mode']]));m.mem_write(0x140a6ec60,struct.pack('<2I',c['keys']['held'],c['keys']['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['keys']['repeat']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1))
  for key,(offset,fmt)in FIELDS.items():m.mem_write(n.owner+offset,struct.pack('<'+fmt,int(initial[key])))
  for key,(offset,fmt)in ENV.items():m.mem_write(offset,struct.pack('<'+fmt,int(c['environment'][key])))
  for key,(offset,fmt)in musicFields.items():m.mem_write(0x140000000+offset,struct.pack('<'+fmt,int(c['music'][key])))
  record=initial['noticeRecord'];m.mem_write(n.owner+0x16908,struct.pack('<Q',n.assets+record['id']*40 if record else 0));m.mem_write(n.owner+0x16928,bytes(initial['completeFlags']))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140052370,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,index
  actual={key:struct.unpack('<'+fmt,m.mem_read(n.owner+offset,struct.calcsize(fmt)))[0]for key,(offset,fmt)in FIELDS.items()}
  expected={key:int(c['expected']['state'][key])for key in FIELDS};assert actual==expected,(index,c['keys'],c['initial'],actual,expected)
  env={key:struct.unpack('<'+fmt,m.mem_read(offset,struct.calcsize(fmt)))[0]for key,(offset,fmt)in ENV.items()};assert env=={key:int(c['afterEnvironment'][key])for key in ENV},(index,'environment',env,c['afterEnvironment'])
  music={key:struct.unpack('<'+fmt,m.mem_read(0x140000000+offset,struct.calcsize(fmt)))[0]for key,(offset,fmt)in musicFields.items()};assert music=={key:int(c['afterMusic'][key])for key in musicFields},(index,'music',music,c['afterMusic']);assert effects==c['expected']['effects'],(index,'effects',effects,c['expected']['effects'])
  noticePointer=struct.unpack('<Q',m.mem_read(n.owner+0x16908,8))[0];notice=c['expected']['state']['noticeRecord'];assert noticePointer==(n.assets+notice['id']*40 if notice else 0),(index,'notice pointer');assert list(m.mem_read(n.owner+0x16928,7))==[int(v)for v in c['expected']['state']['completeFlags']],(index,'complete flags')
  assert calls==c['calls'],(index,'calls',calls,c['calls']);assert list(m.mem_read(fade,56))==c['afterFade'],(index,'fade');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['expected']['soundSlots'],(index,'sounds')
  assert bool(m.reg_read(UC_X86_REG_RAX)&255)==c['expected']['launchReady'],(index,'launchReady');digest.update(json.dumps(actual,sort_keys=True).encode())
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-menu-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':report['cases'],'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
