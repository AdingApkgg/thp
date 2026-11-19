"""Actual spellpractice.msgpack through native 76b90..77540.

Compares published count and every initialized record field/name. Resource I/O,
heap allocation/free, memory primitives and security-cookie check are controlled.
Allocation padding, menu drawing, launch and spell gameplay are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 resource='runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack'
 sources=['shared/th06nc/spell-practice-table.mjs','shared/th06nc/messagepack.mjs']
 hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="import{readFileSync}from'node:fs';import{readSpellPracticeTable}from'./shared/th06nc/spell-practice-table.mjs';console.log(JSON.stringify(readSpellPracticeTable(readFileSync('"+resource+"'))));"
 expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT))
 raw=(ROOT/resource).read_bytes();n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x800000);cursor=heap
 m.mem_write(n.assets,raw)
 malloc=n.vm+0x9000;free=n.vm+0x9010
 m.mem_write(0x1402c0370,struct.pack('<Q',malloc));m.mem_write(0x1402c0378,struct.pack('<Q',free))
 def hook(m,a,size,u):
  nonlocal cursor
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x1400387a0:
   m.mem_write(m.reg_read(UC_X86_REG_R8),struct.pack('<I',len(raw)));m.reg_write(UC_X86_REG_RAX,n.assets)
  elif a==malloc:
   count=m.reg_read(UC_X86_REG_RCX);result=cursor;cursor+=(count+15)&~15;assert cursor<heap+0x800000;m.mem_write(result,bytes(count));m.reg_write(UC_X86_REG_RAX,result)
  elif a==0x1402bdef4:
   count=m.reg_read(UC_X86_REG_R8);left=bytes(m.mem_read(m.reg_read(UC_X86_REG_RCX),count));right=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),count));value=next((x-y for x,y in zip(left,right)if x!=y),0);m.reg_write(UC_X86_REG_RAX,value&0xffffffffffffffff)
  elif a in [0x1402bdee2,0x1402bdee8]:
   dst=m.reg_read(UC_X86_REG_RCX);count=m.reg_read(UC_X86_REG_R8);data=bytes([m.reg_read(UC_X86_REG_RDX)&255])*count if a==0x1402bdee2 else bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),count));m.mem_write(dst,data);m.reg_write(UC_X86_REG_RAX,dst)
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1400387a0,malloc,free,0x1402bdef4,0x1402bdee2,0x1402bdee8,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp)
 try:m.emu_start(0x140076b90,n.stack+0xf000,count=20000000)
 except Exception:
  print('native failure',hex(m.reg_read(UC_X86_REG_RIP)), 'stack', bytes(m.mem_read(m.reg_read(UC_X86_REG_RSP),64)).hex());raise
 assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 pointer=struct.unpack('<Q',m.mem_read(0x14007752b+0xbaac95,8))[0]
 count=struct.unpack('<I',m.mem_read(0x140077532+0xbaab5a,4))[0]
 assert count==len(expected),(count,len(expected));assert pointer
 actual=[]
 for i in range(count):
  b=bytes(m.mem_read(pointer+i*40,40));id,stage,sub,difficulty,order,midboss=struct.unpack_from('<BBHBBB',b)
  actual.append(dict(id=id,stageIndex=stage,subroutine=sub,difficulty=difficulty,order=order,midboss=midboss,name=b[7:39].split(b'\0')[0].decode('utf-8')))
 assert actual==expected
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,entries=count,resource=resource,resourceSha256=hashlib.sha256(raw).hexdigest(),recordsSha256=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-table-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
