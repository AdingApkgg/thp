"""Title Score/Music/Credits and fade-gated Quit50-tick handoff branches, excluding destination bodies."""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/title-menu-handoff.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{titleMenuHandoff}from'./shared/th06nc/title-menu-handoff.mjs';const cases=[];for(const state of [12,21,23])for(const frame of [-1,0,1,49,50,51,99,2147483647])for(const before of [0,1,9])cases.push({state,frame,before,event:titleMenuHandoff(state,frame)});for(const frame of [-1,0,49,50,51,99])for(const present of [false,true])for(const mode of [0,1,2,3])for(const before of [0,1,9])cases.push({state:5,frame,present,mode,before,event:titleMenuHandoff(5,frame,present?{mode}:null)});console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 def stop(m,a,size,u):m.emu_stop()
 for a in [0x14004cbe6,0x14004d0b0]:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
 for c in cases:
  m.mem_write(n.owner+0x9638,struct.pack('<i',c['frame']));m.mem_write(0x140c21d9c,struct.pack('<i',c['before']));m.mem_write(0x140c22158,struct.pack('<Q',n.vm if c.get('present')else 0));m.mem_write(n.vm+0x34,struct.pack('<i',c.get('mode',0)))
  for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_R11,6),(UC_X86_REG_R13,11),(UC_X86_REG_RBX,4)]:m.reg_write(reg,value)
  m.emu_start({5:0x14004c198,12:0x14004c1cc,21:0x14004c1e7,23:0x14004c206}[c['state']],n.stack,count=100)
  assert m.reg_read(UC_X86_REG_RIP)==(0x14004d0b0 if c['event']else 0x14004cbe6)
  assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==(c['event']['gameState']if c['event']else c['before'])
  if c['event']:assert m.reg_read(UC_X86_REG_EAX)==0
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(cases),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-menu-handoff-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
