"""Actual 2caa6..2ceaa ending initialization and full 2b7a0 script replacement.

Complete 1280-byte owner (normalized script pointers), return value and ordered
load/free/achievement/error requests compare. File loader, achievement interface
and error logger are controlled services. Resource/CLRD prefix, script execution,
Staff drawing, scene lifecycle and browser excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/ending-init.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{initializeEndingScript,replaceEndingScript}from'./shared/th06nc/ending-init.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const character of [0,1,2])for(const shot of [0,1])for(const difficulty of [0,1,2,3,4])for(const restricted of [false,true])for(const lifeProtection of [false,true])for(const deathCount of [0,1])for(const previous of [0n,2n])for(const failure of [false,true]){const bytes=Uint8Array.from({length:0x1280},(_,j)=>(j*17+cases.length)&255),v=new DataView(bytes.buffer);v.setBigUint64(8,previous,true);v.setBigUint64(0x1250,3n,true);const before=hex(bytes),events=[],e={character,shot,difficulty,lifeProtection,deathCount},result=initializeEndingScript(bytes,e,{restricted,loadScript:file=>{events.push({kind:'load',file});return failure?0n:1n;},freeScript:pointer=>events.push({kind:'free',pointer:String(pointer)}),awardAchievement:key=>events.push({kind:'award',key}),commitAchievements:()=>events.push({kind:'commit'}),reportError:key=>events.push({kind:'error',key})});cases.push({e,restricted,failure,before,after:hex(bytes),events,result});}for(const c of cases.slice(0,64)){const bytes=Uint8Array.from(Buffer.from(c.before,'hex')),events=[],result=replaceEndingScript(bytes,'data/staff00.end',{loadScript:file=>{events.push({kind:'load',file});return c.failure?0n:1n;},freeScript:pointer=>events.push({kind:'free',pointer:String(pointer)}),reportError:key=>events.push({kind:'error',key})});cases.push({...c,replace:true,after:hex(bytes),events,result});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();newptr=n.assets+0x100000;oldptr=n.vm+0x1000;untouched=n.vm+0x2000;holder=n.vm+0xa000;interface=holder+0x10;vtable=holder+0x100;award=holder+0x200;commit=award+0x10;getapi=award+0x20;free=award+0x30
    m.mem_write(holder,struct.pack('<Q',interface));m.mem_write(interface,struct.pack('<Q',vtable));m.mem_write(vtable+0x30,struct.pack('<Q',award));m.mem_write(vtable+0x48,struct.pack('<Q',commit));m.mem_write(0x1402c0630,struct.pack('<Q',getapi));m.mem_write(0x1402c0378,struct.pack('<Q',free));failure=False
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1400387a0:events.append(dict(kind='load',file=bytes(m.mem_read(m.reg_read(UC_X86_REG_RCX),64)).split(b'\0')[0].decode()));m.reg_write(UC_X86_REG_RAX,0 if failure else newptr)
        elif a==getapi:m.reg_write(UC_X86_REG_RAX,holder)
        elif a==free:assert m.reg_read(UC_X86_REG_RCX)==oldptr;events.append(dict(kind='free',pointer='2'))
        elif a==award:events.append(dict(kind='award',key=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),64)).split(b'\0')[0].decode()));m.reg_write(UC_X86_REG_EAX,1)
        elif a==commit:events.append(dict(kind='commit'));m.reg_write(UC_X86_REG_EAX,1)
        elif a==0x140039ef0:events.append(dict(kind='error',key='endingFileLoadFailed'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1400387a0,getapi,free,award,commit,0x140039ef0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(cases):
        initial=bytearray.fromhex(c['before']);previous=struct.unpack_from('<Q',initial,8)[0];struct.pack_into('<Q',initial,8,oldptr if previous else 0);struct.pack_into('<Q',initial,0x1250,untouched);m.mem_write(n.owner,bytes(initial));e=c['e'];m.mem_write(0x1404f1e80,bytes([e['character'],e['shot']]));m.mem_write(0x1404f27c0,struct.pack('<i',e['difficulty']));m.mem_write(0x1404f27c4,bytes([e['lifeProtection']]));m.mem_write(0x1404f1e60,struct.pack('<i',e['deathCount']));sp=n.stack+0x8000;m.mem_write(sp+(0 if c.get('replace')else 0x28),struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_R9,int(c['restricted']));events.clear();failure=c['failure'];m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RDX,n.assets);m.mem_write(n.assets,b'data/staff00.end\0');m.emu_start(0x14002b7a0 if c.get('replace')else 0x14002caa6,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(i,'stop');actual=bytearray(m.mem_read(n.owner,0x1280))
        for p in [8,0x1250]:
            ptr=struct.unpack_from('<Q',actual,p)[0];assert ptr in [0,newptr,oldptr,untouched];struct.pack_into('<Q',actual,p,{0:0,newptr:1,oldptr:2,untouched:3}[ptr])
        assert actual==bytes.fromhex(c['after']),(i,'owner');assert events==c['events'],(i,'requests',events,c['events']);assert (m.reg_read(UC_X86_REG_EAX)&0xffffffff)==(c['result']&0xffffffff),(i,'return');digest.update(actual);digest.update(json.dumps(events).encode())
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-ending-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
