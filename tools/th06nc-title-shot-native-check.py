"""Complete state-13 shot branch, actual helper/ANM execution.

Stops before common owner postprocessing. Sound/fade calls are observed;
destination mode menu, physical input, rendering and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX,UC_X86_REG_RBX,UC_X86_REG_RSI,UC_X86_REG_RBP,UC_X86_REG_RSP,UC_X86_REG_R13,UC_X86_REG_R15,UC_X86_REG_RDI,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RIP,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R11


def main():
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{selectionResources,initializeSelectionAnimations,finishSelectionEntry}from'./shared/th06nc/title-selection-layout.mjs';import{updateTitleDifficulty}from'./shared/th06nc/title-difficulty-update.mjs';import{updateTitleCharacter}from'./shared/th06nc/title-character-update.mjs';import{updateTitleShot}from'./shared/th06nc/title-shot-update.mjs';
const resources=new Map([...titleResources,...selectionResources].map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))]));
const snap=g=>[...g.slots].map(([offset,v])=>({offset,file:[...resources].find(([n,r])=>r===v.resource)?.[0],state:Buffer.from(v.state).toString('hex')})),cases=[];
for(const difficulty of [1,4])for(const character of [0,1])for(const selection of [0,1])for(const frame of [14,15,29,30])for(const held of [0,0x10,0x20,0x30,0x100,0x200,0x300]){
const g=new TitleAnimations(resources);initializeSelectionAnimations(g,resources);finishSelectionEntry(g,{difficulty,configuredDifficulty:1});updateTitleDifficulty(g,{state:9,difficulty,configuredDifficulty:1,selection:difficulty<4?difficulty:0,frame:30,pulse:0,totalFrame:0,practice:0},{held:0x100,previous:0,repeat:0},{configuredCharacter:character,extraUnlockedCharacters:[true,true]});updateTitleCharacter(g,{state:11,difficulty,configuredDifficulty:1,configuredCharacter:character,configuredShot:selection,selection:character,frame:30,pulse:0,totalFrame:0},{held:0x100,previous:0,repeat:0},{extraUnlockedShots:[[true,true],[true,true]]});
const initial={state:13,difficulty,configuredDifficulty:1,configuredCharacter:character,configuredShot:1-selection,selection,frame,pulse:31,totalFrame:99,practice:0},keys={held,previous:frame>=29?held:0,repeat:frame===30?1:0},extraUnlockedShots=frame%2?[[false,true],[false,false]]:[[true,false],[false,true]],before=snap(g),result=updateTitleShot(g,initial,keys,{extraUnlockedShots,configuredMode:frame%2!==0});cases.push({initial,keys,extraUnlockedShots,configuredMode:frame%2!==0,before,result,after:snap(g)});}
console.log(JSON.stringify({refs:selectionResources,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;effects=[]
    def hook(m,address,size,user):
        if address in [0x140049ab6,0x14004cbf4]:m.emu_stop();return
        if address not in [0x140076050,0x140076af0]:return
        edx=m.reg_read(UC_X86_REG_RDX)&0xffffffff;effects.append(dict(kind='fade',mode=m.reg_read(UC_X86_REG_RCX)&0xffffffff,frames=edx) if address==0x140076050 else dict(kind='sound',id=edx))
        sp=m.reg_read(UC_X86_REG_RSP);ret=struct.unpack('<Q',m.mem_read(sp,8))[0];m.reg_write(UC_X86_REG_RSP,sp+8);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,ret)
    m.hook_add(UC_HOOK_CODE,hook);digest=hashlib.sha256()
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes(0x20000))
        for slot in c['before']:
            state=bytearray.fromhex(slot['state'])
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',state,p)[0]
                if ptr and slot.get('file') in n.assetByFile:struct.pack_into('<Q',state,p,n.assetByFile[slot['file']]+ptr)
            ptr=struct.unpack_from('<Q',state,0x100)[0]
            if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
            m.mem_write(n.owner+slot['offset'],bytes(state))
        initial=c['initial']
        for p,key in [(0x168b0,'state'),(0x9638,'frame'),(0x28,'selection'),(0x30,'pulse'),(0x2c,'totalFrame')]:m.mem_write(n.owner+p,struct.pack('<i',initial[key]))
        m.mem_write(n.owner+0x168d1,bytes([initial['practice']]));m.mem_write(0x1404f27c0,struct.pack('<i',initial['difficulty']));m.mem_write(0x140c21db9,bytes([1]));m.mem_write(0x1404f1e80,bytes([initial['configuredCharacter']]));m.mem_write(0x1404f1e81,bytes([initial['configuredShot']]));m.mem_write(0x140c21dbb,bytes([c['configuredMode']]))
        for char,row in enumerate(c['extraUnlockedShots']):
            for shot,clear in enumerate(row):
                for offset in [0x4ff101,0x4ff102,0x4ff103]:m.mem_write(0x140000000+offset+char*48+shot*24,bytes([99 if clear else 0]))
        m.mem_write(0x140a6ec60,struct.pack('<II',c['keys']['held'],c['keys']['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['keys']['repeat']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');effects.clear()
        for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,4),(UC_X86_REG_R13,11),(UC_X86_REG_R15,0x100),(UC_X86_REG_RDI,8),(UC_X86_REG_RDX,c['keys']['held']),(UC_X86_REG_R8,c['keys']['previous']),(UC_X86_REG_R9,c['keys']['repeat']),(UC_X86_REG_R11,6)]:m.reg_write(reg,value)
        m.emu_start(0x14004b922,n.stack,count=1000000)
        actual=dict(initial)
        for p,key in [(0x168b0,'state'),(0x9638,'frame'),(0x28,'selection'),(0x30,'pulse'),(0x2c,'totalFrame')]:actual[key]=struct.unpack('<i',m.mem_read(n.owner+p,4))[0]
        actual['difficulty']=struct.unpack('<i',m.mem_read(0x1404f27c0,4))[0];actual['configuredDifficulty']=m.mem_read(0x140c21db9,1)[0]
        actual['configuredCharacter']=m.mem_read(0x1404f1e80,1)[0];actual['configuredShot']=m.mem_read(0x1404f1e81,1)[0]
        result=dict(state=actual,effects=effects.copy(),soundSlots=list(struct.unpack('<3i',m.mem_read(0x140509670,12))))
        assert result==c['result'],(index,result,c['result'])
        for slot in c['after']:
            actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
            for p in [0xf0,0xf8]:
                ptr=struct.unpack_from('<Q',actual,p)[0]
                if n.assets<=ptr<n.assets+0x200000:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            ptr=struct.unpack_from('<Q',actual,0x100)[0]
            if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
            wanted=bytes.fromhex(slot['state']);diff=[hex(i) for i,(x,y) in enumerate(zip(actual,wanted)) if x!=y];assert not diff,(index,slot['offset'],diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),vmComparisons=len(data['cases'])*154,stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/title-shot-update.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-title-shot-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))


if __name__=='__main__':main()


