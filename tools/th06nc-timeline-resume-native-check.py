"""Original timeline resume and boss-spawn inhibition are independent globals.

Compare actual 363c2..36ec7 with synthetic timeline markers and message gates.
The original shipped Extra timeline has no opcode13 checkpoint; its resume
request remains set while its independent boss flag permits the hidden spawn.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 script="""
import {EclTimeline} from './shared/th06nc/ecl-timeline.mjs';
const cases=[];
for(const marker of [false,true])for(const requested of [false,true])for(const blocked of [false,true]){
 const bytes=Buffer.alloc(32);bytes.writeInt16LE(40,0);bytes.writeInt16LE(marker?13:14,4);bytes.writeUInt16LE(8,6);bytes.writeInt16LE(80,8);bytes.writeInt16LE(9,12);bytes.writeUInt16LE(8,14);bytes.writeInt16LE(-1,16);
 const timeline={offset:0,end:20,instructions:[{offset:0,time:40,opcode:marker?13:14,length:8,args:bytes.subarray(8,8)},{offset:8,time:80,opcode:9,length:8,args:bytes.subarray(16,16)}]},environment={timelineResumeRequested:requested,suppressSpawn:blocked,messageField3b50:0,messageField36b0:-1},t=new EclTimeline(timeline,{environment});t.cursor=8;t.frame=80;t.messageClock=7;t.runDue();cases.push({marker,requested,blocked,bytes:bytes.toString('hex'),state:{cursor:t.cursor,frame:t.frame,messageClock:t.messageClock,requested:environment.timelineResumeRequested,blocked:environment.suppressSpawn},checkpoint:t.checkpoint});
}
console.log(JSON.stringify(cases));
"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;owner=0x140aa1e90;digest=hashlib.sha256()
 m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner))
 for c in cases:
  m.mem_write(n.assets,bytes.fromhex(c['bytes']));m.mem_write(owner,bytes(0x10d1e0));m.mem_write(owner+0x10c128,struct.pack('<Q',n.assets+8));m.mem_write(owner+0x10c0bc,struct.pack('<i',80));m.mem_write(0x140a6eb88,struct.pack('<Q',n.assets if c['marker'] else 0));m.mem_write(0x140a6eb90,bytes([c['requested']]));m.mem_write(0x140a6ec14,bytes([c['blocked']]));m.mem_write(n.owner+0x3b50,struct.pack('<I',0));m.mem_write(n.owner+0x36b0,struct.pack('<i',-1));m.mem_write(0x1404ff0d8,struct.pack('<i',7))
  for reg,val in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,owner),(UC_X86_REG_RCX,owner)]:m.reg_write(reg,val)
  m.emu_start(0x1400363c2,0x140036ec7,count=100000)
  actual=dict(cursor=struct.unpack('<Q',m.mem_read(owner+0x10c128,8))[0]-n.assets,frame=struct.unpack('<i',m.mem_read(owner+0x10c0bc,4))[0],messageClock=struct.unpack('<i',m.mem_read(0x1404ff0d8,4))[0],requested=bool(m.mem_read(0x140a6eb90,1)[0]),blocked=bool(m.mem_read(0x140a6ec14,1)[0]));assert actual==c['state'],(c,actual);assert c['checkpoint']==(0 if c['marker']else None);digest.update(json.dumps(actual,sort_keys=True).encode())
 paths=['shared/th06nc/ecl-timeline.mjs','shared/th06nc/message-progress.mjs'];report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-timeline-resume-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
