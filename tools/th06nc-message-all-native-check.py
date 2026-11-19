"""Every unique message script through termination or native scene request.

Real message/ANM/STD resources, all stages, passive/skip/pulsed input, live or
absent sound handle, and both Extra capture branches. Full HUD bytes, global
scene/music state and ordered service requests compared. Localization, texture
publication, audio APIs and achievement APIs are observed boundaries; actual
host transitions, playback, persistence and GPU output excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

FIELDS={'stageIndex':(0x4f1e84,'i'),'difficulty':(0x4f27c0,'i'),'replay':(0x4f27b4,'B'),'replayPlayback':(0x4f278c,'B'),'lifeProtection':(0x4f27c4,'B'),'deathCount':(0x4f1e60,'i'),'extraCaptures':(0x4f1e6c,'i'),'suppressSpawn':(0xa6eb90,'B'),'messageTaskSuspended':(0x4f27b3,'B'),'continueState':(0x4ff0f2,'b'),'gameState':(0xc21d9c,'i'),'score':(0x4f2798,'Q'),'displayScore':(0x4f2790,'Q')}
MUSIC={'handle':(0x50966c,'i'),'playing':(0x50967c,'B'),'fading':(0x509668,'B'),'fadeStart':(0x509660,'i'),'fadeFrame':(0x509664,'i'),'pendingValue':(0x509690,'i'),'requestActive':(0xc21c0c,'B')}

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['message-layout','message','message-open','message-state','message-command','message-music','message-progress','music-state','message-update','stage-music']];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{messageAssetPlan}from'./shared/th06nc/message-layout.mjs';import{messageProgressAssetPlan}from'./shared/th06nc/message-progress.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readMessage}from'./shared/th06nc/message.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{readStageMusic}from'./shared/th06nc/stage-music.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex'),serial=e=>({...e,score:String(e.score),displayScore:String(e.displayScore),musicState:{...e.musicState}});let uniqueScripts=0;
for(let file=1;file<=7;file++){
 const program=readMessage(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg'+file+'.dat'));uniqueScripts+=program.uniqueScripts.length;
 for(const dialog of program.uniqueScripts)for(const mode of ['passive','skip','advance'])for(const handle of [-1,17])for(const captures of dialog.instructions.some(i=>i.opcode===14)?[5,6]:[5]){
  const id=program.offsets.indexOf(dialog.offset),character=id>=10?1:0,refs=[...messageAssetPlan(file,character),...messageProgressAssetPlan(file)],special=file===6&&(id===0||id===10)?[{archive:'th06ST.dat',file:'eff06.anm',slot:11,base:0x2d3}]:file===7&&id!==2&&id!==12?[{archive:'th06ST.dat',file:'eff07.anm',slot:11,base:0x2d3},{archive:'th06ST.dat',file:'face12c.anm',slot:18,base:0x4c6}]:[];refs.push(...special);const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
  const environment={stageIndex:file,difficulty:1,replay:false,replayPlayback:false,lifeProtection:false,deathCount:0,extraCaptures:captures,suppressSpawn:false,messageTaskSuspended:false,continueState:0,gameState:42,score:12345678n,displayScore:99n,musicState:{handle,playing:true,fading:false,fadeStart:77,fadeFrame:88,pendingValue:99,requestActive:true}},initialEnvironment=serial(environment),state=new MessageState(program,{anmBank:bank,environment}),musicTracks=readStageMusic(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+file+'.std'));state.rebind(0x3b60,0x785);const initial=hex(state.bytes),openEvents=[];state.open(id,{cancelProjectiles:()=>{},loadAnm:r=>openEvents.push(r)});const frames=[];let previousInput=0,endFrame=null;
  for(let frame=1;frame<=30000;frame++){const input=mode==='skip'?8:mode==='advance'&&frame%16===0?1:0,events=[],result=state.tick(input,{previousInput,musicTracks,publishText:r=>events.push({kind:'text',...r}),playMusic:r=>events.push({kind:'music',...r}),stopMusic:r=>events.push({kind:'stop',...r}),releaseMusic:r=>events.push({kind:'release',...r}),awardAchievement:key=>events.push({kind:'achievement',key}),commitAchievements:()=>events.push({kind:'commit'})});previousInput=input;const terminal=result<0||state.v.getInt32(0x36b0,true)<0||environment.gameState!==42;if(frame<4||frame%64===0||events.length||terminal)frames.push({frame,result,events,afterSha256:sha(state.bytes),environment:serial(environment)});if(terminal){endFrame=frame;break;}}
  if(endFrame===null)throw Error('Dialog did not end: '+file+'/'+id+'/'+mode);scenes.push({file,character,mode,id,refs,initial,initialEnvironment,openEvents,endFrame,frames});
 }
}console.log(JSON.stringify({uniqueScripts,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));scenes=data['scenes'];n=Native();m=n.m;programBase=n.assets+0x100000;stdBase=n.assets+0x120000;table=n.vm;events=[];openEvents=[];digest=hashlib.sha256();checked=0
    holder=n.vm+0xa000;interface=holder+0x10;vtable=holder+0x100;award=holder+0x200;commit=award+0x10;getApi=award+0x20;m.mem_write(holder,struct.pack('<Q',interface));m.mem_write(interface,struct.pack('<Q',vtable));m.mem_write(vtable+0x30,struct.pack('<Q',award));m.mem_write(vtable+0x48,struct.pack('<Q',commit));m.mem_write(0x1402c0630,struct.pack('<Q',getApi))
    for ptr in [award,commit,getApi]:m.mem_write(ptr,b'\xc3')
    def hook(m,a,size,u):
        if a in [0x14003f1eb,0x14003f771,0x14003f591]:m.reg_write(UC_X86_REG_RIP,{0x14003f1eb:0x14003f28f,0x14003f771:0x14003f80f,0x14003f591:0x14003f62f}[a]);return
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400020b0:
            # Special resources are preloaded at exactly the requested native slots.
            openEvents.append(dict(slot=m.reg_read(UC_X86_REG_EDX),file=bytes(m.mem_read(m.reg_read(UC_X86_REG_R8),128)).split(b'\0')[0].decode(),base=m.reg_read(UC_X86_REG_R9D)));m.reg_write(UC_X86_REG_EAX,0)
        elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);string=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(string,128)).split(b'\0')[0].decode();events.append(dict(kind='text',offset=ptr-n.owner,key=key,text=key,colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),struct.unpack('<I',m.mem_read(sp+0x28,4))[0],struct.unpack('<I',m.mem_read(sp+0x30,4))[0]]))
        elif a==0x14007bc80:events.append(dict(kind='music',file=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),128)).split(b'\0')[0].decode()))
        elif a==getApi:m.reg_write(UC_X86_REG_RAX,holder)
        elif a==award:events.append(dict(kind='achievement',key=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),64)).split(b'\0')[0].decode()));m.reg_write(UC_X86_REG_EAX,1)
        elif a==commit:events.append(dict(kind='commit'));m.reg_write(UC_X86_REG_EAX,1)
        elif a==0x1400cce50:events.append(dict(kind='stop',handle=m.reg_read(UC_X86_REG_ECX),mode=m.reg_read(UC_X86_REG_EDX)))
        elif a==0x14007f9c0:events.append(dict(kind='release',handle=m.reg_read(UC_X86_REG_ECX)))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400020b0,0x14003f1eb,0x14003f771,0x14003f591,0x1402bdee2,0x140007530,0x14007bc80,0x1400cce50,0x14007f9c0,award,commit,getApi]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    offsets=[0,0x480,0x5a0,0x3428,0x3548,0x36b8,0x37d8,0x3910,0x3a30,0x3b60,0xa80,0x28e0]
    def normalize(state,encode=False):
        for offset in offsets:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',state,p)[0]
                if ptr:struct.pack_into('<Q',state,p,n.assetByFile['msgframe.anm']+ptr if encode else ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def run(addr):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(addr,n.stack+0xf000,count=1000000)
    for index,s in enumerate(scenes):
        n.load_title(s['refs']);raw=(ROOT/f"runtimes/th06nc/artifacts/scripts/th06ST.dat/msg{s['file']}.dat").read_bytes();m.mem_write(programBase,raw);m.mem_write(stdBase,(ROOT/f"runtimes/th06nc/artifacts/scripts/th06ST.dat/stage{s['file']}.std").read_bytes());m.mem_write(0x140509c08,struct.pack('<Q',stdBase));count=struct.unpack_from('<I',raw)[0]
        for i in range(count):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',raw,4+i*4)[0]))
        initial=bytearray.fromhex(s['initial']);normalize(initial,True);struct.pack_into('<Q',initial,0x38f8,programBase);struct.pack_into('<Q',initial,0x3b58,table);m.mem_write(n.owner,bytes(initial))
        for key,(off,fmt)in FIELDS.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(s['initialEnvironment'][key])))
        for key,(off,fmt)in MUSIC.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(s['initialEnvironment']['musicState'][key])))
        m.mem_write(0x1403ec2a8,bytes(640*0x620));m.mem_write(0x1404e12b8,bytes(64*0x298));m.reg_write(UC_X86_REG_EDX,s['id']);openEvents.clear();run(0x14003ece0)
        wantedOpen=[dict(slot=r['slot'],file='data/'+r['file'],base=r['base'])for r in s['openEvents']];assert openEvents==wantedOpen,(index,'open assets',openEvents,wantedOpen)
        previousInput=0;byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,s['endFrame']+1):
            current=8 if s['mode']=='skip'else 1 if s['mode']=='advance'and frame%16==0 else 0;m.mem_write(0x140a6ec60,struct.pack('<2I',current,previousInput));previousInput=current;events.clear();run(0x14003eee0)
            if frame not in byFrame:continue
            c=byFrame[frame];result=m.reg_read(UC_X86_REG_EAX);assert result==c['result']&0xffffffff,(index,frame,'result',result,c['result']);assert events==c['events'],(index,frame,'events',events,c['events'])
            for key,(off,fmt)in FIELDS.items():
                value=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert value==int(c['environment'][key]),(index,frame,key,value,c['environment'][key])
            for key,(off,fmt)in MUSIC.items():
                value=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert value==int(c['environment']['musicState'][key]),(index,frame,key,value,c['environment']['musicState'][key])
            actual=bytearray(m.mem_read(n.owner,0x4000));normalize(actual);struct.pack_into('<Q',actual,0x38f8,1);struct.pack_into('<Q',actual,0x3b58,1);ptr=struct.unpack_from('<Q',actual,0x3668)[0];struct.pack_into('<Q',actual,0x3668,ptr-programBase if ptr else 0);actualHash=hashlib.sha256(actual).hexdigest();assert actualHash==c['afterSha256'],(index,s['file'],s['id'],s['mode'],frame,'HUD bytes',actualHash,c['afterSha256']);digest.update(actual);checked+=1
        if index%30==0:print(json.dumps(dict(progress=index+1,scenes=len(scenes),checkpoints=checked)),flush=True)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,uniqueScripts=data['uniqueScripts'],scenes=len(scenes),frames=sum(s['endFrame']for s in scenes),checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-message-all-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
