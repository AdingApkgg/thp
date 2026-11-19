"""Native pulse 46d40/4ea50, transition 4e960 and edge alpha 4f040.

Compares scalar colors, full VM draw requests and persistent VM restoration.
Sprite/crop height is controlled metadata; 2a80 visibility and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/spell-practice-draw-effects.mjs','shared/th06nc/spell-practice-draw-list.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{spellPulseAlpha,spellDifficultyColor,drawSpellTransition,drawSpellListEdge}from'./shared/th06nc/spell-practice-draw-effects.mjs';
const make=()=>{const state=new Uint8Array(288),v=new DataView(state.buffer);v.setFloat32(0xc8,12.25,true);v.setFloat32(0xcc,7,true);v.setFloat32(0xd0,3,true);v.setUint32(0xec,0x77224466,true);return{state,v,pointer:p=>Number(v.getBigUint64(p,true)),boundSprite:{height:17.5}};},snap=vm=>Buffer.from(vm.state).toString('hex'),pulses=[],colors=[],transitions=[],edges=[];
for(const frame of [-2147483648,-200,-72,-1,...Array.from({length:145},(_,i)=>i),2147483647]){for(const minimum of [0,64,128,208,255])pulses.push({frame,minimum,expected:spellPulseAlpha(frame,minimum)});for(const selected of [false,true])colors.push({frame,selected,expected:spellDifficultyColor(selected,frame)});}
for(const ticks of [-1,0,1,5,9,10,11])for(const color of [0,0x01224466,0x77224466,0xffffffff])for(const direction of [-1,0,1])for(const offsetX of [-3,0])for(const alpha of [0,.4,1]){
 const vm=make(),before=snap(vm),requests=[],options={ticks,color,direction,offsetX,alpha};drawSpellTransition(vm,()=>requests.push({state:snap(vm),topAlpha:255,bottomAlpha:255}),options);transitions.push({options,before,after:snap(vm),requests});
}
for(const cropped of [-1,0,15,100])for(const y of [350,375,376.77777099609375,380,400,408.77777099609375,410])for(const scale of [.7,1,2])for(const bound of [false,true]){
 const vm=make();vm.v.setBigUint64(0x100,bound?1n:0n,true);vm.v.setInt32(0x118,cropped,true);vm.v.setFloat32(0xcc,y,true);vm.v.setFloat32(0xe4,scale,true);const before=snap(vm),requests=[];drawSpellListEdge(vm,(_,o)=>requests.push({state:snap(vm),topAlpha:o.topAlpha,bottomAlpha:o.bottomAlpha}));edges.push({before,after:snap(vm),requests});
}console.log(JSON.stringify({pulses,colors,transitions,edges}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;requests=[]
 def hook(m,a,size,u):
  p=m.reg_read(UC_X86_REG_RDX);state=bytearray(m.mem_read(p,288));ptr=struct.unpack_from('<Q',state,0x100)[0]
  if ptr:struct.pack_into('<Q',state,0x100,1)
  requests.append(dict(state=state.hex(),topAlpha=m.reg_read(UC_X86_REG_R8)&255,bottomAlpha=m.reg_read(UC_X86_REG_R9)&255));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x140002a80,end=0x140002a80)
 def call(address):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(address,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;return m.reg_read(UC_X86_REG_RAX)
 digest=hashlib.sha256()
 for c in data['pulses']:
  m.reg_write(UC_X86_REG_RCX,c['frame']&0xffffffff);m.reg_write(UC_X86_REG_RDX,c['minimum']);actual=call(0x140046d40)&255;assert actual==c['expected'],(c,actual)
 for c in data['colors']:
  m.reg_write(UC_X86_REG_RCX,int(c['selected']));m.reg_write(UC_X86_REG_RDX,c['frame']&0xffffffff);actual=call(0x14004ea50)&0xffffffff;assert actual==c['expected'],(c,actual)
 for c in data['transitions']:
  requests.clear();m.mem_write(n.owner,bytes.fromhex(c['before']));o=c['options'];m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,o['color']);m.reg_write(UC_X86_REG_R8,o['ticks']&0xffffffff);m.reg_write(UC_X86_REG_R9,o['direction']&0xffffffff);m.mem_write(n.stack+0x8028,struct.pack('<f',o['offsetX']));m.mem_write(n.stack+0x8030,struct.pack('<f',o['alpha']));call(0x14004e960);assert requests==c['requests'],(c['options'],requests,c['requests']);assert bytes(m.mem_read(n.owner,288)).hex()==c['after'];digest.update(m.mem_read(n.owner,288))
 for c in data['edges']:
  requests.clear();state=bytearray.fromhex(c['before']);ptr=struct.unpack_from('<Q',state,0x100)[0]
  if ptr:struct.pack_into('<Q',state,0x100,n.vm)
  m.mem_write(n.vm+0x14,struct.pack('<f',17.5));m.mem_write(n.owner,bytes(state));m.reg_write(UC_X86_REG_RCX,n.owner);call(0x14004f040);assert requests==c['requests'],(c['before'],requests,c['requests']);assert bytes(m.mem_read(n.owner,288))==bytes(state);digest.update(m.mem_read(n.owner,288))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 counts={k:len(v)for k,v in data.items()};report=dict(scope=__doc__,**counts,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-practice-draw-effects-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(counts|{'passed':True,'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
