"""Game-owner spell branch 3a42c..3a626: best score and result/replay handoff.

Compares CATK uint64 bytes, declared gameplay globals, full fade bytes, and result
publication fields. Boss/pause gates are supplied inputs; native result painting,
task lifetime, replay continuation and persistence transport are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 source='shared/th06nc/spell-practice-run.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""
import{advanceSpellPracticeRun}from'./shared/th06nc/spell-practice-run.mjs';import{createSpellRecord}from'./shared/th06nc/spell-record.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const cases=[];
for(const state of [0,1,2,3,4])for(const clock of [-1,0,1,120])for(const life of [null,-1,0,20])for(const survival of [false,true])for(const replayPlayback of [false,true])for(const active of [false,true])for(const counter of [0,1])for(const finished of [false,true]){
 const index=cases.length,id=[0,8,130,133][index%4],profile=(index>>2)%4,difficulty=(index>>4)%5,record=createSpellRecord(),score=[0n,0x123456789abcn,0xfffffffffffffffen][index%3],priorScore=[0n,0x123456789abcn,0xffffffffffffffffn][(index>>2)%3],rv=new DataView(record.bytes.buffer);rv.setBigUint64(0x40+(difficulty*4+profile)*8,priorScore,true);
 const environment={spellPractice:true,spellPracticeIndex:id,character:profile>>1,shot:profile&1,difficulty,score,displayScore:1234n,replayPlayback,spellFinished:finished,spellCounter:counter,spellRunState:state,spellRunClock:clock,spellRunBossLife:7,spellRunSurvival:!survival,spellResultVisible:false,gameState:3},before={...environment},boss=life===null?null:{v:new DataView(new ArrayBuffer(0x240))};if(boss){boss.v.setInt32(0x234,life,true);boss.v.setUint8(0xbe,survival?16:0);}
 const fade=index%7===0?null:new NativeFade();if(fade){fade.v.setInt32(0x34,index%3,true);fade.v.setInt32(0x28,[0,127,255][(index>>1)%3],true);fade.v.setUint32(0x20,0x123456,true);}const beforeFade=fade?[...fade.state]:null,beforeRecord=Buffer.from(record.bytes).toString('hex'),event=advanceSpellPracticeRun(environment,{records:new Map([[id,record]]),boss,bossState:{active},fade});cases.push({before,life,survival,active,beforeFade,beforeRecord,after:environment,afterFade:fade?[...fade.state]:null,afterRecord:Buffer.from(record.bytes).toString('hex'),event});
}console.log(JSON.stringify(cases,(_,v)=>typeof v==='bigint'?v.toString():v));
"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;fade=n.vm+0x2000;digest=hashlib.sha256();fields={'spellPracticeIndex':(0x1404f27b8,'B'),'character':(0x1404f1e80,'B'),'shot':(0x1404f1e81,'B'),'difficulty':(0x1404f27c0,'i'),'replayPlayback':(0x1404f278c,'B'),'spellFinished':(0x140aa1e8e,'B'),'spellCounter':(0x140badf60,'i'),'spellRunState':(0x140c2217c,'i'),'spellRunClock':(0x140c22178,'i'),'spellRunBossLife':(0x140c22088,'i'),'spellRunSurvival':(0x140aa1e8d,'B'),'spellResultVisible':(0x1404f27b6,'B'),'gameState':(0x140c21d9c,'i'),'displayScore':(0x1404f2790,'Q'),'score':(0x1404f2798,'Q')}
 for index,c in enumerate(cases):
  for key,(address,fmt)in fields.items():m.mem_write(address,struct.pack('<'+fmt,int(c['before'][key])))
  id=c['before']['spellPracticeIndex'];record=0x1404f27c8+id*0x180;m.mem_write(record,bytes.fromhex(c['beforeRecord']));m.mem_write(0x140a6ec14,bytes([c['active']]));m.mem_write(0x140badf78,struct.pack('<Q',n.vm if c['life']is not None else 0));m.mem_write(n.vm+0x234,struct.pack('<i',c['life']or 0));m.mem_write(n.vm+0xbe,bytes([16 if c['survival']else 0]));m.mem_write(0x140c22158,struct.pack('<Q',fade if c['beforeFade']else 0))
  if c['beforeFade']:m.mem_write(fade,bytes(c['beforeFade']))
  m.mem_write(0x1403e61c4,struct.pack('<iB',73,1));m.mem_write(0x1403e5f7c,struct.pack('<i',41));m.reg_write(UC_X86_REG_R14,0x140000000);m.reg_write(UC_X86_REG_RDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003a42c,0x14003a626,count=10000);assert m.reg_read(UC_X86_REG_RIP)==0x14003a626
  for key,(address,fmt)in fields.items():
   actual=struct.unpack('<'+fmt,m.mem_read(address,struct.calcsize(fmt)))[0];assert actual==int(c['after'][key]),(index,key,actual,c['after'][key])
  assert bytes(m.mem_read(record,0x180)).hex()==c['afterRecord'],(index,'CATK');digest.update(m.mem_read(record,0x180))
  if c['afterFade']:assert list(m.mem_read(fade,56))==c['afterFade'],(index,'fade')
  clock,captured=struct.unpack('<iB',m.mem_read(0x1403e61c4,5));asciiState=struct.unpack('<i',m.mem_read(0x1403e5f7c,4))[0]
  assert (clock,captured,asciiState)==((0,int(c['event']['captured']),0)if c['event']else(73,1,41)),(index,'result publication',clock,captured,asciiState,c['event'],c['before'])
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-practice-run-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
