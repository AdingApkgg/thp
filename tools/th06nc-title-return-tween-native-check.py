"""Full46e50 title return tween. Input, drawing and surrounding tasks excluded."""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
def main():
 source='shared/th06nc/title-selection-return.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""import{advanceTitleReturnTween}from'./shared/th06nc/title-selection-return.mjs';const cases=[];for(const state of [2,3,4])for(const returnTweenTicks of [-1,0,1,2,23,24,25,2147483647])for(const returnTweenX of [-1,0,.5,1,2])for(const returnTweenY of [-1,0,.5,1,2]){const v=new DataView(new ArrayBuffer(288));v.setFloat32(0xe4,7,true);v.setFloat32(0xe8,9,true);const initial={state,returnTweenTicks,returnTweenX,returnTweenY},group={slots:new Map([[0x9640+59*288,{v}]])},after=advanceTitleReturnTween(group,initial);cases.push({initial,after,x:v.getFloat32(0xe4,true),y:v.getFloat32(0xe8,true)});}console.log(JSON.stringify(cases));"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for c in cases:
  initial=c['initial'];m.mem_write(n.owner,bytes(0x16900))
  for offset,key,fmt in [(0x168b0,'state','i'),(0x1685c,'returnTweenTicks','i'),(0x16860,'returnTweenY','f'),(0x16864,'returnTweenX','f')]:m.mem_write(n.owner+offset,struct.pack('<'+fmt,initial[key]))
  m.mem_write(n.owner+0xd984,struct.pack('<ff',7,9));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140046e50,n.stack+0xf000,count=1000);raw=bytes(m.mem_read(n.owner+0xd984,8));assert raw==struct.pack('<ff',c['x'],c['y']),c;assert struct.unpack('<i',m.mem_read(n.owner+0x1685c,4))[0]==c['after']['returnTweenTicks'],c;digest.update(raw)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-return-tween-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
