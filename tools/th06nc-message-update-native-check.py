"""Whole common dialog step 3eee0 with real message programs and portrait/frame ANM.

Opening scenes for both characters, passive/skip/advance input, wait timers,
music metadata and frame alpha. Actual text ANM and native frame/resource bases. Special ANM loading, text texture publication/localization and audio
transport are observed services. Stage completion/ending commands excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/message-layout.mjs','shared/th06nc/message.mjs','shared/th06nc/message-open.mjs','shared/th06nc/message-state.mjs','shared/th06nc/message-command.mjs','shared/th06nc/message-music.mjs','shared/th06nc/message-update.mjs','shared/th06nc/stage-music.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{messageAssetPlan}from'./shared/th06nc/message-layout.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readMessage}from'./shared/th06nc/message.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{advanceMessage}from'./shared/th06nc/message-update.mjs';import{readStageMusic}from'./shared/th06nc/stage-music.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const file of [1,2,3,4,5,6])for(const character of [0,1])for(const mode of ['passive','skip','advance']){
 const refs=messageAssetPlan(file,character),bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const raw=readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg'+file+'.dat'),program=readMessage(raw),state=new MessageState(program,{anmBank:bank,environment:{stageIndex:file}}),musicTracks=readStageMusic(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+file+'.std'));state.rebind(0x3b60,0x785);const initial=hex(state.bytes),id=character*10;state.open(id,{cancelProjectiles:()=>{},loadAnm:()=>{}});const frames=[];let previousInput=0,endFrame=null;
 for(let frame=1;frame<=30000;frame++){const input=mode==='skip'?8:mode==='advance'&&frame%16===0?1:0,events=[],result=advanceMessage(state,{input,previousInput,musicTracks,publishText:r=>events.push({kind:'text',...r}),playMusic:r=>events.push({kind:'music',...r})});previousInput=input;if(frame<4||frame%32===0||events.length||result<0)frames.push({frame,result,input,events,after:hex(state.bytes)});if(result<0){endFrame=frame;break;}}if(endFrame===null)throw Error('Dialog did not end: '+file+'/'+character+'/'+mode);scenes.push({file,character,mode,id,refs,initial,endFrame,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;programBase=n.assets+0x100000;stdBase=n.assets+0x120000;table=n.vm;events=[];digest=hashlib.sha256();checked=0
    def hook(m,a,size,u):
        if a in [0x14003f1eb,0x14003f771,0x14003f591]:m.reg_write(UC_X86_REG_RIP,{0x14003f1eb:0x14003f28f,0x14003f771:0x14003f80f,0x14003f591:0x14003f62f}[a]);return
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400020b0:m.reg_write(UC_X86_REG_EAX,0)
        elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x140007530:
            ptr=m.reg_read(UC_X86_REG_RDX);string=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(string,128)).split(b'\0')[0].decode();events.append(dict(kind='text',offset=ptr-n.owner,key=key,text=key,colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),struct.unpack('<I',m.mem_read(sp+0x28,4))[0],struct.unpack('<I',m.mem_read(sp+0x30,4))[0]]))
        elif a==0x14007bc80:events.append(dict(kind='music',file=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),128)).split(b'\0')[0].decode()))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400020b0,0x14003f1eb,0x14003f771,0x14003f591,0x1402bdee2,0x140007530,0x14007bc80]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    offsets=[0x3428,0x3548,0x36b8,0x37d8,0x3910,0x3a30,0x3b60,0xa80,0x28e0]
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
        initial=bytearray.fromhex(s['initial']);normalize(initial,True);struct.pack_into('<Q',initial,0x38f8,programBase);struct.pack_into('<Q',initial,0x3b58,table);m.mem_write(n.owner,bytes(initial));m.mem_write(0x1404f1e84,struct.pack('<i',s['file']));m.mem_write(0x1403ec2a8,bytes(640*0x620));m.mem_write(0x1404e12b8,bytes(64*0x298));m.reg_write(UC_X86_REG_EDX,s['id']);run(0x14003ece0);previousInput=0;byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,s['endFrame']+1):
            current=8 if s['mode']=='skip'else 1 if s['mode']=='advance'and frame%16==0 else 0;m.mem_write(0x140a6ec60,struct.pack('<2I',current,previousInput));previousInput=current;events.clear();run(0x14003eee0)
            if frame not in byFrame:continue
            c=byFrame[frame];result=m.reg_read(UC_X86_REG_EAX);assert result==c['result']&0xffffffff,(index,frame,'result',result,c['result']);assert events==c['events'],(index,frame,'events',events,c['events']);actual=bytearray(m.mem_read(n.owner,0x4000));normalize(actual);struct.pack_into('<Q',actual,0x38f8,1);struct.pack_into('<Q',actual,0x3b58,1);struct.pack_into('<Q',actual,0x3668,struct.unpack_from('<Q',actual,0x3668)[0]-programBase);wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,s['file'],s['character'],s['mode'],frame,[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);digest.update(actual);checked+=1
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,scenes=len(scenes),frames=sum(s['endFrame']for s in scenes),checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-message-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
