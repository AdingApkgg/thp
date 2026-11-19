"""Player life states 68ad2..69035: death-bomb window, death, respawn, immunity.

Main ANM reset publication and item creation are observed boundaries; native
state logic and inline projectile cancellation execute. Full player bytes and
related globals compared, excluding input, bombs, shots and visual pixels.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-life.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{createHash}from'node:crypto';import{advancePlayerLife}from'./shared/th06nc/player-life.mjs';const cases=[];
for(const playerState of [0,1,2,3])for(const deathBomb of [0,1,8])for(const clock of [0,1,7,8,16,29,30,31,239,240])for(const protectedLife of [false,true])for(const lives of [0,3])for(const difficulty of [0,4])for(const practice of [false,true]){
 const state=new Uint8Array(0xa300),v=new DataView(state.buffer);v.setUint8(0x7898,playerState);v.setInt32(0x773c,deathBomb,true);v.setInt32(0x7854,17,true);v.setInt32(0x7858,clock,true);v.setInt32(0xa298,2,true);v.setUint32(0x798c,0x18,true);[100,200,0.5].forEach((x,k)=>v.setFloat32(0x7730+k*4,x,true));
 const environment={deathCount:4,powerItemChain:1,lives,playerPower:32,lifeProtection:protectedLife,inputFlags:255,continueState:7,gameOverRequested:false,difficulty,practice,defaultBombs:4,bombs:2},events=[];advancePlayerLife(state,{environment,resetMainAnimation:script=>events.push({kind:'animation',script}),dropItem:item=>events.push({kind:'item',...item}),cancelProjectiles:()=>events.push({kind:'cancel'})});cases.push({playerState,deathBomb,clock,protectedLife,lives,difficulty,practice,environment,events,sha256:createHash('sha256').update(state).digest('hex')});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x140068c03:events.append(dict(kind='cancel'));return
        if a==0x140068e07:events.append(dict(kind='animation',script=0x420));m.reg_write(UC_X86_REG_RIP,0x140068e66);return
        events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),critical=bool(m.reg_read(UC_X86_REG_R9D))));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140068c03,0x140068e07,0x1400426e0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        state=bytearray(0xa300);state[0x7898]=c['playerState'];struct.pack_into('<i',state,0x773c,c['deathBomb']);struct.pack_into('<2i',state,0x7854,17,c['clock']);struct.pack_into('<i',state,0xa298,2);struct.pack_into('<I',state,0x798c,0x18);struct.pack_into('<3f',state,0x7730,100,200,0.5);m.mem_write(n.owner,bytes(state))
        m.mem_write(0x1404f1e60,struct.pack('<i',4));m.mem_write(0x1404ff0dd,b'\1');m.mem_write(0x1404ff0f0,bytes([c['lives'],2,7]));m.mem_write(0x1404f1e88,struct.pack('<H',32));m.mem_write(0x1404f27c4,bytes([c['protectedLife']]));m.mem_write(0x140a6ec18,struct.pack('<I',255));m.mem_write(0x1404f27b1,b'\0');m.mem_write(0x1404f27b4,bytes([c['practice']]));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.mem_write(0x140c21de1,b'\4')
        m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_ESI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140068ad2,0x140069035,count=100000);actual=bytes(m.mem_read(n.owner,0xa300));assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'player',c);assert events==c['events'],(index,'events',events,c['events'])
        env=dict(deathCount=struct.unpack('<i',m.mem_read(0x1404f1e60,4))[0],powerItemChain=m.mem_read(0x1404ff0dd,1)[0],lives=m.mem_read(0x1404ff0f0,1)[0],playerPower=struct.unpack('<H',m.mem_read(0x1404f1e88,2))[0],lifeProtection=c['protectedLife'],inputFlags=struct.unpack('<I',m.mem_read(0x140a6ec18,4))[0],continueState=struct.unpack('<b',m.mem_read(0x1404ff0f2,1))[0],gameOverRequested=bool(m.mem_read(0x1404f27b1,1)[0]),difficulty=c['difficulty'],practice=c['practice'],defaultBombs=4,bombs=m.mem_read(0x1404ff0f1,1)[0]);assert env==c['environment'],(index,'environment',env,c['environment']);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-life-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
