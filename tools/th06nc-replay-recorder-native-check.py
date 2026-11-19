"""Replay record owner initialization, stage headers, input-change stream and seal.

Actual 6b271 constructor fields, 6bfd0 init, 6b970 tick and 6c3a0 finish.
Full owner/header and used stage bytes compared with heap pointer identities
normalized. Allocations are zero-filled services; task registration, recording
seed producer/timing, file assembly/I/O and playback are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/replay-recorder.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{ReplayRecorder}from'./shared/th06nc/replay-recorder.mjs';import{createHash}from'node:crypto';const sha=b=>createHash('sha256').update(b).digest('hex'),hex=b=>Buffer.from(b).toString('hex'),scenes=[];
for(const character of [0,1])for(const shot of [0,1])for(const difficulty of [0,4])for(const lifeProtection of [false,true])for(const spellPractice of [false,true])for(const sequence of [[1,2,3],[7]]){
 const r=new ReplayRecorder(),initial=hex(r.bytes),steps=[],snapshot=()=>({owner:hex(r.bytes),header:hex(r.header),stages:r.stages.map((b,i)=>b?{length:Math.max(32,r.ends[i]),sha256:sha(b.subarray(0,Math.max(32,r.ends[i])))}:null)});
 for(const stageIndex of sequence){
  const environment={character,shot,difficulty,lifeProtection,spellPractice,spellPracticeIndex:37,stageIndex,replaySeed:(0xbeef+stageIndex)&65535,pointTotalCount:65535-stageIndex,playerPower:511-stageIndex,lives:stageIndex,bombs:stageIndex+1,powerItemChain:stageIndex+2,deathCount:65536-stageIndex,score:String(9999999990n-BigInt(stageIndex)*123457n)},result=r.initializeStage(environment);steps.push({kind:'init',environment,result,...snapshot()});let previous=0;
  for(let frame=0;frame<96;frame++){const held=[0,1,1,2,16,32,4,128,1025,0][Math.floor(frame/5)%10],active=frame%17!==0,result=r.advance(held,previous,{active});steps.push({kind:'tick',held,previous,active,result,...snapshot()});previous=held;}
  r.finish();steps.push({kind:'finish',...snapshot()});r.finish();steps.push({kind:'finish',...snapshot()});r.advance(1,0);steps.push({kind:'tick',held:1,previous:0,active:true,result:1,...snapshot()});
 }scenes.push({initial,steps});
}console.log(JSON.stringify({scenes}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x800000);stageBase=heap+0x100000;owner=n.owner;digest=hashlib.sha256();alloc=[];checked=0;currentStage=1
 def hook(m,a,size,u):
  size=m.reg_read(UC_X86_REG_RCX);ptr=heap if size==120 else stageBase+(currentStage-1)*0x100000;assert size in [120,0x9e33c];m.mem_write(ptr,bytes(size));alloc.append(size);m.reg_write(UC_X86_REG_RAX,ptr);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000))
 for a in [0x1402bcf40,n.vm+0x9000]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(a):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(a,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;return m.reg_read(UC_X86_REG_EAX)
 def pointer(p):return 0 if p==0 else 0x1000 if p==heap else p-stageBase+0x100000
 for i,s in enumerate(data['scenes']):
  m.mem_write(owner,bytes(0x1a0));m.reg_write(UC_X86_REG_RSI,owner);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14006b271,0x14006b2cb,count=10000);assert bytes(m.mem_read(owner,0x1a0)).hex()==s['initial'],(i,'constructor')
  for j,c in enumerate(s['steps']):
   if c['kind']=='init':
    e=c['environment'];currentStage=e['stageIndex'];alloc.clear()
    for key,address,fmt in [('stageIndex',0x4f1e84,'i'),('character',0x4f1e80,'B'),('shot',0x4f1e81,'B'),('difficulty',0x4f27c0,'i'),('lifeProtection',0x4f27c4,'B'),('spellPractice',0x4f27b5,'B'),('spellPracticeIndex',0x4f27b8,'B'),('replaySeed',0x4ff268,'H'),('pointTotalCount',0x4f27bc,'H'),('playerPower',0x4f1e88,'H'),('lives',0x4ff0f0,'B'),('bombs',0x4ff0f1,'B'),('powerItemChain',0x4ff0dd,'B'),('deathCount',0x4f1e60,'H'),('score',0x4f2798,'Q')]:m.mem_write(0x140000000+address,struct.pack('<'+fmt,int(e[key])))
    assert run(0x14006bfd0)==c['result'],(i,j,'init return')
   elif c['kind']=='tick':m.mem_write(0x1404f27b2,bytes([c['active']]));m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));assert run(0x14006b970)==c['result']
   else:run(0x14006c3a0)
   raw=bytearray(m.mem_read(owner,0x1a0))
   for p in [0,*range(0x38,0x70,8),0x70]:struct.pack_into('<Q',raw,p,pointer(struct.unpack_from('<Q',raw,p)[0]))
   assert raw.hex()==c['owner'],(i,j,c['kind'],'owner',raw.hex(),c['owner']);header=bytearray(m.mem_read(heap,120))
   for p in range(64,120,8):struct.pack_into('<Q',header,p,pointer(struct.unpack_from('<Q',header,p)[0]))
   assert header.hex()==c['header'],(i,j,'header')
   for k,stage in enumerate(c['stages']):
    if stage:assert hashlib.sha256(bytes(m.mem_read(stageBase+k*0x100000,stage['length']))).hexdigest()==stage['sha256'],(i,j,k,'stage')
   digest.update(raw);digest.update(header);checked+=1
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,scenes=len(data['scenes']),checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-recorder-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
