"""Combined native state-3 navigation, presentation and input decisions.

Starts at the state-3 branch and stops before common owner postprocessing.
Fade/sound delivery is observed; no destination owner, rendering or gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RIP


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{updateTitleMain}from'./shared/th06nc/title-main-update.mjs';
const resources=new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))]));
const snapshot=g=>[...g.slots].map(([offset,vm])=>({offset,state:Buffer.from(vm.state).toString('hex')}));const base=snapshot(new TitleAnimations(resources)),cases=[];
for(let selection=0;selection<10;selection++)for(const held of [0,0x20,0x100,0x800])for(const extra of [false,true]){
const group=new TitleAnimations(resources),initial={selection,state:3,frame:21,pulse:selection*10,practice:1,spell:1,difficulty:5,configuredDifficulty:5},keys={held,previous:0,repeat:0};
const result=updateTitleMain(group,initial,keys,{extraAvailable:extra});cases.push({initial,keys,extra,result:{state:result.state,effects:result.effects,fades:Array.from(result.fades),soundSlots:result.soundSlots},slots:snapshot(group)});}
console.log(JSON.stringify({refs:titleResources,base,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;effects=[]
    def hook(m,address,size,user):
        if address in [0x140049ab6,0x140047f60,0x14004cbf4]:m.emu_stop();return
        if address not in [0x140076050,0x140076af0]:return
        edx=m.reg_read(UC_X86_REG_RDX)&0xffffffff;effects.append(dict(kind='fade',mode=m.reg_read(UC_X86_REG_RCX)&0xffffffff,frames=edx) if address==0x140076050 else dict(kind='sound',id=edx))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook);digest=hashlib.sha256()
    scores=[0x4ff101,0x4ff102,0x4ff103,0x4ff119,0x4ff11a,0x4ff11b,0x4ff131,0x4ff132,0x4ff133,0x4ff149,0x4ff14a,0x4ff14b]
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes(0x20000))
        for slot in data['base']:
            state=bytearray.fromhex(slot['state']);ptr=struct.unpack_from('<Q',state,0x100)[0]
            if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
            m.mem_write(n.owner+slot['offset'],bytes(state))
        initial=c['initial']
        for p,key in [(0x28,'selection'),(0x30,'pulse'),(0x9638,'frame'),(0x168b0,'state')]:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
        m.mem_write(n.owner+0x168d1,b'\1');m.mem_write(n.owner+0x168d3,b'\1');m.mem_write(0x1404f27c0,struct.pack('<i',5));m.mem_write(0x140c21db9,b'\5')
        for address in scores:m.mem_write(0x140000000+address,bytes([99 if c['extra'] else 0]))
        m.mem_write(0x140a6ec60,struct.pack('<II',c['keys']['held'],0));m.mem_write(0x140a6ec48,bytes(4));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');effects.clear()
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x140048174,n.stack,count=100000)
        actual=dict(initial)
        for p,key in [(0x28,'selection'),(0x30,'pulse'),(0x9638,'frame'),(0x168b0,'state')]:actual[key]=struct.unpack('<i',m.mem_read(n.owner+p,4))[0]
        actual.update(practice=m.mem_read(n.owner+0x168d1,1)[0],spell=m.mem_read(n.owner+0x168d3,1)[0],difficulty=struct.unpack('<i',m.mem_read(0x1404f27c0,4))[0],configuredDifficulty=m.mem_read(0x140c21db9,1)[0])
        result=dict(state=actual,effects=effects.copy(),fades=list(struct.unpack('<10i',m.mem_read(n.owner+0x16880,40))),soundSlots=list(struct.unpack('<3i',m.mem_read(0x140509670,12))))
        assert result==c['result'],(index,result,c['result'])
        for slot in c['slots']:
            actual=bytearray(m.mem_read(n.owner+slot['offset'],288));ptr=struct.unpack_from('<Q',actual,0x100)[0]
            if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
            expected=bytes.fromhex(slot['state']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,expected)) if x!=y];assert not diff,(index,slot['offset'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*len(data['base']),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-main-update.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-main-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
