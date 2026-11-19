"""Configuration publication through actual TitleScene3/9/14 and original decision owners.
Full44 cfg bytes compare. Real original selection/ANM logic runs, file services,
common owner/draw/task lifetime and audible output excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/title-scene.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-title-config-cases.mjs'],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;baseline=bytearray(0x20000);digest=hashlib.sha256()
 for slot in data['baseline']:
  raw=bytearray.fromhex(slot['bytes'])
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,n.assetByFile[slot['file']]+ptr)
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,n.manager+0x608+(ptr-1)*64)
  baseline[slot['offset']:slot['offset']+288]=raw
 def stop(m,a,size,u):m.emu_stop()
 for a in [0x140049ab6,0x14004cbf4,0x14004cbe6]:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
 def service(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0)
 for a in [0x140076050,0x140076af0]:m.hook_add(UC_HOOK_CODE,service,begin=a,end=a)
 for index,c in enumerate(data['cases']):
  initial=c['initial'];m.mem_write(n.owner,bytes(baseline));m.mem_write(0x140c21da4,bytes(c['before']));m.mem_write(0x1404ff0f4,b'\x63'*96)
  for p,key in [(0x168b0,'state'),(0x9638,'frame'),(0x28,'selection'),(0x30,'pulse'),(0x2c,'totalFrame')]:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
  m.mem_write(n.owner+0x168d1,bytes([0,0]));m.mem_write(0x1404f27c0,struct.pack('<i',initial['difficulty']));m.mem_write(0x1404f1e80,bytes([0,0]));m.mem_write(0x140a6ec60,struct.pack('<II',c['held'],0));m.mem_write(0x140a6ec48,bytes(4));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x140c22158,bytes(8))
  for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,4),(UC_X86_REG_R13,11),(UC_X86_REG_R15,256),(UC_X86_REG_RDI,8),(UC_X86_REG_RDX,c['held']),(UC_X86_REG_R8,0),(UC_X86_REG_R9,0),(UC_X86_REG_R10,3),(UC_X86_REG_R11,6)]:m.reg_write(reg,value)
  m.emu_start({3:0x14004832d,9:0x14004b0f5,14:0x14004bced}[initial['state']],n.stack,count=1000000)
  actual=bytes(m.mem_read(0x140c21da4,44));assert actual==bytes(c['after']),(index,c,list(actual));digest.update(actual)
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-config-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(data['cases']))))
if __name__=='__main__':main()
