"""Playback init 6c1b0, per-frame input 6ba40 and dialogue result 6b9f0.

Real native routines restore globals, seed/count and previous-stage score.
Complete owner and input globals compared; file pointers are normalized.
Decoded files are controlled inputs. Overlay init 6bab0 is a service; task
scheduling, clock platform, UI, full world replay and disk are excluded.
"""
import json,struct,hashlib,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 names=['replay-playback','replay-recorder','replay-assemble','replay-file','rng'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names};script="""
import{ReplayPlayback,replayDialogueTaskResult}from'./shared/th06nc/replay-playback.mjs';import{ReplayRecorder}from'./shared/th06nc/replay-recorder.mjs';import{assembleRecordedReplay}from'./shared/th06nc/replay-assemble.mjs';import{decodeReplayFile}from'./shared/th06nc/replay-file.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const hex=b=>Buffer.from(b).toString('hex'),scenes=[];
for(const profile of [0,3])for(const mode of [0,1,2,3])for(const sequence of [[1,2],[7]]){const recorder=new ReplayRecorder(),e={character:profile>>1,shot:profile&1,difficulty:4,lifeProtection:false,score:123456n,displayScore:123450n,rng:new NativeRng(0xbeef,99),replaySeed:0xbeef,pointTotalCount:1234,playerPower:128,lives:2,bombs:3,powerItemChain:7,deathCount:65535,timingNumerator:1,timingDenominator:1};for(const stageIndex of sequence){e.stageIndex=stageIndex;recorder.initializeStage(e);let previous=0;for(let f=0;f<80;f++){const held=[0,1,2,16,128,0,4,0][Math.floor(f/10)];recorder.advance(held,previous);previous=held;}if(stageIndex!==sequence.at(-1))recorder.finish();}const decoded=decodeReplayFile(assembleRecordedReplay(recorder,{environment:e,name:'ABC',date:'26/11/15'}));decoded.bytes[6]=mode;const playback=new ReplayPlayback(decoded),file=hex(playback.file),initial=hex(playback.bytes),steps=[];for(const stageIndex of [...sequence,3]){const environment={stageIndex,score:17n,displayScore:11n,character:9,shot:9,difficulty:2,lifeProtection:true,defaultLives:9,defaultBombs:9,pointTotalCount:9,playerPower:9,lives:9,bombs:9,powerItemChain:9,deathCount:9,rng:new NativeRng(1,99)},result=playback.initializeStage(environment);steps.push({kind:'init',result,environment:{...environment,score:String(environment.score),displayScore:String(environment.displayScore),rng:{...environment.rng}},owner:hex(playback.bytes)});if(result!==0)continue;for(let frame=0;frame<100;frame++){const input={held:0xabcdf000,previous:0x1234,repeat:7,repeatClock:37},active=frame%13!==0,result=playback.advance(input,{active}),dialogue={active,messageField:frame%3===0?0:-1,indicator:frame%2===0};steps.push({kind:'tick',input,active,result,dialogue,task:replayDialogueTaskResult(playback.v.getInt32(0x30,true),dialogue),owner:hex(playback.bytes)});}}scenes.push({file,initial,steps});}console.log(JSON.stringify(scenes));
""";scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;fileBase=0x75000000;m.mem_map(fileBase,0x200000);digest=hashlib.sha256();checked=0
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x14006bab0,end=0x14006bab0)
 def run(a):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(a,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;value=m.reg_read(UC_X86_REG_EAX);return value-2**32 if value>=2**31 else value
 def normalized():
  raw=bytearray(m.mem_read(n.owner,0x1a0))
  for p in [0,0x70]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,ptr-fileBase+0x1000)
  return bytes(raw)
 fields={'defaultLives':(0xc21de0,'B'),'defaultBombs':(0xc21de1,'B'),'character':(0x4f1e80,'B'),'shot':(0x4f1e81,'B'),'difficulty':(0x4f27c0,'i'),'lifeProtection':(0x4f27c4,'B'),'pointTotalCount':(0x4f27bc,'H'),'playerPower':(0x4f1e88,'H'),'lives':(0x4ff0f0,'B'),'bombs':(0x4ff0f1,'B'),'powerItemChain':(0x4ff0dd,'B'),'deathCount':(0x4f1e60,'i'),'score':(0x4f2798,'Q'),'displayScore':(0x4f2790,'Q')}
 for i,s in enumerate(scenes):
  file=bytearray.fromhex(s['file'])
  for p in range(64,120,8):
   offset=struct.unpack_from('<Q',file,p)[0]
   if offset:struct.pack_into('<Q',file,p,fileBase+offset)
  m.mem_write(fileBase,bytes(file));raw=bytearray.fromhex(s['initial']);struct.pack_into('<Q',raw,0x70,fileBase);m.mem_write(n.owner,bytes(raw));m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm))
  for j,c in enumerate(s['steps']):
   if c['kind']=='init':
    e=c['environment'];m.mem_write(0x1404f1e84,struct.pack('<i',e['stageIndex']))
    for key,(address,fmt)in fields.items():m.mem_write(0x140000000+address,struct.pack('<'+fmt,17 if key=='score'else 11 if key=='displayScore'else 2 if key=='difficulty'else 1 if key=='lifeProtection'else 9))
    m.mem_write(0x140a6ec40,struct.pack('<IH',99,1));assert run(0x14006c1b0)==c['result'],(i,j,'init')
    for key,(address,fmt)in fields.items():assert struct.unpack('<'+fmt,m.mem_read(0x140000000+address,struct.calcsize(fmt)))[0]==int(e[key]),(i,j,key)
    assert struct.unpack('<IH',m.mem_read(0x140a6ec40,6))==(e['rng']['count'],e['rng']['seed']),(i,j,'rng')
   else:
    m.mem_write(0x1404f27b2,bytes([c['active']]));m.mem_write(0x140a6ec60,struct.pack('<2I',0xabcdf000,0x1234));m.mem_write(0x140a6ec48,struct.pack('<i',7));m.mem_write(0x140a6ec5c,struct.pack('<i',37));assert run(0x14006ba40)==c['result'];actual={'held':struct.unpack('<I',m.mem_read(0x140a6ec60,4))[0],'previous':struct.unpack('<I',m.mem_read(0x140a6ec64,4))[0],'repeat':struct.unpack('<i',m.mem_read(0x140a6ec48,4))[0],'repeatClock':struct.unpack('<i',m.mem_read(0x140a6ec5c,4))[0]};assert actual==c['input'],(i,j,'input',actual,c['input']);m.mem_write(n.vm+0x36b0,struct.pack('<i',c['dialogue']['messageField']));m.mem_write(n.vm+0x3900,bytes([c['dialogue']['indicator']]));assert run(0x14006b9f0)==c['task'],(i,j,'dialogue')
   raw=normalized();assert raw.hex()==c['owner'],(i,j,'owner');digest.update(raw);checked+=1
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(scenes),checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-playback-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
