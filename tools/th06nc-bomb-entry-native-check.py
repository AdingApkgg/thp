"""Bomb input branch 68820..68ad2, complete owner bytes and global writes.

Bomb callbacks and Steam Achievement20/commit are observed service boundaries.
This check isolates entry/eligibility from the four separate bomb programs.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-bomb.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{advancePlayerBomb}from'./shared/th06nc/player-bomb.mjs';const cases=[];
for(const state of [0,2])for(const replayPlayback of [false,true])for(const active of [false,true])for(const callback of [0,0x14000d1a0,0x14000e7f0])for(const messageField of [-1,0])for(const death of [0,8,-1])for(const bombs of [-128,0,1,3,127])for(const [input,previousInput]of [[0,0],[2,0],[2,2],[0,2]]){
 if(active&&!callback)continue;const index=cases.length,spellCounter=index%3,finish=Boolean(index&4),bombCount=index%5===0?2147483647:13,bytes=Uint8Array.from({length:0xa2b8},(_,i)=>(i*3+7)&255),v=new DataView(bytes.buffer),environment={bombs:bombs&255,bombCount,inputFlags:255,replayPlayback,spellCounter,spellActive:true,spellBombFlag:true},initialEnvironment={...environment},player={bytes,v,environment},events=[];
 v.setUint8(0x9ec8,Number(active));v.setBigUint64(0x9ed0,BigInt(callback),true);v.setUint8(0x7898,state);v.setInt32(0x773c,death,true);v.setInt32(0x7ac0,77,true);v.setInt32(0x7ac4,88,true);v.setInt32(0x9f20,222,true);for(let i=0;i<32;i++)v.setInt32(0x180+i*12,0,true);for(let i=0;i<16;i++)v.setInt32(0x7754+i*16,0,true);
 advancePlayerBomb(player,input,{previousInput,messageField,awardAchievement:key=>events.push({kind:'achievement',key}),commitAchievements:()=>events.push({kind:'commit'}),updateBomb:p=>{events.push({kind:'callback',active:p.v.getUint8(0x9ec8),clock:p.v.getInt32(0x7ac4,true),previous:p.v.getInt32(0x7ac0,true),limit:p.v.getInt32(0x9f20,true),bombs:environment.bombs,bombCount:environment.bombCount,inputFlags:environment.inputFlags});p.v.setInt32(0x7ac4,p.v.getInt32(0x7ac4,true)+11,true);if(finish)p.v.setUint8(0x9ec8,0);}});
 cases.push({active,callback,messageField,death,input,previousInput,state,finish,initialEnvironment,environment,events,sha256:createHash('sha256').update(bytes).digest('hex')});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];current={};digest=hashlib.sha256()
    fields={'bombs':(0x4ff0f1,'B'),'bombCount':(0x4f1e64,'i'),'inputFlags':(0xa6ec18,'I'),'replayPlayback':(0x4f278c,'B'),'spellCounter':(0xbadf60,'i'),'spellActive':(0xbadf6c,'B'),'spellBombFlag':(0xbadf64,'B')}
    def value(key):
        off,fmt=fields[key];return struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0]
    def hook(m,a,size,u):
        if a==0x140068a30:
            events.extend([dict(kind='achievement',key='Achievement20'),dict(kind='commit')]);m.reg_write(UC_X86_REG_ECX,value('bombs'));m.reg_write(UC_X86_REG_RIP,0x140068a6a);return
        ptr=m.reg_read(UC_X86_REG_RCX);active=m.mem_read(ptr+0x9ec8,1)[0];clock=struct.unpack('<i',m.mem_read(ptr+0x7ac4,4))[0];previous=struct.unpack('<i',m.mem_read(ptr+0x7ac0,4))[0];limit=struct.unpack('<i',m.mem_read(ptr+0x9f20,4))[0];events.append(dict(kind='callback',active=active,clock=clock,previous=previous,limit=limit,bombs=value('bombs'),bombCount=value('bombCount'),inputFlags=value('inputFlags')));m.mem_write(ptr+0x7ac4,struct.pack('<i',clock+11))
        if current['finish']:m.mem_write(ptr+0x9ec8,b'\0')
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140068a30,0x14000d1a0,0x14000e7f0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    initial=bytes((i*3+7)&255 for i in range(0xa2b8));m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm))
    for i,c in enumerate(cases):
        current=c;raw=bytearray(initial);raw[0x9ec8]=int(c['active']);struct.pack_into('<Q',raw,0x9ed0,c['callback']);raw[0x7898]=c['state'];struct.pack_into('<i',raw,0x773c,c['death']);struct.pack_into('<2i',raw,0x7ac0,77,88);struct.pack_into('<i',raw,0x9f20,222);m.mem_write(n.owner,bytes(raw));m.mem_write(n.vm+0x36b0,struct.pack('<i',c['messageField']));m.mem_write(0x140a6ec60,struct.pack('<2I',c['input'],c['previousInput']))
        for key,(off,fmt)in fields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(c['initialEnvironment'][key])))
        sp=n.stack+0x8000;m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);events.clear();m.emu_start(0x140068820,0x140068ad2,count=10000);assert m.reg_read(UC_X86_REG_RIP)==0x140068ad2;actual=bytes(m.mem_read(n.owner,0xa2b8));assert hashlib.sha256(actual).hexdigest()==c['sha256'],(i,'owner');assert events==c['events'],(i,events,c['events'])
        for key in fields:assert value(key)==int(c['environment'][key]),(i,key,value(key),c['environment'][key])
        digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-bomb-entry-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
