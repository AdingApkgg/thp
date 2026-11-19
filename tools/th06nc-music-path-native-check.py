"""Actual soundtrack path branch7bcf4..7bd7e, before cache/transport.
Original string copies and prefix replacement execute. strncmp import is
controlled. No audio/cache/MUSC-prefix/application claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/music-path.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{resolveMusicPath}from'./shared/th06nc/music-path.mjs';const cases=[];for(const path of[...Array.from({length:18},(_,i)=>'data/bgm/th06_'+String(i+1).padStart(2,'0')+'.opus'),...['','data/bgm/','data/bgm2/th06_01.opus','DATA/bgm/th06_01.opus','data/bgm','data/bgm/X','data/bgm/曲目.opus','data/bgm3/x']])for(const soundtrack of[0,1,2,255])cases.push({path,soundtrack,expected:resolveMusicPath(path,soundtrack)});console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 def prefix(m,a,size,u):
  x=m.reg_read(UC_X86_REG_RCX);y=m.reg_read(UC_X86_REG_RDX);count=m.reg_read(UC_X86_REG_R8);left=bytes(m.mem_read(x,count)).split(b'\0')[0];right=bytes(m.mem_read(y,count)).split(b'\0')[0];m.reg_write(UC_X86_REG_EAX,0 if left==right else 1);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.mem_write(n.vm,b'\xc3');m.mem_write(0x1402c0580,struct.pack('<Q',n.vm));m.hook_add(UC_HOOK_CODE,prefix,begin=n.vm,end=n.vm);digest=hashlib.sha256()
 for index,c in enumerate(cases):
  m.mem_write(n.owner+0x448,bytes([c['soundtrack']]));m.mem_write(n.assets,c['path'].encode()+bytes(300));sp=n.stack+0x8000;m.mem_write(sp,bytes(300));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_RBX,n.assets);m.emu_start(0x14007bcf4,0x14007bd7e,count=10000);actual=bytes(m.mem_read(sp+0x30,260)).split(b'\0')[0];assert actual==c['expected'].encode(),(index,c,actual);digest.update(actual+b'\0')
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-music-path-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','cases','stateSha256']}))
if __name__=='__main__':main()
