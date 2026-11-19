"""Native float32 FPS-weight accumulation 3c66e..3c6da.

The platform FPS/clock acquisition, sleep scheduling and sample-window adapter
are outside this CPU scope. Actual native threshold/accumulator block executes.
"""
import sys,json,struct,hashlib,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
def main():
 source='shared/th06nc/runtime-speed.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{accumulateRuntimeSpeed}from'./shared/th06nc/runtime-speed.mjs';const scenes=[];for(const active of [false,true])for(const initial of [0,16777216,-60]){const state={numerator:initial,denominator:initial},frames=[];for(let frame=0;frame<100;frame++){const fps=[30,30.0001,42,42.0001,54,54.0001,60,100,-1,NaN][frame%10];accumulateRuntimeSpeed(state,fps,{active});frames.push({...state,fps:Number.isNaN(fps)?null:fps});}scenes.push({active,initial,frames});}console.log(JSON.stringify(scenes));
""";scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0
 for s in scenes:
  m.mem_write(0x140c21d0c,struct.pack('<2f',s['initial'],s['initial']))
  for c in s['frames']:
   fps=float('nan')if c['fps']is None else c['fps'];m.reg_write(UC_X86_REG_XMM6,int.from_bytes(struct.pack('<d',fps),'little'));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000)
   if s['active']:m.emu_start(0x14003c66e,0x14003c6da,count=1000)
   actual=bytes(m.mem_read(0x140c21d0c,8));assert actual==struct.pack('<2f',c['numerator'],c['denominator']),(s,c,actual.hex());digest.update(actual);checked+=1
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,scenes=len(scenes),samples=checked,stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-runtime-speed-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
