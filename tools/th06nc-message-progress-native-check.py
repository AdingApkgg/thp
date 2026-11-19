"""Remaining message progress/audio branches: 7(-1),9,11,12,14.

Full HUD bytes, real loading/secret ANM, music globals and scene-state fields
compared. Achievement and sound-handle APIs are observed service boundaries;
host scene replacement, persistence, playback and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/message-command.mjs','shared/th06nc/message-progress.mjs','shared/th06nc/message-music.mjs','shared/th06nc/music-state.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readMessage}from'./shared/th06nc/message.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{messageProgressAssetPlan}from'./shared/th06nc/message-progress.mjs';import{applyMessageCommand}from'./shared/th06nc/message-command.mjs';const refs=messageProgressAssetPlan(7),bank=new AnmBank(),program=readMessage(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg7.dat')),cases=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
function run(op,options={}){const environment={stageIndex:1,difficulty:1,practice:false,replayPlayback:false,lifeProtection:false,deathCount:2,extraCaptures:0,timelineResumeRequested:false,messageTaskSuspended:false,continueState:0,gameState:42,score:0xfffffffffffffff0n,displayScore:123n,musicState:{handle:-1,playing:false,fading:false,fadeStart:77,fadeFrame:88,pendingValue:99,requestActive:true},...options},initial={...environment,score:String(environment.score),displayScore:String(environment.displayScore),musicState:{...environment.musicState}},state=new MessageState(program,{anmBank:bank,environment}),v=state.v;v.setInt32(0x36b0,11,true);v.setInt32(0x958,99,true);v.setUint8(0x715,options.hudFlag??0);v.setUint8(0x716,1);v.setUint16(0x34,17,true);v.setUint16(0x296a,9,true);const events=[],args=new Uint8Array(4);new DataView(args.buffer).setInt32(0,-1,true);const action=applyMessageCommand(state,{opcode:op,args},{awardAchievement:key=>events.push({kind:'achievement',key}),commitAchievements:()=>events.push({kind:'commit'}),stopMusic:r=>events.push({kind:'stop',...r}),releaseMusic:r=>events.push({kind:'release',...r})});cases.push({op,initial,action,events,environment:{...environment,score:String(environment.score),displayScore:String(environment.displayScore)},sha256:createHash('sha256').update(state.bytes).digest('hex')});}
for(let stageIndex=1;stageIndex<=7;stageIndex++)for(const difficulty of [0,1,2,3,4])for(const practice of [false,true])for(const replayPlayback of [false,true])run(11,{stageIndex,difficulty,practice,replayPlayback});
for(let stageIndex=1;stageIndex<=7;stageIndex++)for(const replayPlayback of [false,true])for(const hudFlag of [0,1])run(9,{stageIndex,replayPlayback,hudFlag});
for(const stageIndex of [1,7])for(const extraCaptures of [5,6,10])for(const lifeProtection of [false,true])for(const deathCount of [0,2,3,99])for(const timelineResumeRequested of [false,true])run(14,{stageIndex,extraCaptures,lifeProtection,deathCount,timelineResumeRequested});
for(const op of [7,12])for(const handle of [-1,17])for(const playing of [false,true])for(const fading of [false,true])for(const requestActive of [false,true])run(op,{musicState:{handle,playing,fading,requestActive,fadeStart:77,fadeFrame:88,pendingValue:99}});console.log(JSON.stringify({refs,cases}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;events=[];action=None;digest=hashlib.sha256()
    fields={'stageIndex':(0x4f1e84,'i'),'difficulty':(0x4f27c0,'i'),'practice':(0x4f27b4,'B'),'replayPlayback':(0x4f278c,'B'),'lifeProtection':(0x4f27c4,'B'),'deathCount':(0x4f1e60,'i'),'extraCaptures':(0x4f1e6c,'i'),'timelineResumeRequested':(0xa6eb90,'B'),'messageTaskSuspended':(0x4f27b3,'B'),'continueState':(0x4ff0f2,'b'),'gameState':(0xc21d9c,'i'),'score':(0x4f2798,'Q'),'displayScore':(0x4f2790,'Q')};musicFields={'handle':(0x50966c,'i'),'playing':(0x50967c,'B'),'fading':(0x509668,'B'),'fadeStart':(0x509660,'i'),'fadeFrame':(0x509664,'i'),'pendingValue':(0x509690,'i'),'requestActive':(0xc21c0c,'B')}
    holder=n.vm+0xa000;interface=holder+0x10;vtable=holder+0x100;award=holder+0x200;commit=award+0x10;getApi=award+0x20;m.mem_write(holder,struct.pack('<Q',interface));m.mem_write(interface,struct.pack('<Q',vtable));m.mem_write(vtable+0x30,struct.pack('<Q',award));m.mem_write(vtable+0x48,struct.pack('<Q',commit));m.mem_write(0x1402c0630,struct.pack('<Q',getApi))
    for ptr in [award,commit,getApi]:m.mem_write(ptr,b'\xc3')
    def hook(m,a,size,u):
        nonlocal action
        if a in [0x14003f2f0,0x14003f32d,0x14003fc10]:action='advance'if a==0x14003f2f0 else'wait'if a==0x14003f32d else'return';m.emu_stop();return
        if a==getApi:m.reg_write(UC_X86_REG_RAX,holder)
        elif a==award:events.append(dict(kind='achievement',key=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),64)).split(b'\0')[0].decode()));m.reg_write(UC_X86_REG_EAX,1)
        elif a==commit:events.append(dict(kind='commit'));m.reg_write(UC_X86_REG_EAX,1)
        elif a==0x1400cce50:events.append(dict(kind='stop',handle=m.reg_read(UC_X86_REG_ECX),mode=m.reg_read(UC_X86_REG_EDX)))
        elif a==0x14007f9c0:events.append(dict(kind='release',handle=m.reg_read(UC_X86_REG_ECX)))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14003f2f0,0x14003f32d,0x14003fc10,0x1400cce50,0x14007f9c0,award,commit,getApi]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    starts={7:0x3f49d,9:0x3f82d,11:0x3fb51,12:0x3f9e4,14:0x3fa28};m.mem_write(n.assets+0x100000,struct.pack('<HBBi',0,7,4,-1))
    for index,c in enumerate(data['cases']):
        env=c['initial'];initial=bytearray(0x4000);struct.pack_into('<i',initial,0x36b0,11);struct.pack_into('<i',initial,0x958,99);initial[0x715]=env.get('hudFlag',0);initial[0x716]=1;struct.pack_into('<H',initial,0x34,17);struct.pack_into('<H',initial,0x296a,9);struct.pack_into('<Q',initial,0x38f8,1);struct.pack_into('<Q',initial,0x3b58,1);m.mem_write(n.owner,bytes(initial))
        for key,(off,fmt)in fields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(env[key])))
        for key,(off,fmt)in musicFields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(env['musicState'][key])))
        events.clear();action=None
        for reg,value in [(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R14,n.assets+0x100000),(UC_X86_REG_R12,0xffffffffffffffff),(UC_X86_REG_RSI,0),(UC_X86_REG_R8D,1),(UC_X86_REG_R10D,0x648),(UC_X86_REG_R11D,0x730),(UC_X86_REG_R15D,0x731),(UC_X86_REG_RDX,0x140000000),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x140000000+starts[c['op']],n.stack+0xf000,count=1000000);assert action==c['action'],(index,c['op'],'action',action,c['action']);assert events==c['events'],(index,c['op'],'events',events,c['events'])
        for key,(off,fmt)in fields.items():
            value=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert value==int(c['environment'][key]),(index,c['op'],key,value,c['environment'][key])
        for key,(off,fmt)in musicFields.items():
            value=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert value==int(c['environment']['musicState'][key]),(index,c['op'],key,value,c['environment']['musicState'][key])
        actual=bytearray(m.mem_read(n.owner,0x4000))
        for offset in [0,0x480,0x5a0]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,c['op'],'HUD bytes');digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-message-progress-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
