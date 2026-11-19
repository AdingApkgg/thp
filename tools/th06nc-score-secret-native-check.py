"""Actual Lunatic Score secret producers 6e020 + 6e190, keyboard and raw pad.
Full result owner, all96 CLRD bytes, sounds. No application input/persistence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/score-secret-unlock.mjs','shared/th06nc/sound-queue.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{createHash}from'node:crypto';import{advanceScoreSecret}from'./shared/th06nc/score-secret-unlock.mjs';const cases=[],sha=b=>createHash('sha256').update(b).digest('hex');
function test(progress,keyboardMask,previous,padProgress,controllerMask,padPrevious){const index=cases.length,bytes=new Uint8Array(0xbb48),v=new DataView(bytes.buffer),cleared=Uint8Array.from({length:96},(_,i)=>i),sounds=index%3===0?[28,-1,-1]:index%3===1?[10,11,12]:[-1,-1,-1],beforeSounds=[...sounds],soundDisabled=index%5===0;for(const[p,x]of[[0x4430,progress],[0x4434,previous],[0x4448,padProgress],[0x444c,padPrevious]])v.setInt32(p,x,true);advanceScoreSecret({v},{keyboardMask,controllerMask,cleared,soundSlots:sounds,soundDisabled});cases.push({progress,keyboardMask,previous,padProgress,controllerMask,padPrevious,beforeSounds,soundDisabled,sounds,ownerSha256:sha(bytes),cleared:[...cleared]});}
for(let progress=0;progress<12;progress++)for(let keyboardMask=0;keyboardMask<256;keyboardMask++)for(const previous of[0,keyboardMask])test(progress,keyboardMask,previous,0,0,0);
for(const padProgress of[-1,0,1,2,3,4])for(let controllerMask=0;controllerMask<64;controllerMask++)for(const padPrevious of[0,controllerMask,63])test(0,0,0,padProgress,controllerMask,padPrevious);
for(let mask=0;mask<64;mask++)test(11,128,0,3,mask,0);
console.log(JSON.stringify(cases));
"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();scans=[0x2e,0x26,0x1e,0x1f,0x17,0x22,0x12,0x13];addresses=[0xc21e8e,0xc21e86,0xc21e7e,0xc21e7f,0xc21e77,0xc21e82,0xc21e72,0xc21e73]
 for address,scan in zip(addresses,scans):m.mem_write(0x140000000+address,bytes([scan]))
 for index,c in enumerate(cases):
  m.mem_write(n.owner,bytes(0xbb48));m.mem_write(0x1404ff0f4,bytes(range(96)));m.mem_write(0x140509670,struct.pack('<3i',*c['beforeSounds']));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140c21f70,bytes(256))
  for bit,scan in enumerate(scans):m.mem_write(0x140c21f70+scan,bytes([128 if c['keyboardMask']&(1<<bit)else 0]))
  for p,key in[(0x4430,'progress'),(0x4434,'previous'),(0x4448,'padProgress'),(0x444c,'padPrevious')]:m.mem_write(n.owner+p,struct.pack('<i',c[key]))
  m.mem_write(0x140c21e58,struct.pack('<I',c['controllerMask']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006e020,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=bytes(m.mem_read(n.owner,0xbb48));assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,c,'owner');assert list(m.mem_read(0x1404ff0f4,96))==c['cleared'],(index,c,'cleared');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,c,'sounds');digest.update(actual);digest.update(bytes(c['cleared']))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-secret-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases),stateSha256=digest.hexdigest())))
if __name__=='__main__':main()

