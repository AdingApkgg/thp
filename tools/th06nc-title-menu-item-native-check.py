"""Actual menu-item helper and sprite bindings versus portable presentation.

Does not cover input, owner selection transitions, drawing or game acceptance.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_RSP


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{updateTitleMenuItem}from'./shared/th06nc/title-menu-item.mjs';
const g=new TitleAnimations(new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))]))),cases=[];
for(const id of [0x100,0x120,0x132,0x133,0x13c,0x146,0x164])for(const group of [0,1])for(const item of [0,1])for(const pulse of [-1,0,15,29,30,41,42,60,71,72]){
const vm=g.bank.createVm(0x100);vm.tick();vm.bindSprite(id);vm.v.setUint16(0x36,id,true);const initial=Buffer.from(vm.state).toString('hex'),args={group,item,selected:0,activeGroup:0,pulse};updateTitleMenuItem(vm,args);cases.push({id,args,initial,expected:Buffer.from(vm.state).toString('hex')});}
console.log(JSON.stringify({refs:titleResources,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
    for c in data['cases']:
        initial=bytearray.fromhex(c['initial']);pointer=struct.unpack_from('<Q',initial,0x100)[0]
        if pointer:struct.pack_into('<Q',initial,0x100,n.manager+0x608+(pointer-1)*64)
        m.mem_write(n.vm,bytes(initial));a=c['args'];m.mem_write(n.owner+0x28,struct.pack('<i',a['activeGroup']));m.mem_write(n.owner+0x30,struct.pack('<i',a['pulse']))
        sp=n.stack+0x8008;m.mem_write(sp,struct.pack('<Q',n.stack));m.mem_write(sp+0x28,struct.pack('<i',a['selected']))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RCX,n.owner),(UC_X86_REG_RDX,n.vm),(UC_X86_REG_R8,a['group']),(UC_X86_REG_R9,a['item'])]:m.reg_write(reg,value)
        m.emu_start(0x14004d8e0,n.stack,count=100000);assert m.reg_read(UC_X86_REG_RSP)==sp+8
        actual=bytearray(m.mem_read(n.vm,288));pointer=struct.unpack_from('<Q',actual,0x100)[0]
        if pointer:struct.pack_into('<Q',actual,0x100,(pointer-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['expected']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,wanted)) if x!=y];assert not diff,(c['id'],a,diff);digest.update(actual)
    sources=['shared/th06nc/title-menu-item.mjs','shared/th06nc/anm-vm.mjs','shared/th06nc/anm-bank.mjs']
    report=dict(scope=__doc__,cases=len(data['cases']),comparedBytes=len(data['cases'])*288,stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-menu-item-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
