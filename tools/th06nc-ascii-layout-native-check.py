"""Actual font loader 9700 first two ANM publications: paths, slots and bases.

Loader calls are observed services. File contents, ANM execution and GPU are
covered separately; later pause/front publications are outside this slice.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/ascii-layout.mjs';before=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();refs=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{asciiFontAssets}from'./shared/th06nc/ascii-layout.mjs';console.log(JSON.stringify(asciiFontAssets));"],cwd=ROOT));n=Native();m=n.m;calls=[]
 def hook(m,a,size,u):
  ptr=m.reg_read(UC_X86_REG_R8);calls.append(dict(path=bytes(m.mem_read(ptr,100)).split(b'\0')[0].decode(),slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x1400020b0,end=0x1400020b0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140009700,0x140009738,count=10000);assert calls==[dict(path='data/'+r['file'],slot=r['slot'],base=r['base'])for r in refs],calls;assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==before;report=dict(scope=__doc__,publications=calls,sourceSha256={source:before},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ascii-layout-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'publications':calls}))

if __name__=='__main__':main()
