"""Native spell timeline branch 36260..363bd with full initial ECL execution.

Actual 131-row catalog; synthetic per-subroutine ECL life commands demonstrate
ID-to-subroutine routing and time-zero execution. Compares full enemy pool bytes
by SHA, selected slot bytes, init flag and repeat behavior. Controls catalog lazy
init, memcpy and cookie; real spell scripts/gameplay/GPU remain separate.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['spell-practice-spawn','spell-practice-table','enemy-pool','ecl-tick'];hashes={'shared/th06nc/'+s+'.mjs':hashlib.sha256((ROOT/'shared/th06nc'/f'{s}.mjs').read_bytes()).hexdigest()for s in sources}
 subprocess.run(['node','tools/th06nc-spell-practice-spawn-cases.mjs'],cwd=ROOT,check=True);data=json.loads((ROOT/'tools/tmp/th06nc-spell-practice-spawn-cases.json').read_text(encoding='utf-8'));n=Native();m=n.m;catalog=n.assets;programBase=n.assets+0x10000;program=bytes.fromhex(data['program']);m.mem_write(programBase,program);owner=0x140aa1e90;poolBase=owner+8
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);m.mem_write(catalog+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',catalog));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])))
 for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(n.manager+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
 m.mem_write(0x140a6eb80,struct.pack('<Q',n.manager));m.mem_write(0x1404f27b5,b'\1');m.mem_write(0x1404f27c0,struct.pack('<i',1))
 def hook(m,a,size,u):
  if a==0x1402bdee8:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),m.reg_read(UC_X86_REG_R8))))
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1402bdee8,0x1402bdee2,0x1402bcf20,0x140076b90]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 template_script="import{createEnemyTemplate}from'./shared/th06nc/enemy-pool.mjs';console.log(Buffer.from(createEnemyTemplate()).toString('hex'));";template=bytes.fromhex(subprocess.check_output(['node','--input-type=module','-e',template_script],cwd=ROOT).decode().strip());m.mem_write(owner+0x10c130,template);digest=hashlib.sha256()
 for index,c in enumerate(data['cases']):
  m.mem_write(poolBase,bytes(256*0x10b0))
  for i in range(c['occupied']):m.mem_write(poolBase+i*0x10b0+0xbc,b'\x80')
  m.mem_write(0x1404f27b8,bytes([c['id']&255]));m.mem_write(0x140aa1e7f,bytes([c['started']]))
  for repeat in range(2):
   sp=n.stack+0x8000;m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(0x140036260,0x140036ef8,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x140036ef8
  assert bool(m.mem_read(0x140aa1e7f,1)[0])==c['afterStarted'],(index,'started');actual=bytearray(m.mem_read(poolBase,256*0x10b0))
  if c['slot']is not None:
   p=c['slot']*0x10b0;value=struct.unpack_from('<Q',actual,p+0x88)[0];struct.pack_into('<Q',actual,p+0x88,value-programBase);wanted=bytes.fromhex(c['enemy']);assert actual[p:p+0x10b0]==wanted,(index,c['id'],[(hex(j),x,y)for j,(x,y)in enumerate(zip(actual[p:p+0x10b0],wanted))if x!=y][:20])
  assert hashlib.sha256(actual).hexdigest()==c['poolSha256'],(index,'pool');digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-practice-spawn-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
