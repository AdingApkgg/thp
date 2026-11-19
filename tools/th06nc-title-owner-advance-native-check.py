"""Common postprocessing across implemented main/start/difficulty state pairs.

Uses base title resources and actual ANM updates, including replay and spell-menu state pairs;
excludes replay resource replacement, return tween, GPU and audible output.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_R13,UC_X86_REG_R12,UC_X86_REG_RAX,UC_X86_REG_RDX


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleBackdrop}from'./shared/th06nc/title-backdrop.mjs';import{advanceTitleOwnerCommon}from'./shared/th06nc/title-owner-advance.mjs';
const resources=new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))]));
const snap=g=>[...g.slots].map(([offset,vm])=>({offset,file:[...resources].find(([n,r])=>r===vm.resource)?.[0],state:Buffer.from(vm.state).toString('hex')})),cases=[];
for(const [previousState,state] of [[3,5],[5,5],[3,23],[23,23],[3,4],[4,4],[4,3],[4,6],[6,6],[6,4],[4,7],[7,7],[7,4],[3,12],[12,12],[3,21],[21,21],[10,10],[10,0],[0,2],[2,2],[2,3],[14,22],[22,22],[22,14],[22,24],[24,22],[3,3],[3,8],[8,8],[8,9],[9,9],[9,10],[9,11],[11,11],[11,13],[13,13],[13,11],[13,14],[14,14],[14,13],[14,24],[24,24],[24,14],[24,25],[25,25],[3,15],[15,16],[16,17],[17,18],[18,18],[18,19],[18,20],[19,19],[20,20],[20,18],[20,26],[26,26],[3,27],[27,27],[27,28],[27,30],[28,28],[28,29],[28,0],[29,29],[29,28],[29,30],[30,30],[30,29],[30,31],[31,31]])for(const frame of [34,35,36])for(const entryHold of [false,true])for(const previousGroupState of [3,4])for(const counter of [0,1])for(const warmReturn of [false,true]){
const group=new TitleAnimations(resources),b=new TitleBackdrop(group);b.counter=counter;const initial={state,frame,pulse:71,totalFrame:99,inputCooldown:2,entryHold,previousGroupState,warmReturn};const before=snap(group);const result=advanceTitleOwnerCommon(group,initial,b,{previousState});cases.push({initial,previousState,counter,before,result,after:snap(group),control:Buffer.from(b.control).toString('hex'),counterAfter:b.counter});}
const baseline=cases[0].before;for(const c of cases)delete c.before;console.log(JSON.stringify({refs:titleResources,baseline,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes(0x20000))
        for slot in data['baseline']:
            state=bytearray.fromhex(slot['state'])
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,p)[0]
                if ptr:struct.pack_into('<Q',state,p,n.assetByFile[slot['file']]+ptr)
            ptr=struct.unpack_from('<Q',state,0x100)[0]
            if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
            m.mem_write(n.owner+slot['offset'],bytes(state))
        initial=c['initial'];fields=[(0x168b0,'state'),(0x9638,'frame'),(0x30,'pulse'),(0x2c,'totalFrame'),(0x1686c,'inputCooldown'),(0x16870,'previousGroupState')]
        for p,key in fields:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
        m.mem_write(n.owner+0x16877,bytes([initial['entryHold']]));m.mem_write(n.owner+0x16876,bytes([initial['warmReturn']]));m.mem_write(n.owner+0x16830,b'\1');m.mem_write(n.owner+0x16868,struct.pack('<i',c['counter']))
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_R13,c['previousState']),(UC_X86_REG_R12,5),(UC_X86_REG_RAX,initial['state']),(UC_X86_REG_RDX,0)]:m.reg_write(reg,value)
        m.emu_start(0x14004cd09,0x14004d0ad,count=1000000)
        actual={key:struct.unpack('<i',m.mem_read(n.owner+p,4))[0] for p,key in fields};actual['entryHold']=bool(m.mem_read(n.owner+0x16877,1)[0]);actual['warmReturn']=bool(m.mem_read(n.owner+0x16876,1)[0]);assert actual==c['result'],(index,actual,c['result'])
        assert bytes(m.mem_read(n.owner+0x16834,40)).hex()==c['control'],(index,c['initial'],c['previousState'],c['counter'],bytes(m.mem_read(n.owner+0x16834,40)).hex(),c['control']);assert struct.unpack('<i',m.mem_read(n.owner+0x16868,4))[0]==c['counterAfter']
        for slot in c['after']:
            actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            ptr=struct.unpack_from('<Q',actual,0x100)[0]
            if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(slot['state']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,wanted)) if x!=y];assert not diff,(index,slot['offset'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*132,stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/title-owner-advance.mjs','shared/th06nc/title-selection-return.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-owner-advance-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()
