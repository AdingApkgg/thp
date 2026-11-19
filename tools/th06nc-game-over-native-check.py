"""GameOver b4f0 and bce0: whole owner, continue globals and ordered draws.

Actual ANM/float/int/fade code executes. Screenshot capture and GPU are
observed boundaries; score-entry/replay/spell-practice destinations are requests.
No complete run, persisted score, native input-device or music equivalence.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['game-over-menu','pause-menu','anm-bank','anm-rebind','anm-vm','fade','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{pauseAsset}from'./shared/th06nc/pause-menu.mjs';import{GameOverMenu}from'./shared/th06nc/game-over-menu.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const refs=[pauseAsset,{archive:'th06IN.dat',file:'ascii.anm',slot:1,base:0}],scenes=[],hex=b=>Buffer.from(b).toString('hex'),encode=e=>JSON.parse(JSON.stringify(e,(_,x)=>typeof x==='bigint'?String(x):x)),paths=[{},{40:16,50:256},{40:256},{3:16,8:256,40:48,50:256},{40:16,44:32,50:256}];
const specs=[];for(const path of paths)for(const continuesUsed of [0,1,2,3])for(const difficulty of [1,4])for(const soundDisabled of [false,true])for(const fullQueue of [false,true])specs.push({path,continuesUsed,difficulty,soundDisabled,fullQueue});for(const practice of [false,true])for(const replayPlayback of [false,true])for(const spellPractice of [false,true])if(practice||replayPlayback||spellPractice)specs.push({path:{},continuesUsed:0,difficulty:1,practice,replayPlayback,spellPractice});
for(const continuesUsed of [0,1,2])specs.push({path:{40:16,50:256},continuesUsed,difficulty:1,repeatDeaths:true});
for(const spec of specs){const {path,soundDisabled=false,fullQueue=false,...flags}=spec,bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const fade=new NativeFade(),environment={practice:false,replayPlayback:false,spellPractice:false,gameOverRequested:true,score:123456789n,displayScore:120000000n,scoreDisplayStep:10000n,highScore:987654321n,continuesUsed:0,difficulty:1,defaultLives:2,defaultBombs:3,lives:0,bombs:1,inputFlags:0xdeadbeef,totalGraze:456,stageGraze:123,playerPower:27,pointStageCount:29,pointTotalCount:83,continueState:-1,...flags},sounds=fullQueue?[12,10,11]:[-1,-1,-1],initial=encode(environment),menu=new GameOverMenu(bank,{environment,fade,soundSlots:sounds,soundDisabled}),frames=[];let previous=0,age=0;for(let frame=1;frame<=(flags.repeatDeaths?400:120);frame++){const opened=!menu.active;if(opened){menu.active=true;environment.gameOverRequested=true;age=0;}age++;const held=path[age]??0;fade.tick();menu.tick({held,previous});previous=held;const calls=[];if(menu.active)menu.draw((vm,r)=>calls.push({offset:r.offset,state:hex(vm.state)}));frames.push({frame,held,opened,state:hex(menu.bytes),active:menu.active,event:menu.event,environment:encode(environment),soundDisabled:menu.soundDisabled,sounds:[...sounds],fade:hex(fade.state),calls});if(!menu.active&&(!flags.repeatDeaths||menu.event.kind!=='continue'))break;}scenes.push({initial,soundDisabled,fullQueue,frames});}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);draws=[];digest=hashlib.sha256();checked=0;requests={}
    fields={'continuesUsed':(0x1404ff0dc,'B'),'difficulty':(0x1404f27c0,'i'),'defaultLives':(0x140c21de0,'B'),'defaultBombs':(0x140c21de1,'B'),'lives':(0x1404ff0f0,'B'),'bombs':(0x1404ff0f1,'B'),'inputFlags':(0x140a6ec18,'I'),'totalGraze':(0x1404ff0cc,'i'),'stageGraze':(0x1404ff0d0,'i'),'playerPower':(0x1404f1e88,'H'),'pointStageCount':(0x1404f27ba,'H'),'pointTotalCount':(0x1404f27bc,'H'),'continueState':(0x1404ff0f2,'b'),'practice':(0x1404f27b4,'B'),'replayPlayback':(0x1404f278c,'B'),'spellPractice':(0x1404f27b5,'B'),'gameOverRequested':(0x1404f27b1,'B'),'score':(0x1404f2798,'Q'),'displayScore':(0x1404f2790,'Q'),'scoreDisplayStep':(0x1404f27a0,'Q'),'highScore':(0x1404f27a8,'Q')}
    def normal_vm(raw):
        raw=bytearray(raw)
        for p in [0xf0,0xf8]:
            ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
        ptr=struct.unpack_from('<Q',raw,0x100)[0]
        if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
        return raw
    def normalize():
        raw=bytearray(m.mem_read(n.owner,0xda0))
        for p in [*range(0,5*288,288),0xb50,0xc70]:raw[p:p+288]=normal_vm(raw[p:p+288])
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400067f0:
            ptr=m.reg_read(UC_X86_REG_RDX);raw=normal_vm(bytes(m.mem_read(ptr,288)));id=struct.unpack_from('<H',raw,0x38)[0];offset={0x771:0,0x772:0x120,0x76f:0x240,0x770:0x360,0x773:0xc70}[id]
            if id==0x772 and struct.unpack_from('<Q',raw,0x100)[0]<=256:offset=0x480
            assert m.reg_read(UC_X86_REG_R8)&255==1
            draws.append(dict(offset=offset,state=raw.hex()))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400067f0,0x14007af40,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,bytes(0xda0));m.mem_write(n.vm,bytes(0x10000));m.mem_write(0x140c21e03,b'\0');m.mem_write(0x140509670,struct.pack('<3i',*([12,10,11]if s['fullQueue']else[-1,-1,-1])));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140c22158,struct.pack('<Q',n.vm));m.mem_write(0x140c21d9c,bytes(4));m.mem_write(0x1404f27b6,b'\0');m.mem_write(0x1403e61c4,struct.pack('<i',9));m.mem_write(0x1403e61c8,b'\7');m.mem_write(0x1403e5f7c,struct.pack('<i',13))
        for field,(address,fmt)in fields.items():m.mem_write(address,struct.pack('<'+fmt,int(s['initial'][field])))
        previous=0
        for c in s['frames']:
            frame=c['frame'];
            if c['opened']:m.mem_write(0x1404f27b1,b'\1')
            m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],previous));previous=c['held'];run(0x140075af0,n.vm);run(0x14000b4f0,n.owner);draws.clear();run(0x14000bce0,n.owner);actual=normalize();expected=bytes.fromhex(c['state'])
            if actual!=expected:
                diff=[hex(i)for i,(a,b)in enumerate(zip(actual,expected))if a!=b];raise AssertionError((index,frame,'owner',diff[:20],[(p,actual[int(p,16)],expected[int(p,16)])for p in diff[:10]]))
            assert len(draws)==len(c['calls']),(index,frame,'draw count',len(draws),len(c['calls']))
            for i,(a,b)in enumerate(zip(draws,c['calls'])):
                assert a==b,(index,frame,'draw VM',i,next((hex(j)for j,(x,y)in enumerate(zip(bytes.fromhex(a['state']),bytes.fromhex(b['state'])))if x!=y),None))
            for field,(address,fmt)in fields.items():assert struct.unpack('<'+fmt,m.mem_read(address,struct.calcsize(fmt)))[0]==int(c['environment'][field]),(index,frame,field)
            assert bool(m.mem_read(0x140509694,1)[0])==c['soundDisabled'],(index,frame,'disabled');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,frame,'sounds');assert bytes(m.mem_read(n.vm,56)).hex()==c['fade'],(index,frame,'fade')
            if c['event']:
                kind=c['event']['kind'];requests[kind]=requests.get(kind,0)+1
                if kind in ['scoreEntry','replaySelect']:assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==(8 if kind=='replaySelect'else 7),(index,frame,'supervisor')
                if kind=='spellPracticeResult':assert bytes(m.mem_read(0x1404f27b6,1))==b'\1' and bytes(m.mem_read(0x1403e61c4,5))==bytes(5) and bytes(m.mem_read(0x1403e5f7c,4))==bytes(4),(index,frame,'spell result')
            digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,requests=requests,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-game-over-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
