"""Practice list 54ca8..54f3f: actual formatted text requests and font colors.

Actual native formatting call boundary is observed; the formatter, glyph cache,
GPU, stable ANM draw loop and font flush are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/title-practice-draw.mjs','shared/th06nc/title-practice-entry.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{practiceStageDrawPlan}from'./shared/th06nc/title-practice-draw.mjs';const scores=new Uint8Array(2304),v=new DataView(scores.buffer),cases=[];for(let i=0;i<96;i++)v.setBigUint64(i*24+12,i%8===0?0xffffffffffffffffn:BigInt(i)*1000000001n,true);for(const difficulty of [0,1,2,3])for(let profile=0;profile<4;profile++)for(const kind of [22,24,25])for(const frame of [0,15,29,30])for(const progress of [0,1,6,99]){const state={state:kind,frame,pulse:cases.length%72,selection:cases.length%6,configuredPracticeStage:(cases.length+2)%6,spell:cases.length%2,launchFrom:22,difficulty,configuredCharacter:profile>>1,configuredShot:profile&1},cleared=new Uint8Array(96);cleared[profile*24+17+difficulty]=progress;cases.push({state,cleared:[...cleared],expected:practiceStageDrawPlan(state,{cleared,practiceScores:scores})});}console.log(JSON.stringify({cases,scores:Buffer.from(scores).toString('hex')}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();m.mem_write(0x1404f1e8c,bytes.fromhex(data['scores']))
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);stage=m.reg_read(UC_X86_REG_R9D);score=struct.unpack('<Q',m.mem_read(sp+0x28,8))[0];position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12)));color=struct.unpack('<I',m.mem_read(0x1403e38ec,4))[0];events.append(dict(text=f'STAGE {stage}  {score:09}',position=position,color=color));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140009aa0,end=0x140009aa0)
 for index,c in enumerate(data['cases']):
  s=c['state'];m.mem_write(n.owner,bytes(0x16900))
  for p,key in [(0x168b0,'state'),(0x168cc,'launchFrom'),(0x9638,'frame'),(0x30,'pulse'),(0x28,'selection')]:m.mem_write(n.owner+p,struct.pack('<i',s[key]))
  m.mem_write(n.owner+0x168d2,bytes([s['spell']]));m.mem_write(0x1404f1e80,bytes([s['configuredCharacter'],s['configuredShot']]));m.mem_write(0x1404f27c0,struct.pack('<i',s['difficulty']));m.mem_write(0x1404ff0c8,struct.pack('<i',s['configuredPracticeStage']));m.mem_write(0x1404ff0f4,bytes(c['cleared']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R9D,s['state']);m.reg_write(UC_X86_REG_R12,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140054ca8,0x140054f3f,count=10000);assert events==c['expected'],(index,events,c['expected']);assert struct.unpack('<I',m.mem_read(0x1403e38ec,4))[0]==0xffffffff,(index,hex(struct.unpack('<I',m.mem_read(0x1403e38ec,4))[0]));digest.update(json.dumps(events,sort_keys=True).encode())
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-practice-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases'])}))
if __name__=='__main__':main()
