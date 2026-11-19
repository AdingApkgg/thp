"""Selected spell row 4eaf0..4f038: temporary VM bytes and retained state.

Controlled texture availability, cookie and f32 sin/cos services. Captures the
36c0 draw request; native CRT trigonometry and GPU submission are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/spell-practice-highlight.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""
import{drawSpellHighlight}from'./shared/th06nc/spell-practice-highlight.mjs';
const bits=x=>{const a=new Float32Array([x]);return new Uint32Array(a.buffer)[0];},trig={},sin=Math.sin,cos=Math.cos;
for(const [name,fn]of[['sin',sin],['cos',cos]])Math[name]=x=>{const result=fn(x);trig[name+':'+bits(x)]=bits(result);return result;};
const cases=[],snap=vm=>Buffer.from(vm.state).toString('hex');
class VM{constructor(){this.state=new Uint8Array(288);this.v=new DataView(this.state.buffer);this.boundSprite={width:796.5,height:170.5};this.boundBinding={active:true};}pointer(p){return Number(this.v.getBigUint64(p,true));}}
for(const noticeClock of [-1,0,...Array.from({length:62},(_,i)=>i+1)])for(const ticks of [0,1,12,24,25,26])for(const direction of [-1,0,1])for(const variant of [0,1]){
 const vm=new VM(),v=vm.v;v.setBigUint64(0x100,1n,true);v.setUint32(0xc4,0x4503,true);v.setFloat32(0xd0,3.5,true);v.setFloat32(0xe8,variant?-.55:.55,true);v.setFloat32(0xe4,variant?1.25:.55,true);v.setInt32(0x114,100,true);v.setInt32(0x118,45,true);
 const options={noticeClock,ticks,direction,x:variant?-7.25:13.5,y:variant?400.75:103.25,color:variant?0x01224466:0xaf884422},before=snap(vm),requests=[];
 drawSpellHighlight(vm,(copy,o)=>{if(copy===vm)throw Error('highlight reused retained VM');requests.push({state:snap(copy),snap:o.snap});},options);cases.push({options,before,after:snap(vm),requests});
}
for(const mode of ['unbound','inactive','texture']){const vm=new VM();vm.v.setBigUint64(0x100,mode==='unbound'?0n:1n,true);if(mode==='inactive')vm.boundBinding.active=false;const options={hasTexture:mode!=='texture'},before=snap(vm),requests=[];drawSpellHighlight(vm,(copy,o)=>requests.push({state:snap(copy),snap:o.snap}),options);cases.push({mode,options,before,after:snap(vm),requests});}
console.log(JSON.stringify({cases,trig}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;requests=[]
 m.mem_write(0x140a6e9b0,struct.pack('<Q',n.manager));m.mem_write(n.manager+0x20624,struct.pack('<i',-1));m.mem_write(n.vm+0x14,struct.pack('<ff',170.5,796.5))
 def ret():
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 def hook(m,a,size,u):
  if a in [0x1402be07d,0x1402be071]:
   key=('sin'if a==0x1402be07d else'cos')+':'+str(m.reg_read(UC_X86_REG_XMM0)&0xffffffff);assert key in data['trig'],key;m.reg_write(UC_X86_REG_XMM0,data['trig'][key])
  elif a==0x1400036c0:
   state=bytearray(m.mem_read(m.reg_read(UC_X86_REG_RDX),288));struct.pack_into('<Q',state,0x100,1);requests.append(dict(state=state.hex(),snap=bool(m.reg_read(UC_X86_REG_R8)&255)))
  ret()
 for a in [0x1402be07d,0x1402be071,0x1400036c0,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 digest=hashlib.sha256()
 for index,c in enumerate(data['cases']):
  assert c['after']==c['before'],('retained JavaScript VM changed',index)
  requests.clear();state=bytearray.fromhex(c['before']);ptr=struct.unpack_from('<Q',state,0x100)[0]
  if ptr:struct.pack_into('<Q',state,0x100,n.vm)
  m.mem_write(n.owner,bytes(state));m.mem_write(n.vm+0x24,struct.pack('<i',-1 if c.get('mode')=='inactive'else 0));m.mem_write(n.manager+0x20620,struct.pack('<i',-1 if c.get('mode')=='texture'else 0));o=c['options'];sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_R9,o.get('color',0xffffffff))
  for reg,key in [(UC_X86_REG_XMM1,'x'),(UC_X86_REG_XMM2,'y')]:m.reg_write(reg,struct.unpack('<I',struct.pack('<f',o.get(key,0)))[0])
  for offset,key in [(0x28,'ticks'),(0x30,'direction'),(0x38,'noticeClock')]:m.mem_write(sp+offset,struct.pack('<i',o.get(key,0)))
  m.emu_start(0x14004eaf0,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  assert requests==c['requests'],(index,o,[(hex(i),x,y)for r,s in zip(requests,c['requests'])for i,(x,y)in enumerate(zip(bytes.fromhex(r['state']),bytes.fromhex(s['state'])))if x!=y]);assert bytes(m.mem_read(n.owner,288))==bytes(state)
  for r in requests:digest.update(bytes.fromhex(r['state']))
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-highlight-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
