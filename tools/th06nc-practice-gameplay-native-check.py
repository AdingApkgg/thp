"""Practice Power correction and actual full Result-17 dispatcher.

Compare full Result owner, full global fade bytes, scene request and return.
No task graph, Result construction/loading, file I/O or drawing claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/practice-gameplay.mjs','shared/th06nc/fade.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{createHash}from'node:crypto';import{advancePracticeResult,practiceStartingPower}from'./shared/th06nc/practice-gameplay.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const cases=[],powers=[];for(let stage=1;stage<=6;stage++)for(const power of [0,8,64,128,65535])powers.push({stage,power,expected:practiceStartingPower(stage,power)});for(const exists of [false,true])for(const flag of [0,1])for(let mode=0;mode<=4;mode++)for(const alpha of [-1,0,1,128,255,256,2147483647]){const raw=Uint8Array.from({length:0xbb48},(_,i)=>(i*31+cases.length)&255);raw[0x9e98]=flag;new DataView(raw.buffer).setInt32(0x9e94,17,true);const fade=new NativeFade();fade.state.set(Uint8Array.from({length:56},(_,i)=>(i*17+cases.length)&255));fade.v.setInt32(0x34,mode,true);fade.v.setInt32(0x28,alpha,true);const before=Buffer.from(fade.state).toString('hex'),seed=cases.length,result=advancePracticeResult({bytes:raw},exists?fade:null);cases.push({exists,flag,mode,alpha,seed,before,after:Buffer.from(fade.state).toString('hex'),owner:createHash('sha256').update(raw).digest('hex'),result});}console.log(JSON.stringify({cases,powers}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for c in data['powers']:
  m.mem_write(n.owner,bytes(0x956));m.mem_write(n.owner+0x954,b'\1');m.mem_write(n.owner+0x28,struct.pack('<H',c['power']));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_EDX,c['stage']);m.emu_start(0x14003afe5,0x14003b00b,count=100);actual=bytes(m.mem_read(n.owner+0x28,2));assert struct.unpack('<H',actual)[0]==c['expected'];digest.update(actual)
 # Dispatcher calls only the stack-cookie verifier on this branch.
 def ret(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,ret,begin=0x1402bcf20,end=0x1402bcf20)
 for c in data['cases']:
  raw=bytearray((i*31+c['seed'])&255 for i in range(0xbb48));raw[0x9e98]=c['flag'];struct.pack_into('<i',raw,0x9e94,17);m.mem_write(n.owner,bytes(raw));m.mem_write(n.vm,bytes.fromhex(c['before']));m.mem_write(0x140c22158,struct.pack('<Q',n.vm if c['exists']else 0));m.mem_write(0x140c21d9c,struct.pack('<i',99));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006e3a0,n.stack+0xf000,count=10000)
  assert m.reg_read(UC_X86_REG_EAX)==c['result'],(c,'return');actual=bytes(m.mem_read(n.owner,0xbb48));assert hashlib.sha256(actual).hexdigest()==c['owner'],(c,'owner');assert bytes(m.mem_read(n.vm,56)).hex()==c['after'],(c,'fade');assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==(1 if c['result']==0 else 99);digest.update(actual)
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,powerCases=len(data['powers']),resultCases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-practice-gameplay-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'powerCases':len(data['powers']),'resultCases':len(data['cases'])}))
if __name__=='__main__':main()
