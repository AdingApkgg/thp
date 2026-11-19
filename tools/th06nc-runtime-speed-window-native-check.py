"""Native half-second FPS sample window and weighted runtime-speed counters.

Executes 3c5ec..3c6da with a controlled microsecond clock. FPS text output is
stubbed. Platform timer acquisition, native sleep/pacing and lifecycle excluded.
"""
import struct,json,hashlib,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/runtime-speed.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{RuntimeSpeed}from'./shared/th06nc/runtime-speed.mjs';const scenes=[];for(const step of [8333,16667,25000,50000,500000,700000]){const state=new RuntimeSpeed(),frames=[];for(let i=0;i<200;i++){const now=i*step,active=i%7!==0;state.sample(now,active);frames.push({now,active,numerator:state.numerator,denominator:state.denominator,frames:state.frames,previousTime:state.previousTime});}scenes.push(frames);}console.log(JSON.stringify(scenes));
""";scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;now=0;digest=hashlib.sha256();checked=0
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x1400b03d0:m.reg_write(UC_X86_REG_RAX,now)
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1400b03d0,0x140038740]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for s in scenes:
  m.mem_write(0x140c21d0c,bytes(8));m.mem_write(0x140c2232c,bytes(4));m.mem_write(0x140c29648,bytes(8))
  for c in s:
   now=c['now'];m.mem_write(0x1404f27b2,bytes([c['active']]));m.reg_write(UC_X86_REG_R15D,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003c5ec,0x14003c6da,count=10000)
   actual=bytes(m.mem_read(0x140c21d0c,8))+bytes(m.mem_read(0x140c2232c,4))+bytes(m.mem_read(0x140c29648,8));expected=struct.pack('<2fIQ',c['numerator'],c['denominator'],c['frames'],c['previousTime']);assert actual==expected,(now,c,actual.hex(),expected.hex());digest.update(actual);checked+=1
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,scenes=len(scenes),clockSamples=checked,stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-runtime-speed-window-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
