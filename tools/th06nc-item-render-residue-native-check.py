"""Native item draw11b0a and spawn426e0: inactive item presentation cache.
Original normal/above-screen draws prime different cache bytes. Inactive draw
retains them; all7 types/3 drop modes followed by one real ANM tick and draw
reconstruct identical complete owners, VM requests and RNG. Physics bytes and
active presentation remain strict. GPU pixels/task scheduling excluded.
"""
import base64,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['tools/th06nc-pool-comparison.mjs','shared/th06nc/item-draw.mjs','shared/th06nc/item-pool.mjs','shared/th06nc/anm-rebind.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};n=Native();n.load_title([dict(file='etama3.anm',archive='th06CM.dat',base=0x200,slot=6),dict(file='etama3_2.anm',archive='th06CM.dat',base=0x29a,slot=0x34),dict(file='etama4.anm',archive='th06CM.dat',base=0x2ba,slot=7)]);m=n.m;base=0x140baf0d8;size=1025*0x160;draws=[];pairs=[];digest=hashlib.sha256()
 def hook(m,a,size,u):
  draws.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),288)));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x1400067f0,end=0x1400067f0)
 def spawn(kind,mode,y):
  m.mem_write(0x140c07238,bytes(4));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f27b5,bytes(1));m.mem_write(n.vm,struct.pack('<3f',100,y,.5));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8D,kind);m.reg_write(UC_X86_REG_R9D,mode);m.emu_start(0x1400426e0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 def draw():
  draws.clear();m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_R12D,0);m.reg_write(UC_X86_REG_R14D,64);m.emu_start(0x140011b0a,0x140011c2a,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x140011c2a;return bytes(m.mem_read(base,size)),list(draws)
 for kind in range(7):
  primed=[]
  for y in [-100.,100.]:
   m.mem_write(base,bytes(size));spawn(kind,1,y);draw();m.mem_write(base,bytes(1));m.mem_write(base+0x10,struct.pack('<3f',100,200,.5));before=bytes(m.mem_read(base,size));after,requests=draw();assert after==before and requests==[];primed.append(before)
  assert primed[0]!=primed[1];pairs.append([base64.b64encode(p[:0x160]).decode()for p in primed])
  for mode in range(3):
   outcomes=[]
   for before in primed:
    m.mem_write(base,before);spawn(kind,mode,200.);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RDX,base+0x38);m.emu_start(0x1400069b0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;owner,requests=draw();outcomes.append((owner,requests,bytes(m.mem_read(0x140a6ec40,6))));digest.update(owner)
   assert outcomes[0]==outcomes[1],(kind,mode)
 script="""import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{itemDrawIndependentBytes}from'./tools/th06nc-pool-comparison.mjs';const hash=x=>createHash('sha256').update(x).digest('hex');for(const pair of JSON.parse(readFileSync(0,'utf8'))){const blocks=pair.map(raw=>{const b=new Uint8Array(1025*0x160);b.set(Buffer.from(raw,'base64'));return b;});const before=blocks.map(hash),normal=blocks.map(itemDrawIndependentBytes);if(hash(normal[0])!==hash(normal[1]))throw Error('Draw residue retained');if(blocks.some((b,i)=>hash(b)!==before[i]))throw Error('Snapshot mutated');blocks.forEach(b=>b[0]=1);if(hash(itemDrawIndependentBytes(blocks[0]))===hash(itemDrawIndependentBytes(blocks[1])))throw Error('Active presentation hidden');}console.log('ok');"""
 assert subprocess.check_output(['node','--input-type=module','-e',script],input=json.dumps(pairs).encode(),cwd=ROOT).strip()==b'ok';assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,inactivePairs=7,spawnReuseCases=21,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-item-render-residue-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,inactivePairs=7,spawnReuseCases=21)))
if __name__=='__main__':main()
