"""Title playback launch helper 4d680, real native body and complete fade bytes.

Compares launch globals, path, state/frame, sound queue and return value.
Decoded headers/stages and spell catalogue are controlled; 76b90 catalogue
construction is a service. File I/O, title list/draw and gameplay are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['title-replay-launch','sound-queue','fade'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names}
 script="""
import{prepareTitleReplayLaunch}from'./shared/th06nc/title-replay-launch.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const cases=[];
for(const mode of [0,1,2,3])for(const profile of [0,3])for(const stageIndex of [0,2,6])for(const firstStage of [0,2,6])for(const present of [false,true])for(const alpha of [0,127,255])for(const disabled of [false,true]){
 const bytes=new Uint8Array(120+7*32),stageOffsets=Array(7).fill(null);bytes[6]=mode;bytes[7]=profile;bytes[8]=mode===3?19:4;stageOffsets[firstStage]=120+firstStage*32;bytes[stageOffsets[firstStage]+13]=firstStage+1;bytes[stageOffsets[firstStage]+14]=firstStage+2;
 const initial={state:20,frame:47,selection:stageIndex,pulse:31},before={spellPractice:true,spellPracticeIndex:88,stageIndex:99,difficulty:2,replay:false,replayFilename:'OLD',character:9,shot:9,lifeProtection:true,lives:9,bombs:9,replayStartStage:99},environment={...before},spellRecords=present?[{id:7,stageIndex:1,difficulty:0},{id:19,stageIndex:5,difficulty:3}]:[{id:7,stageIndex:1,difficulty:0}],fade=new NativeFade();fade.v.setInt32(0x28,alpha,true);fade.v.setInt32(0x34,3,true);fade.v.setInt32(0x2c,170,true);const fadeBefore=Buffer.from(fade.state).toString('hex'),sounds=[-1,-1,-1],filename='replay/th6_16.rpy',result=prepareTitleReplayLaunch(initial,{bytes,stageOffsets},stageIndex,{environment,filename,spellRecords,fade,soundSlots:sounds,soundDisabled:disabled});cases.push({mode,profile,stageIndex,firstStage,present,disabled,initial,before,filename,spellRecords,bytes:Buffer.from(bytes).toString('hex'),stageOffsets,fadeBefore,result,environment,fade:Buffer.from(fade.state).toString('hex'),sounds});}console.log(JSON.stringify(cases));
 """
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;fileBase=n.vm+0x1000;fadeBase=n.vm+0x3000;spellBase=n.vm+0x4000;digest=hashlib.sha256()
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140076b90,end=0x140076b90)
 fields={'spellPractice':(0x4f27b5,'B'),'spellPracticeIndex':(0x4f27b8,'i'),'stageIndex':(0x4f1e84,'i'),'difficulty':(0x4f27c0,'i'),'replay':(0x4f278c,'B'),'character':(0x4f1e80,'B'),'shot':(0x4f1e81,'B'),'lifeProtection':(0x4f27c4,'B'),'lives':(0x4ff0f0,'B'),'bombs':(0x4ff0f1,'B'),'replayStartStage':(0x4ff264,'i')}
 for index,c in enumerate(cases):
  m.mem_write(n.owner,bytes(0x20000));m.mem_write(n.owner+0x168b8,struct.pack('<Q',fileBase));m.mem_write(n.owner+0x963c,struct.pack('<i',15));m.mem_write(n.owner+0x34+15*512,c['filename'].encode()+b'\0');m.mem_write(n.owner+0x168b0,struct.pack('<i',c['initial']['state']));m.mem_write(n.owner+0x9638,struct.pack('<i',c['initial']['frame']))
  raw=bytearray.fromhex(c['bytes'])
  for i,offset in enumerate(c['stageOffsets']):
   if offset is not None:struct.pack_into('<Q',raw,64+i*8,fileBase+offset)
  m.mem_write(fileBase,bytes(raw));m.mem_write(fadeBase,bytes.fromhex(c['fadeBefore']));m.mem_write(0x140c22158,struct.pack('<Q',fadeBase));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,bytes([c['disabled']]))
  m.mem_write(0x1404ff164,b'OLD\0'+bytes(252))
  for name,(offset,fmt)in fields.items():m.mem_write(0x140000000+offset,struct.pack('<'+fmt,c['before'][name]))
  m.mem_write(0x140c2208c,struct.pack('<i',len(c['spellRecords'])));m.mem_write(0x140c221c0,struct.pack('<Q',spellBase))
  for i,r in enumerate(c['spellRecords']):
   raw=bytearray(40);raw[0]=r['id'];raw[1]=r['stageIndex'];raw[4]=r['difficulty'];m.mem_write(spellBase+i*40,bytes(raw))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_EDX,c['stageIndex']);m.emu_start(0x14004d680,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual={name:struct.unpack('<'+fmt,m.mem_read(0x140000000+offset,struct.calcsize('<'+fmt)))[0]for name,(offset,fmt)in fields.items()};actual['replayFilename']=bytes(m.mem_read(0x1404ff164,512)).split(b'\0')[0].decode();assert actual==c['environment'],(index,actual,c['environment']);assert bool(m.reg_read(UC_X86_REG_RAX)&255)==c['result']['accepted'],index
  for offset,key in [(0x168b0,'state'),(0x9638,'frame')]:assert struct.unpack('<i',m.mem_read(n.owner+offset,4))[0]==c['result']['state'][key],(index,key)
  fade=bytes(m.mem_read(fadeBase,56));assert fade.hex()==c['fade'],(index,'fade');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,'sounds');digest.update(fade);digest.update(json.dumps(actual,sort_keys=True).encode())
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-replay-launch-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
