"""Actual7bb80 name read and7bc00 write prefix. CRT strncpy supplied; file queue/allocation excluded."""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/config-name.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""import{readConfigName,writeConfigName}from'./shared/th06nc/config-name.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(let value=0;value<256;value++)for(let pos=0;pos<8;pos++){const config=Uint8Array.from({length:44},(_,i)=>(i*17+value)&255);config.fill(65,32,40);config[32+pos]=value;const input=Uint8Array.from({length:9},(_,i)=>(i*31+value)&255);const read=readConfigName(config),after=config.slice();writeConfigName(after,input);cases.push({config:hex(config),input:hex(input),read:hex(read),after:hex(after)});}console.log(JSON.stringify(cases));"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 def strncpy(m,a,size,u):
  dest=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);count=m.reg_read(UC_X86_REG_R8);raw=bytes(m.mem_read(src,count));raw=raw.split(b'\0')[0].ljust(count,b'\0');m.mem_write(dest,raw);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,dest)
 def memset(m,a,size,u):
  dest=m.reg_read(UC_X86_REG_RCX);value=m.reg_read(UC_X86_REG_RDX)&255;count=m.reg_read(UC_X86_REG_R8);m.mem_write(dest,bytes([value])*count);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,dest)
 m.hook_add(UC_HOOK_CODE,memset,begin=0x1402bdee2,end=0x1402bdee2)
 m.mem_write(0x1402c0588,struct.pack('<Q',n.vm));m.mem_write(n.vm,b'\xc3');m.hook_add(UC_HOOK_CODE,strncpy,begin=n.vm,end=n.vm)
 for c in cases:
  m.mem_write(0x140c21da4,bytes.fromhex(c['config']));m.mem_write(n.owner,b'\xa5'*16);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.owner);m.emu_start(0x14007bb80,n.stack+0xf000,count=1000);actual=bytes(m.mem_read(n.owner,9));assert actual.hex()==c['read'];digest.update(actual)
  m.mem_write(n.owner,bytes.fromhex(c['input']));m.reg_write(UC_X86_REG_RSP,sp);m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RDX,n.owner);m.emu_start(0x14007bc00,0x14007bc2b,count=1000);actual=bytes(m.mem_read(0x140c21da4,44));assert actual.hex()==c['after'];digest.update(actual)
 assert sha==hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-config-name-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
