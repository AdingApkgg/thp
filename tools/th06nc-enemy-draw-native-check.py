"""Full enemy draw owner 38290..3868c plus actual 67f0 routing bridge.

Complete first enemy bytes and drawable VM requests compare across flat and
three-axis routes. Camera request, flat/world renderer bodies and GPU are
controlled boundaries; world vertex math has its separate native fixture.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/enemy-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{createEnemyTemplate}from'./shared/th06nc/enemy-pool.mjs';import{drawEnemyAnimations}from'./shared/th06nc/enemy-draw.mjs';const cases=[],offsets=[0x2d8,0x3f8,0x518,0x638,0x108,0x758,0x878,0x998,0xab8],hex=b=>Buffer.from(b).toString('hex');for(const active of [false,true])for(const hidden of [false,true])for(const borrowed of [false,true])for(const x of [0,.5,NaN])for(const y of [0,-.5])for(const z of [0,1]){const raw=createEnemyTemplate(),v=new DataView(raw.buffer),enemyAnms=new Map();v.setUint8(0xbc,active?128:0);v.setUint8(0xbe,(hidden?8:0)|(borrowed?2:0));v.setFloat32(0xb0,123.25,true);v.setFloat32(0xb4,234.5,true);v.setFloat32(0x22c,.25,true);for(let i=0;i<offsets.length;i++){const p=offsets[i],state=raw.subarray(p,p+288),a=new DataView(state.buffer,state.byteOffset,state.byteLength);a.setInt16(0x38,i%3===0?-1:0,true);a.setUint32(0xc4,i%4===0?1:3,true);a.setUint32(0xec,i%5===0?0:0xffabcdef,true);a.setUint16(0x88,i%2,true);a.setFloat32(0x18,i+0.5,true);a.setFloat32(0x1c,-i-.25,true);a.setFloat32(0x9c,x,true);a.setFloat32(0xa0,y,true);a.setFloat32(0xa4,z,true);enemyAnms.set(p,{state,v:a});}const before=hex(raw),events=[];drawEnemyAnimations({v,enemyAnms},(vm,options)=>events.push({offset:vm.state.byteOffset,space:options.space??'screen',snap:options.snap??false,state:hex(vm.state)}),{worldOffset:[236,16]});cases.push({before,after:hex(raw),events});}console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;m.mem_map(n.owner+0x20000,0x100000);events=[];digest=hashlib.sha256();m.mem_write(0x140a6e9b0,struct.pack('<Q',n.manager));m.mem_write(0x1404f1e70,struct.pack('<2f',236,16))
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a!=0x14007af40:
   ptr=m.reg_read(UC_X86_REG_RDX);raw=bytes(m.mem_read(ptr,288));flags=struct.unpack_from('<I',raw,0xc4)[0];color=struct.unpack_from('<I',raw,0xec)[0]
   if flags&3==3 and color:events.append(dict(offset=ptr-n.owner-8,space='world'if a==0x140004dc0 else'screen',snap=False if a==0x140004dc0 else bool(m.reg_read(UC_X86_REG_R8)&255),state=raw.hex()))
  m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for address in [0x14007af40,0x1400036c0,0x140004dc0]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
 for index,c in enumerate(cases):
  m.mem_write(n.owner,bytes(0x10b008));m.mem_write(n.owner+8,bytes.fromhex(c['before']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);events.clear();m.emu_start(0x140038290,n.stack+0xf000,count=100000);actual=bytes(m.mem_read(n.owner+8,0x10b0));assert actual.hex()==c['after'],(index,'owner');assert events==c['events'],(index,[(e['offset'],e['space'],e['snap'])for e in events],[(e['offset'],e['space'],e['snap'])for e in c['events']]);digest.update(actual)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-enemy-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
