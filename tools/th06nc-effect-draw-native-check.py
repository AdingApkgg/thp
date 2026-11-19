"""Effect draw task: all 512 slots, position publication and ordered world VMs.

Compare complete owner bytes and VM requests against original 2b310. Camera
setup and original 4dc0 GPU draw are observed boundaries; no pixel claim.
"""
import hashlib,json,struct,subprocess,base64
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/effect-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{drawEffects}from'./shared/th06nc/effect-draw.mjs';import{createHash}from'node:crypto';const cases=[];for(const slots of [[],[0],[3,200,511],[0,511,512]])for(const active of [1,255]){const storage=new Uint8Array(513*0x198),entries=new Map(),entry=slot=>{if(!entries.has(slot)){const bytes=storage.subarray(slot*0x198,(slot+1)*0x198),v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),state=bytes.subarray(0x40,0x160),vm={state,v:new DataView(state.buffer,state.byteOffset,state.byteLength)};entries.set(slot,{bytes,v,vm});}return entries.get(slot);};for(const slot of slots){const e=entry(slot);for(let p=0;p<0x198;p+=4)e.v.setFloat32(p,(p%37)-15.75,true);e.v.setUint8(0x14,active);[slot+.5,-slot-2.25,slot%3*.25].forEach((n,i)=>e.v.setFloat32(0x174+i*4,n,true));}const before=Buffer.from(storage).toString('base64'),calls=[],result=drawEffects({entry},(vm,info)=>calls.push({slot:info.slot,state:Buffer.from(vm.state).toString('hex')}));cases.push({before,calls,result,sha:createHash('sha256').update(storage).digest('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;base=0x140a6ecd0;calls=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x140004dc0:
            ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(slot=(ptr-base-0x40)//0x198,state=bytes(m.mem_read(ptr,288)).hex()))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140004dc0,0x14007af40]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(cases):
        m.mem_write(base,base64.b64decode(c['before']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,base);calls.clear();m.emu_start(0x14002b310,n.assets,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.assets,(i,'instruction limit');actual=bytes(m.mem_read(base,513*0x198));assert hashlib.sha256(actual).hexdigest()==c['sha'],(i,'pool');assert calls==c['calls'],(i,'world draw requests');assert len(calls)==c['result'];digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),drawCalls=sum(len(c['calls'])for c in cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-effect-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
