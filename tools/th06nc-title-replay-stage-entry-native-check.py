"""Title replay stage-page entry 48cf7..48e77, complete owner slice comparison.

Original animation interrupts and filename selection execute. Validated file
decode is a recorded service; no ANM ticks, rendering, common tail or playback.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['title-replay-stage-entry','sound-queue'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names}
 script="""
import{enterTitleReplayStage}from'./shared/th06nc/title-replay-stage-entry.mjs';import{createHash}from'node:crypto';const cases=[];
for(const selection of [0,14,15,29,30,59])for(const mask of [0,1,4,64,85,127])for(const disabled of [false,true]){
 const initial={state:18,frame:56,selection,replaySelection:selection,pulse:31,totalFrame:99},bytes=new Uint8Array(0x20000),v=new DataView(bytes.buffer),fields=[[0x168b0,'state'],[0x9638,'frame'],[0x28,'selection'],[0x963c,'replaySelection'],[0x30,'pulse'],[0x2c,'totalFrame']];for(const [p,key]of fields)v.setInt32(p,initial[key],true);const offsets=Array.from({length:7},(_,i)=>mask&(1<<i)?120+i*32:null);for(let i=0;i<7;i++)v.setBigUint64(0x7a18+selection*120+64+i*8,BigInt(offsets[i]??0),true);const filename='replay/th6_16.rpy',encoded=new TextEncoder().encode(filename);bytes.set(encoded,0x34+selection*512);const before=Buffer.from(bytes).toString('hex'),group={slots:new Map(Array.from({length:26},(_,i)=>[0x13ba0+i*288,{interrupt:id=>v.setInt16(0x13ba0+i*288+0x8a,id,true)}]))},sounds=[-1,-1,-1],events=[],result=enterTitleReplayStage(group,initial,offsets,{filename,soundSlots:sounds,soundDisabled:disabled,loadReplay:(path,full)=>{events.push({path,full});return 12345;}});for(const [p,key]of fields)v.setInt32(p,result.state[key],true);cases.push({selection,mask,disabled,initial,before,expected:createHash('sha256').update(bytes).digest('hex'),sounds,events,result});}console.log(JSON.stringify(cases));
 """
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
 def hook(m,a,size,u):
  if a==0x140049ab6:m.emu_stop();return
  if a==0x14006af60:
   ptr=m.reg_read(UC_X86_REG_RCX);events.append(dict(path=bytes(m.mem_read(ptr,100)).split(b'\0')[0].decode(),full=bool(m.reg_read(UC_X86_REG_RDX)&255)));m.reg_write(UC_X86_REG_RAX,12345)
   sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x14006af60,end=0x14006af60)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140049ab6,end=0x140049ab6)
 for index,c in enumerate(cases):
  m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,bytes([c['disabled']]));events.clear()
  for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R9,c['selection']),(UC_X86_REG_RDI,8)]:m.reg_write(reg,value)
  m.emu_start(0x140048cf7,0x140048e77,count=100000);raw=bytearray(m.mem_read(n.owner,0x20000));assert struct.unpack_from('<Q',raw,0x168b8)[0]==12345;struct.pack_into('<Q',raw,0x168b8,0);assert hashlib.sha256(raw).hexdigest()==c['expected'],(index,c);assert events==c['events'],(index,events);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'];digest.update(raw)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-replay-stage-entry-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
