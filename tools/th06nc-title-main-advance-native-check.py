"""Actual stable state-3 common postprocessing and animation updates.

Excludes state-changing paths, return tween, menu slide, GPU and audible output.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_R13,UC_X86_REG_R12,UC_X86_REG_RAX,UC_X86_REG_RDX


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleBackdrop}from'./shared/th06nc/title-backdrop.mjs';import{advanceStableTitleMain}from'./shared/th06nc/title-main-advance.mjs';
const resources=new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))]));
const snap=g=>[...g.slots].map(([offset,vm])=>({offset,file:[...resources].find(([n,r])=>r===vm.resource)?.[0],state:Buffer.from(vm.state).toString('hex')})),cases=[];
for(const frame of [34,35,36])for(const entryHold of [false,true])for(const previousGroupState of [3,4])for(const counter of [0,1]){
const group=new TitleAnimations(resources),b=new TitleBackdrop(group);b.counter=counter;const initial={state:3,frame,pulse:71,totalFrame:99,inputCooldown:2,entryHold,previousGroupState};const before=snap(group);const result=advanceStableTitleMain(group,initial,b);cases.push({initial,counter,before,result,after:snap(group),control:Buffer.from(b.control).toString('hex'),counterAfter:b.counter});}
console.log(JSON.stringify({refs:titleResources,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes(0x20000))
        for slot in c['before']:
            state=bytearray.fromhex(slot['state'])
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,p)[0]
                if ptr:struct.pack_into('<Q',state,p,n.assetByFile[slot['file']]+ptr)
            ptr=struct.unpack_from('<Q',state,0x100)[0]
            if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
            m.mem_write(n.owner+slot['offset'],bytes(state))
        initial=c['initial'];fields=[(0x168b0,'state'),(0x9638,'frame'),(0x30,'pulse'),(0x2c,'totalFrame'),(0x1686c,'inputCooldown'),(0x16870,'previousGroupState')]
        for p,key in fields:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
        m.mem_write(n.owner+0x16877,bytes([initial['entryHold']]));m.mem_write(n.owner+0x16830,b'\1');m.mem_write(n.owner+0x16868,struct.pack('<i',c['counter']))
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R13,3),(UC_X86_REG_R12,5),(UC_X86_REG_RAX,3),(UC_X86_REG_RDX,0)]:m.reg_write(reg,value)
        m.emu_start(0x14004cd09,0x14004d0ad,count=1000000)
        actual={key:struct.unpack('<i',m.mem_read(n.owner+p,4))[0] for p,key in fields};actual['entryHold']=bool(m.mem_read(n.owner+0x16877,1)[0]);assert actual==c['result'],(index,actual,c['result'])
        assert bytes(m.mem_read(n.owner+0x16834,40)).hex()==c['control'];assert struct.unpack('<i',m.mem_read(n.owner+0x16868,4))[0]==c['counterAfter']
        for slot in c['after']:
            actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            ptr=struct.unpack_from('<Q',actual,0x100)[0]
            if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(slot['state']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,wanted)) if x!=y];assert not diff,(index,slot['offset'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*132,stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-main-advance.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-main-advance-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
