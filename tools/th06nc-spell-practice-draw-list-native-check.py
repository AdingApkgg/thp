"""Native list placement 532e0 and transient slide/alpha 4e880.

Observes 2a80 draw requests and full VM bytes, plus retained VM state. Rendering,
sprite visibility/texture checks inside 2a80 and GPU pixels are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/spell-practice-draw-list.mjs';before_hash=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""
import{drawSpellFade,drawSpellList}from'./shared/th06nc/spell-practice-draw-list.mjs';
const make=()=>{const state=new Uint8Array(288),v=new DataView(state.buffer);for(const [p,x]of [[0xc8,12.5],[0xcc,-3.25],[0xd0,7]])v.setFloat32(p,x,true);v.setUint32(0xec,0x77223344,true);return{state,v};},snap=vm=>Buffer.from(vm.state).toString('hex'),lists=[],fades=[];
for(const count of [-1,0,1,3,8])for(const selection of [-1,0,2,7,9])for(const variant of [0,1,2])for(const x of [-40,211])for(const slide of [10,-32]){
 const selected=make(),ordinary=make();ordinary.v.setUint32(0xec,0x88224466,true);const group={slots:new Map([[0,selected],[288,ordinary]])},progress=variant?Array.from({length:9},(_,i)=>[0,.125,.5,1,2,-.25][(i+variant)%6]):null,options={offset:0,count,selection,x,y:110,step:32,selectedOffsetX:-6,selectedOffsetY:-1.5,color:0xaabbccdd,progress,slide},before=[snap(selected),snap(ordinary)],requests=[];drawSpellList(group,vm=>requests.push({slot:vm===selected?0:1,state:snap(vm)}),options);lists.push({options,before,after:[snap(selected),snap(ordinary)],requests});
}
for(const alpha of [-1,0,.001,.125,.5,.999,1,1.5])for(const offsetX of [-12.25,0,31.5])for(const color of [0,0x01223344,0x77223344,0xffffffff]){
 const vm=make();vm.v.setUint32(0xec,color,true);const before=snap(vm),requests=[],options={alpha,offsetX,offsetY:-5.5};drawSpellFade(vm,()=>requests.push(snap(vm)),options);fades.push({before,after:snap(vm),requests,options});
}console.log(JSON.stringify({lists,fades}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;requests=[]
 def hook(m,a,size,u):
  p=m.reg_read(UC_X86_REG_RDX);requests.append(dict(slot=(p-n.owner)//288,state=bytes(m.mem_read(p,288)).hex()));sp=m.reg_read(UC_X86_REG_RSP);assert m.reg_read(UC_X86_REG_R8)&255==255;assert m.reg_read(UC_X86_REG_R9)&255==255;assert m.mem_read(sp+0x28,1)[0]==1;m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140002a80,end=0x140002a80)
 def xmm(reg,value):m.reg_write(reg,struct.unpack('<I',struct.pack('<f',value))[0])
 digest=hashlib.sha256()
 for index,c in enumerate(data['lists']):
  requests.clear();o=c['options'];m.mem_write(n.owner,bytes.fromhex(''.join(c['before'])));progress=n.vm if o['progress']else 0
  if progress:m.mem_write(progress,struct.pack('<9f',*o['progress']))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000))
  for offset,fmt,value in [(0x28,'f',o['y']),(0x30,'f',o['step']),(0x38,'f',o['selectedOffsetX']),(0x40,'f',o['selectedOffsetY']),(0x48,'I',o['color']),(0x50,'Q',progress),(0x58,'f',o['slide'])]:m.mem_write(sp+offset,struct.pack('<'+fmt,value))
  for reg,value in [(UC_X86_REG_RCX,n.owner),(UC_X86_REG_RDX,o['count']),(UC_X86_REG_R8,o['selection']),(UC_X86_REG_RSP,sp)]:m.reg_write(reg,value&0xffffffffffffffff)
  xmm(UC_X86_REG_XMM3,o['x']);m.emu_start(0x1400532e0,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;assert requests==c['requests'],(index,'requests',requests,c['requests']);assert bytes(m.mem_read(n.owner,576)).hex()==''.join(c['after']),(index,'retained VMs');digest.update(m.mem_read(n.owner,576))
 for index,c in enumerate(data['fades']):
  requests.clear();m.mem_write(n.owner,bytes.fromhex(c['before']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner)
  for reg,key in [(UC_X86_REG_XMM1,'offsetX'),(UC_X86_REG_XMM2,'offsetY'),(UC_X86_REG_XMM3,'alpha')]:xmm(reg,c['options'][key])
  m.emu_start(0x14004e880,n.stack+0xf000,count=100000);assert [r['state']for r in requests]==c['requests'],(index,'fade requests');assert bytes(m.mem_read(n.owner,288)).hex()==c['after'],(index,'restoration');digest.update(m.mem_read(n.owner,288))
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==before_hash
 report=dict(scope=__doc__,listCases=len(data['lists']),fadeCases=len(data['fades']),stateSha256=digest.hexdigest(),sourceSha256={source:before_hash},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-draw-list-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'listCases':report['listCases'],'fadeCases':report['fadeCases'],'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
