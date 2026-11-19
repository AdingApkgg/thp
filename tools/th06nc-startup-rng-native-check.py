"""Native boot7a7fe..7a812 samples GetNowCount(0), publishes low16 seed and count0.
The platform clock call is a controlled boundary. This checks the original boot
contract; complete shared-RNG task lifetime and browser/Windows clock epochs
are not established by this fragment.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 n=Native();m=n.m;clock=0;requests=[];digest=hashlib.sha256()
 def time(m,a,size,u):
  requests.append(m.reg_read(UC_X86_REG_ECX));m.reg_write(UC_X86_REG_EAX,clock&0xffffffff);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,time,begin=0x1400b0370,end=0x1400b0370)
 times=[0,1,65535,65536,65537,0x7fffffff,0x80000000,0xffffffff]+[i*104729&0xffffffff for i in range(256)]
 script="import{seedStartupRng}from'./shared/th06nc/startup-rng.mjs';console.log(JSON.stringify("+json.dumps(times)+".map(time=>seedStartupRng({seed:123,count:456},time))));"
 expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))
 for index,clock in enumerate(times):
  requests.clear();m.mem_write(0x140a6ec40,bytes([0xa5])*6);m.reg_write(UC_X86_REG_EDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007a7fe,0x14007a812,count=20);actual=bytes(m.mem_read(0x140a6ec40,6));assert struct.unpack('<IH',actual)==(expected[index]['count'],expected[index]['seed']);assert requests==[0];digest.update(actual)
 source='shared/th06nc/startup-rng.mjs';report=dict(scope=__doc__,cases=len(times),stateSha256=digest.hexdigest(),sourceSha256={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-startup-rng-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(times))))
if __name__=='__main__':main()
