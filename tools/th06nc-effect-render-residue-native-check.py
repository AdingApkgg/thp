"""Native draw2b310 and spawn2b0d0: inactive VM draw-position residue.
Twin inactive slots retain different VM+c8 values without draw requests; active
world-position publication and all21 original spawn/ANM bindings followed by
draw erase those differences, with identical full owners/VM requests/RNG. GPU
pixels and native per-display scheduling are separate boundaries.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+p+'.mjs'for p in ['effect-compare','effect-pool','effect-draw','anm-rebind']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""import{effectDrawIndependentBytes}from'./shared/th06nc/effect-compare.mjs';const a=new Uint8Array(513*0x198),b=a.slice();new DataView(b.buffer).setFloat32(3*0x198+0x108,123,true);const equal=(a,b)=>Buffer.from(a).equals(Buffer.from(b));if(!equal(effectDrawIndependentBytes(a),effectDrawIndependentBytes(b)))throw Error('Inactive residue retained');a[3*0x198+0x14]=b[3*0x198+0x14]=1;if(equal(effectDrawIndependentBytes(a),effectDrawIndependentBytes(b)))throw Error('Active position hidden');a.fill(0);b.fill(0);b[512*0x198+0x108]=1;if(equal(effectDrawIndependentBytes(a),effectDrawIndependentBytes(b)))throw Error('Sentinel position hidden');console.log(JSON.stringify({passed:true}));"""
 assert json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))['passed'];n=Native();n.load_title([dict(file='etama4.anm',archive='th06CM.dat',base=698,slot=7),dict(file='eff01.anm',archive='th06ST.dat',base=723,slot=11)]);m=n.m;base=0x140a6ecd0;cursorAddress=0x140aa1e6c;draws=[];digest=hashlib.sha256()
 def hook(m,a,size,u):
  if a==0x140004dc0:draws.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),288)))
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for address in [0x140004dc0,0x14007af40]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 def draw():
  draws.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,base);m.emu_start(0x14002b310,n.assets,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.assets;return bytes(m.mem_read(base,513*0x198)),list(draws)
 for active in [0,1]:
  outcomes=[]
  for vector in [(1.,2.,3.),(-101.,999.,.5)]:
   raw=bytearray(513*0x198);p=3*0x198;raw[p+0x14]=active;struct.pack_into('<3f',raw,p+0x108,*vector);struct.pack_into('<3f',raw,p+0x174,100.5,200.25,-2.);m.mem_write(base,bytes(raw));outcomes.append(draw())
  if active:assert outcomes[0]==outcomes[1]
  else:assert outcomes[0][0]!=outcomes[1][0]and outcomes[0][1]==outcomes[1][1]==[]
 for kind in range(21):
  outcomes=[]
  for vector in [(1.,2.,3.),(-101.,999.,.5)]:
   raw=bytearray(513*0x198);struct.pack_into('<3f',raw,3*0x198+0x108,*vector);m.mem_write(base,bytes(raw));m.mem_write(cursorAddress,struct.pack('<i',3));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(n.vm,struct.pack('<3f',100.5,200.25,-2));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<I',0x89abcdef))
   for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_EDX,kind),(UC_X86_REG_R8,n.vm),(UC_X86_REG_R9D,1)]:m.reg_write(reg,value)
   m.emu_start(0x14002b0d0,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;owner,requests=draw();outcomes.append((owner,requests,bytes(m.mem_read(0x140a6ec40,6))));digest.update(owner)
  assert outcomes[0]==outcomes[1],kind
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,drawGatePairs=2,spawnReuseTypes=21,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-effect-render-residue-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,drawGatePairs=2,spawnReuseTypes=21)))
if __name__=='__main__':main()
