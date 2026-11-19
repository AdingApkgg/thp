"""Real update dispatcher 3be80 + replay input 6ba40 + dialogue task 6b9f0.

Controlled message/indicator windows replace the world/message task; native
callbacks otherwise execute in order. Per-display input frame, input globals,
world callback count and sound flush count compared. Actual MSG/world, draw,
task registration and browser scheduling are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['task-update-chain','replay-playback'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names};script="""
import{runUpdateChain}from'./shared/th06nc/task-update-chain.mjs';import{ReplayPlayback,replayDialogueTaskResult}from'./shared/th06nc/replay-playback.mjs';const cases=[];
for(const active of [false,true])for(const indicator of [false,true]){const file=new Uint8Array(176),v=new DataView(file.buffer);[[0,1,0],[20,0,1],[9999999,0,0]].forEach((r,i)=>r.forEach((x,j)=>v.setInt32(140+i*12+j*4,x,true)));const playback=new ReplayPlayback({bytes:file,stageOffsets:[120,null,null,null,null,null,null]});playback.cursor=140;playback.stageEnd=176;playback.v.setBigUint64(0,0x1000n+140n,true);const input={held:0x1000,previous:0,repeat:0,repeatClock:0};let world=0,sounds=0,messageField=-1;const tail={update:()=>replayDialogueTaskResult(playback.v.getInt32(0x30,true),{active,messageField,indicator}),next:null},middle={update:()=>{world++;const f=playback.v.getInt32(0x30,true);messageField=f>=15&&f<45?0:-1;return 1;},next:tail},head={update:()=>playback.advance(input,{active}),next:middle},frames=[];for(let display=0;display<100;display++){input.held=0x1000;const status={value:42},result=runUpdateChain(head,{status,consumeSounds:()=>sounds++});frames.push({frame:playback.v.getInt32(0x30,true),input:{...input},world,sounds,value:result.value,status:status.value});}cases.push({active,indicator,frames});}console.log(JSON.stringify(cases));
 """;cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;head=0x1404f1440;nodeBase=n.vm+0x1000;fileBase=n.vm+0x2000;messageBase=n.assets+0x100000;world=sounds=0;digest=hashlib.sha256()
 def hook(m,a,size,u):
  nonlocal world,sounds
  if a==0x140076a30:sounds+=1
  elif a==n.vm+0x9000:
   world+=1;frame=struct.unpack('<i',m.mem_read(n.owner+0x30,4))[0];m.mem_write(messageBase+0x36b0,struct.pack('<i',0 if 15<=frame<45 else -1));m.reg_write(UC_X86_REG_EAX,1)
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140076a30,n.vm+0x9000]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for c in cases:
  world=sounds=0;m.mem_write(n.owner,bytes(0x1a0));m.mem_write(n.owner,struct.pack('<Q',fileBase+140));m.mem_write(messageBase,bytes(0x4000));m.mem_write(messageBase+0x36b0,struct.pack('<i',-1));m.mem_write(messageBase+0x3900,bytes([c['indicator']]));m.mem_write(0x140a6ec08,struct.pack('<Q',messageBase));m.mem_write(0x1404f27b2,bytes([c['active']]));m.mem_write(0x140a6ec60,struct.pack('<2I',0x1000,0));m.mem_write(0x140a6ec48,bytes(4));m.mem_write(0x140a6ec5c,bytes(4));m.mem_write(head,bytes(64));m.mem_write(head+0x28,struct.pack('<Q',nodeBase))
  for i,fn in enumerate([0x14006ba40,n.vm+0x9000,0x14006b9f0]):
   raw=bytearray(64);struct.pack_into('<Q',raw,8,fn);struct.pack_into('<Q',raw,0x38,n.owner);struct.pack_into('<Q',raw,0x28,nodeBase+(i+1)*64 if i<2 else 0);m.mem_write(nodeBase+i*64,bytes(raw))
  raw=bytearray(176)
  for i,row in enumerate([(0,1,0),(20,0,1),(9999999,0,0)]):struct.pack_into('<3i',raw,140+i*12,*row)
  m.mem_write(fileBase,bytes(raw))
  for display,expected in enumerate(c['frames']):
   m.mem_write(0x140a6ec60,struct.pack('<I',0x1000));m.mem_write(n.vm,struct.pack('<i',42));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.vm);m.emu_start(0x14003be80,n.stack+0xf000,count=100000);held,previous=struct.unpack('<2I',m.mem_read(0x140a6ec60,8));actual=dict(frame=struct.unpack('<i',m.mem_read(n.owner+0x30,4))[0],input=dict(held=held,previous=previous,repeat=struct.unpack('<i',m.mem_read(0x140a6ec48,4))[0],repeatClock=struct.unpack('<i',m.mem_read(0x140a6ec5c,4))[0]),world=world,sounds=sounds,value=m.reg_read(UC_X86_REG_RAX)&255,status=struct.unpack('<i',m.mem_read(n.vm,4))[0]);assert actual==expected,(c['active'],c['indicator'],display,actual,expected);digest.update(json.dumps(actual,sort_keys=True).encode())
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=4,displayTicks=400,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-dialogue-chain-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'displayTicks':400,'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
