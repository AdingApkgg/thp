"""Native queue insertion 76af0, BGM fade 79c84..79d26 and .pos conversion.

Checks global state and ordered transport requests; excludes PCM mixing.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/sound-queue.mjs','shared/th06nc/music-update.mjs','shared/th06nc/music-loop.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{queueSound}from'./shared/th06nc/sound-queue.mjs';import{advanceMusicFade}from'./shared/th06nc/music-update.mjs';import{readMusicLoop}from'./shared/th06nc/music-loop.mjs';const queues=[],fades=[],loops=[];
for(let id=0;id<34;id++)for(const disabled of [false,true])for(const initial of [[-1,id,-1],[id,-1,7],[7,id,10],[7,10,-1],[7,-1,id],[7,10,11]]){const slots=[...initial];queueSound(slots,id,{disabled});queues.push({id,disabled,initial,slots});}
for(const handle of [-1,17])for(const fading of [false,true])for(const playing of [false,true])for(const requestActive of [false,true])for(const fadeStart of [-2,0,1,2,119,240,0x40000001])for(const fadeFrame of [120,240,-240])for(const volume of [0,1,5,10,255]){const initial={handle,fading,playing,requestActive,fadeStart,fadeFrame,pendingValue:99},state={...initial},events=[];advanceMusicFade(state,{volume,setVolume:r=>events.push({kind:'volume',...r}),muteMusic:r=>events.push({kind:'mute',...r}),stopMusic:r=>events.push({kind:'stop',...r}),releaseMusic:r=>events.push({kind:'release',...r})});fades.push({initial,state,volume,events});}
for(const a of [-2147483648,-485100,-442,-441,-440,-1,0,1,440,441,442,485100,2147483647])for(const b of [0,5192292,2147483647]){const raw=new Uint8Array(8),v=new DataView(raw.buffer);v.setInt32(0,a,true);v.setInt32(4,b,true);loops.push({a,b,...readMusicLoop(raw)});}console.log(JSON.stringify({queues,fades,loops}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[]
    fields={'handle':(0x50966c,'i'),'playing':(0x50967c,'B'),'fading':(0x509668,'B'),'fadeStart':(0x509660,'i'),'fadeFrame':(0x509664,'i'),'pendingValue':(0x509690,'i'),'requestActive':(0xc21c0c,'B')}
    def hook(m,a,size,u):
        ecx=m.reg_read(UC_X86_REG_ECX);edx=m.reg_read(UC_X86_REG_EDX)
        if a==0x1400ca7d0:events.append(dict(kind='volume',handle=edx,value=ecx if ecx<0x80000000 else ecx-0x100000000))
        elif a==0x1400c2440:events.append(dict(kind='mute',handle=edx,value=ecx))
        elif a==0x1400cce50:events.append(dict(kind='stop',handle=ecx,mode=edx))
        else:events.append(dict(kind='release',handle=ecx))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400ca7d0,0x1400c2440,0x1400cce50,0x14007f9c0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for c in data['queues']:
        m.mem_write(0x140509670,struct.pack('<3i',*c['initial']));m.mem_write(0x140509694,bytes([c['disabled']]));m.reg_write(UC_X86_REG_EDX,c['id']);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x140076af0,n.assets,count=1000);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['slots'],c
    for i,c in enumerate(data['fades']):
        for key,(off,fmt)in fields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(c['initial'][key])))
        m.mem_write(0x140c21db6,bytes([c['volume']]));m.reg_write(UC_X86_REG_RBX,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140079c84,0x140079d26,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x140079d26
        for key,(off,fmt)in fields.items():assert struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0]==int(c['state'][key]),(i,key,c)
        assert events==c['events'],(i,events,c)
    for c in data['loops']:
        m.mem_write(n.vm,struct.pack('<2i',c['a'],c['b']));m.reg_write(UC_X86_REG_RAX,n.vm);m.reg_write(UC_X86_REG_RBP,n.vm);m.emu_start(0x14007be52,0x14007bea4,count=1000)
        def signed(value):return value if value<1<<63 else value-(1<<64)
        assert (signed(m.reg_read(UC_X86_REG_RBX)),signed(m.reg_read(UC_X86_REG_RDI)))==(c['start'],c['end']),c
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes
    report=dict(scope=__doc__,queueCases=len(data['queues']),fadeCases=len(data['fades']),loopCases=len(data['loops']),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-audio-control-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()

