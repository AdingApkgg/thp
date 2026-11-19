"""Ordinary result states 9/15/16 through state-10 replay-selection handoff, 6e3a0.

Real result ANMs, candidate lists, input, common tail, sounds and fade.
Rank lists are prebuilt logical inputs; their head pointers are normalized.
Localized profile text/font crop and achievement/config writes are services.
Loading I/O, result drawing, replay destination and disk excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    names=['result-name-scene','result-summary','result-summary-draw','result-state','result-name-draw','score-qualify','score-name-input','score-tables','score-file','ascii-text','score-popup-draw','title-navigation','fade','sound-queue','anm-bank','anm-rebind','anm-vm'];hashes={f'shared/th06nc/{s}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{s}.mjs').read_bytes()).hexdigest()for s in names};script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{resultAssets,resultTextAsset}from'./shared/th06nc/result-state.mjs';import{ResultNameScene}from'./shared/th06nc/result-name-scene.mjs';import{createDefaultScoreTables}from'./shared/th06nc/score-tables.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';const refs=[...resultAssets,resultTextAsset,{archive:'th06IN.dat',file:'ascii.anm',slot:1,base:0}],bank=new AnmBank(),sha=b=>createHash('sha256').update(b).digest('hex'),hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const localization=Object.fromEntries(['EXE_REIMU_A_NAME','EXE_REIMU_B_NAME','EXE_MARISA_A_NAME','EXE_MARISA_B_NAME','EXE_RESULT_MODE_NORMAL_NAME','EXE_RESULT_MODE_CHALLENGE_NAME'].map((key,i)=>[key,i<4?'P'+i:'M'+(i-4)])),defaults=[...createDefaultScoreTables().values()].map(t=>t.map(hex)),scenes=[];
for(const character of [0,1])for(const shot of [0,1])for(const difficulty of [1,4])for(const lifeProtection of [false,true])for(const score of [0n,410721n,9999999990n])for(const previousName of ['', 'PREVIOUS']){const environment={character,shot,difficulty,lifeProtection,score,stageIndex:3},fade=new NativeFade();fade.requestOut(0,0);fade.tick();const events=[],scene=new ResultNameScene(bank,{environment,fade,previousName,localization,publishText:(vm,r)=>{events.push({kind:'font',offset:vm.state.byteOffset,...r});[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);},achievement:id=>events.push({kind:'achievement',id}),saveName:bytes=>events.push({kind:'saveName',bytes:[...bytes]})}),frames=[];for(let frame=1;frame<=240;frame++){events.length=0;const held=({35:256,39:128,40:256,51:1024,55:256,142:256})[frame]??0,previous=scene.input.held,event=scene.state.v.getInt32(0x9e94,true)===9?scene.tick(held):scene.tickSummary(held);frames.push({held,previous,events:[...events],ownerSha256:sha(scene.state.bytes),fadeSha256:sha(scene.fade.state),sounds:[...scene.sounds],state:scene.report(),event});if(event?.kind==='replaySelection')break;}scenes.push({environment:{...environment,score:String(score)},previousName,frames});}console.log(JSON.stringify({refs,defaults,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);cursor=n.vm+0x7000;events=[];digest=hashlib.sha256();checked=0;offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310];fadePtr=n.vm+0x1000;m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000))
    def normalized():
        raw=bytearray(m.mem_read(n.owner,0xbb48));raw[0x4458:0x49f8]=bytes(0x5a0)
        for offset in offsets:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return raw
    def hook(m,a,size,u):
        nonlocal cursor
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:
            count=m.reg_read(UC_X86_REG_RCX);out=cursor;cursor+=(count+15)&~15;assert cursor<n.vm+0x9000;m.mem_write(out,bytes(count));m.reg_write(UC_X86_REG_RAX,out)
        elif a==0x14006cf80:
            profile=m.reg_read(UC_X86_REG_EDX);mode=m.reg_read(UC_X86_REG_R8D);assert profile in range(4)and mode in range(2);m.mem_write(m.reg_read(UC_X86_REG_RCX),f'P{profile} / M{mode}'.encode()+b'\0')
        elif a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);textPtr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];text=bytes(m.mem_read(textPtr,100)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];events.append(dict(kind='font',offset=ptr-n.owner,text=text,colors=colors));m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0];m.mem_write(ptr+0xc4,struct.pack('<I',flags|1))
        elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x140067cb0:events.append(dict(kind='achievement',id=bytes(m.mem_read(m.reg_read(UC_X86_REG_RCX),40)).split(b'\0')[0].decode()))
        elif a==0x14007bc00:events.append(dict(kind='saveName',bytes=list(m.mem_read(m.reg_read(UC_X86_REG_RDX),9))))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [n.vm+0x9000,0x14006cf80,0x140007530,0x1402bdee2,0x1402bcf20,0x140067cb0,0x14007bc00]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);baseline=bytes(m.mem_read(n.owner,0xbb48))
    for index,s in enumerate(data['scenes']):
        e=s['environment'];m.mem_write(n.owner,baseline);m.mem_write(n.owner+0x9e94,struct.pack('<i',9));m.mem_write(n.owner+0x9e9c,struct.pack('<i',9));m.mem_write(0x1404f1e80,bytes([e['character'],e['shot']]));m.mem_write(0x1404f27c0,struct.pack('<i',e['difficulty']));m.mem_write(0x1404f27c4,bytes([e['lifeProtection']]));m.mem_write(0x1404f2798,struct.pack('<Q',int(e['score'])));m.mem_write(0x1404f1e84,b'\3');m.mem_write(0x1404f27b3,b'\0');m.mem_write(0x140c21dc4,bytes(128));m.mem_write(0x140c21dc4,s['previousName'].encode());m.mem_write(0x140509694,b'\0');m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140c22158,struct.pack('<Q',fadePtr));fade=bytearray(56);struct.pack_into('<3i',fade,0,30,-999,0);struct.pack_into('<2i',fade,0x28,255,255);struct.pack_into('<i',fade,0x34,3);m.mem_write(fadePtr,bytes(fade));cursor=n.vm+0x7000
        for tableIndex,table in enumerate(data['defaults']):
            first=n.vm+0x2000+tableIndex*10*32;head=n.owner+0x4458+tableIndex*24;m.mem_write(head+16,struct.pack('<Q',first))
            for row,record in enumerate(table):
                ptr=n.assets+0x100000+tableIndex*10*64+row*64;m.mem_write(ptr,bytes.fromhex(record));m.mem_write(first+row*32,struct.pack('<3Q',ptr,head if row==0 else first+(row-1)*32,first+(row+1)*32 if row<9 else 0))
        previous=0;inputClock=0
        for frame,c in enumerate(s['frames'],1):
            held=c['held'];repeat=0
            if held==previous:
                if inputClock>=30 and inputClock&7==0:repeat=1
                if inputClock>=38:inputClock=30
                inputClock+=1
            else:inputClock=0
            m.mem_write(0x140a6ec60,struct.pack('<2I',held,previous));m.mem_write(0x140a6ec48,struct.pack('<i',repeat));previous=held;events.clear();run(0x140075af0,fadePtr);run(0x14006e3a0,n.owner);actual=normalized();assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,frame,'owner');assert hashlib.sha256(bytes(m.mem_read(fadePtr,56))).hexdigest()==c['fadeSha256'],(index,frame,'fade');assert events==c['events'],(index,frame,'services',events,c['events']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,frame,'sounds');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-summary-scene-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
