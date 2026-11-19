"""Actual th06.cfg validation/acceptance7b92b..7b9e2, reset7bad0, and
th06.env validation/acceptance7b9f4..7ba5d.
Loader file I/O and startup orchestration excluded. Full44-byte config and
runtime ten-byte key owner compared. Default reset receives runtime keys.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/config-file.mjs';hashes={source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()};script="""
import{readFileSync}from'node:fs';import{acceptGameConfig,resetGameConfig,validEnvironmentConfig}from'./shared/th06nc/config-file.mjs';const base=new Uint8Array(readFileSync('H:/Games/th/06nc/th06.cfg')),cases=[],resets=[],environments=[],hex=b=>Buffer.from(b).toString('hex');
function test(bytes){const result=acceptGameConfig(bytes);cases.push({raw:hex(bytes),result:result?{bytes:hex(result.bytes),keys:hex(result.keys)}:null});}
for(let length=0;length<=60;length++){const b=new Uint8Array(length);b.set(base.subarray(0,length));test(b);}
for(const offset of[12,13,14,15,16,17,18,19,20,21,22,23,24,33,40])for(let value=0;value<256;value++){const b=base.slice();b[offset]=value;test(b);}
for(let i=0;i<256;i++){const b=Uint8Array.from({length:44},(_,k)=>(i*53+k*31)&255),keys=Uint8Array.from({length:10},(_,k)=>(i+k*17)&255),before=hex(b);resetGameConfig(b,keys);resets.push({before,keys:hex(keys),result:hex(b)});}
for(let length=0;length<20;length++){const raw=new Uint8Array(length);raw.set([2,1,0,0].slice(0,length));environments.push({raw:hex(raw),valid:validEnvironmentConfig(raw)});}
for(let offset=0;offset<12;offset++)for(let value=0;value<256;value++){const raw=new Uint8Array([2,1,0,0,0,3,1,0,1,21,22,23]);raw[offset]=value;environments.push({raw:hex(raw),valid:validEnvironmentConfig(raw)});}
console.log(JSON.stringify({cases,resets,environments}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 def stop(m,a,size,u):m.emu_stop()
 hooks=[m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)for a in[0x14007b6d4,0x14007b75a]]
 for index,c in enumerate(data['cases']):
  raw=bytes.fromhex(c['raw']);m.mem_write(n.owner,raw+bytes(64));m.mem_write(0x140c21da4,bytes([0xa5])*44);m.mem_write(0x140a6ec50,bytes([0x5a])*10);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R15,len(raw));m.reg_write(UC_X86_REG_RSI,0);m.emu_start(0x14007b92b,n.stack,count=1000);accepted=m.reg_read(UC_X86_REG_RIP)==0x14007b75a;assert accepted==bool(c['result']),(index,c)
  actual=bytes(m.mem_read(0x140c21da4,44));keys=bytes(m.mem_read(0x140a6ec50,10));assert actual.hex()==(c['result']['bytes']if accepted else 'a5'*44),(index,c,'config');assert keys.hex()==(c['result']['keys']if accepted else '5a'*10),(index,c,'keys');digest.update(actual);digest.update(keys)
 for hook in hooks:m.hook_del(hook)
 for index,c in enumerate(data['resets']):
  m.mem_write(0x140c21da4,bytes.fromhex(c['before']));m.mem_write(0x140a6ec50,bytes.fromhex(c['keys']));m.mem_write(n.stack,bytes(0x10000));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x14007bad0,n.stack+0xf000,count=1000);actual=bytes(m.mem_read(0x140c21da4,44));assert actual.hex()==c['result'],(index,actual.hex(),c);digest.update(actual)
 hooks=[m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)for a in[0x14007b7f0,0x14007b832]]
 for index,c in enumerate(data['environments']):
  raw=bytes.fromhex(c['raw']);m.mem_write(n.owner,raw+bytes(32));m.mem_write(0x140c21dfc,bytes([0xa5])*12);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R15,len(raw));m.emu_start(0x14007b9f4,n.stack,count=1000);accepted=m.reg_read(UC_X86_REG_RIP)==0x14007b832;assert accepted==c['valid'],(index,c);actual=bytes(m.mem_read(0x140c21dfc,12));assert actual==(raw if accepted else bytes([0xa5])*12),(index,c,'environment');digest.update(actual)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==hashes[source]
 report=dict(scope=__doc__,cases=len(data['cases']),resets=len(data['resets']),environments=len(data['environments']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],originalConfigSha256=hashlib.sha256(Path(n.target['executable']).with_name('th06.cfg').read_bytes()).hexdigest(),passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-config-file-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','resets','environments','stateSha256']}))
if __name__=='__main__':
 from pathlib import Path
 main()
