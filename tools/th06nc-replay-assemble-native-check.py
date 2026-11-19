"""Full record-mode replay writer 6c420, real assembly/RNG/codec and cleanup.

Captured file-delivery service compares every output byte. Native heap pointer
identities normalize to recorder tokens. Local time, allocation/free, memcpy,
file delivery and task removal are services; stack padding is zeroed. No disk,
actual game scheduling, source seed producer or playback equivalence claimed.
"""
import json,hashlib,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 names=['replay-recorder','replay-assemble','replay-file','rng'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names};script="""
import{ReplayRecorder}from'./shared/th06nc/replay-recorder.mjs';import{assembleRecordedReplay}from'./shared/th06nc/replay-assemble.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const hex=b=>Buffer.from(b).toString('hex'),scenes=[],snapshot=r=>({owner:hex(r.bytes),header:hex(r.header),stages:r.stages.map((b,i)=>b?hex(b.subarray(0,Math.max(32,r.ends[i]))):null)});
for(const profile of [0,3])for(const lifeProtection of [false,true])for(const sequence of [[1],[1,2,3],[7]])for(const preserveRecording of [false,true])for(const speed of [[0,0],[1,1],[3,4]]){
 const r=new ReplayRecorder(),environment={character:profile>>1,shot:profile&1,difficulty:profile?4:1,lifeProtection,playerPower:128,lives:2,bombs:3,powerItemChain:1,pointTotalCount:17,deathCount:3,replaySeed:0xbeef,rng:new NativeRng(0xbeef,99),score:1234567890n,displayScore:1234500000n,timingNumerator:speed[0],timingDenominator:speed[1]};for(const stageIndex of sequence){environment.stageIndex=stageIndex;r.initializeStage(environment);let previous=0;for(let frame=0;frame<40;frame++){const held=[0,1,16,2,32,4,128,0][Math.floor(frame/5)];r.advance(held,previous);previous=held;}if(stageIndex!==sequence.at(-1))r.finish();}const before=snapshot(r),encoded=assembleRecordedReplay(r,{environment,name:new Uint8Array([65,66,32,32,32,32,32,32,0]),date:'26/11/15',preserveRecording}),after=snapshot(r);scenes.push({environment:{...environment,rng:undefined,score:String(environment.score),displayScore:String(environment.displayScore)},preserveRecording,before,after,encoded:hex(encoded),rng:{seed:environment.rng.seed,count:environment.rng.count}});
}console.log(JSON.stringify(scenes));
""";scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;stageBase=heap+0x100000;packet=0x76000000;m.mem_map(heap,0x800000);m.mem_map(packet,0x200000);captured=[];digest=hashlib.sha256()
 for ptr,shim in [(0x1402c0370,n.vm+0x9000),(0x1402c0378,n.vm+0x9010),(0x1402c05a8,n.vm+0x9020),(0x1402c05a0,n.vm+0x9030),(0x1402c05b0,n.vm+0x9040)]:m.mem_write(ptr,struct.pack('<Q',shim))
 def hook(m,a,size,u):
  if a==n.vm+0x9000:
   count=m.reg_read(UC_X86_REG_RCX);assert count<0x200000;m.mem_write(packet,bytes(count));m.reg_write(UC_X86_REG_RAX,packet)
  elif a==n.vm+0x9020:m.reg_write(UC_X86_REG_RAX,1700000000)
  elif a==n.vm+0x9030:m.reg_write(UC_X86_REG_RAX,n.vm+0x2000)
  elif a==n.vm+0x9040:m.mem_write(m.reg_read(UC_X86_REG_RCX),b'26/11/15\0');m.reg_write(UC_X86_REG_RAX,8)
  elif a==0x1402bdee8:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),m.reg_read(UC_X86_REG_R8))))
  elif a==0x140039610:captured.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),m.reg_read(UC_X86_REG_R8))));m.reg_write(UC_X86_REG_RAX,1)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [n.vm+0x9000,n.vm+0x9010,n.vm+0x9020,n.vm+0x9030,n.vm+0x9040,0x1402bdee8,0x140039610,0x1402bcf20,0x1400126e0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def pointer(p,to_native):
  if not p:return 0
  if to_native:return heap if p==0x1000 else stageBase+p-0x100000
  return 0x1000 if p==heap else p-stageBase+0x100000
 for index,s in enumerate(scenes):
  b=s['before'];raw=bytearray.fromhex(b['owner']);header=bytearray.fromhex(b['header'])
  for p in [0,*range(0x38,0x70,8),0x70]:struct.pack_into('<Q',raw,p,pointer(struct.unpack_from('<Q',raw,p)[0],True))
  for p in range(64,120,8):struct.pack_into('<Q',header,p,pointer(struct.unpack_from('<Q',header,p)[0],True))
  m.mem_write(n.owner,bytes(raw));m.mem_write(heap,bytes(header));m.mem_write(0x140a6ec38,struct.pack('<Q',n.owner))
  for i,stage in enumerate(b['stages']):
   if stage:m.mem_write(stageBase+i*0x100000,bytes(0x9e33c));m.mem_write(stageBase+i*0x100000,bytes.fromhex(stage))
  e=s['environment'];m.mem_write(0x1404f1e84,struct.pack('<i',e['stageIndex']));m.mem_write(0x1404f2790,struct.pack('<Q',int(e['displayScore'])));m.mem_write(0x1404f2798,struct.pack('<Q',int(e['score'])));m.mem_write(0x140c21d0c,struct.pack('<2f',e['timingNumerator'],e['timingDenominator']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(n.vm+0x3000,b'replay/th6_01.rpy\0');m.mem_write(n.vm+0x3100,b'AB      \0');m.mem_write(n.stack+0x6000,bytes(0x3000));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,n.vm+0x3000);m.reg_write(UC_X86_REG_R8,n.vm+0x3100);m.reg_write(UC_X86_REG_R9D,int(s['preserveRecording']));captured.clear();m.emu_start(0x14006c420,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;assert len(captured)==1,(index,'delivery');assert captured[0].hex()==s['encoded'],(index,'file',next((i for i,(a,b)in enumerate(zip(captured[0],bytes.fromhex(s['encoded'])))if a!=b),None),captured[0][:120].hex(),s['encoded'][:240]);assert struct.unpack('<IH',m.mem_read(0x140a6ec40,6))==(s['rng']['count'],s['rng']['seed']),(index,'rng');raw=bytearray(m.mem_read(n.owner,0x1a0));header=bytearray(m.mem_read(heap,120))
  for p in [0,*range(0x38,0x70,8),0x70]:struct.pack_into('<Q',raw,p,pointer(struct.unpack_from('<Q',raw,p)[0],False))
  for p in range(64,120,8):struct.pack_into('<Q',header,p,pointer(struct.unpack_from('<Q',header,p)[0],False))
  assert raw.hex()==s['after']['owner'],(index,'owner');assert header.hex()==s['after']['header'],(index,'header');digest.update(captured[0]);digest.update(raw)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(scenes),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-assemble-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
