"""Boss registration/unregistration and manager health gauge arithmetic.

Original x64 blocks execute against complete enemy state and reserved slot table.
This does not validate boss attack/death, UI rendering or complete gameplay.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    script="""
import{createBossState,setBossRegistration,updateBossGauge}from'./shared/th06nc/boss-state.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(const flags of [0,8,31,255])for(const index of [-3,-1,0,1,2,3,4,5,6,7]){
 const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),bossSlots=Array(8).fill(null),bossState={...createBossState(),lifeFraction:0.25,segmentFraction:0.75,active:true},environment={};v.setUint8(0xbd,flags);v.setUint8(0x230,3);bossSlots[3]={enemy,v};const before=hex(enemy);setBossRegistration(enemy,index,{bossSlots,bossState,environment});cases.push({kind:'registration',before,after:hex(enemy),index,bossState,slots:bossSlots.map(e=>Boolean(e))});
}
for(const life of [-5,0,5,100,2147483647])for(const maximum of [-1,0,10,2147483647])for(const phaseMaximum of [-1,0,10])for(const threshold of [-1,0,5])for(const boss of [false,true])for(const dialog of [-1,0]){
 const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),bossState={...createBossState(),lifeFraction:0.25,segmentFraction:0.75};v.setUint8(0xbd,boss?8:0);for(const [p,x]of [[0x234,life],[0x238,maximum],[0x23c,phaseMaximum],[0xa0,threshold]])v.setInt32(p,x,true);const before=hex(enemy);updateBossGauge({v},{bossState,environment:{messageField36b0:dialog}});cases.push({kind:'gauge',before,after:hex(enemy),dialog,bossState});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;owner=0x140aa1e90;digest=hashlib.sha256()
    m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner))
    for index,c in enumerate(cases):
        m.mem_write(n.vm,bytes.fromhex(c['before']));m.mem_write(0x140a6ebd4,struct.pack('<f',0.25));m.mem_write(0x140a6ebdc,struct.pack('<f',0.75));m.mem_write(0x140a6ebec,b'\0');m.mem_write(0x140a6ec14,b'\1')
        m.reg_write(UC_X86_REG_RSP,n.stack+0x8000)
        if c['kind']=='registration':
            m.mem_write(owner+0x10c0e8,bytes(64));m.mem_write(owner+0x10c0e8+3*8,struct.pack('<Q',n.vm));m.mem_write(n.assets,struct.pack('<i',c['index']));m.reg_write(UC_X86_REG_RDI,n.vm);m.reg_write(UC_X86_REG_RSI,n.assets);m.reg_write(UC_X86_REG_R12,0);m.emu_start(0x1400271d3,0x140025d7d,count=1000)
            slots=[struct.unpack('<Q',m.mem_read(owner+0x10c0e8+i*8,8))[0]for i in range(8)];assert slots==[n.vm if active else 0 for active in c['slots']],(index,'slots');assert bool(m.mem_read(0x140a6ec14,1)[0])==c['bossState']['active'],(index,'active');assert bool(m.mem_read(0x140a6ebec,1)[0])==c['bossState']['dirty'],(index,'dirty')
        else:
            m.mem_write(n.owner+0x36b0,struct.pack('<i',c['dialog']));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_XMM10,0);m.reg_write(UC_X86_REG_XMM14,int.from_bytes(struct.pack('<f',1),'little'));m.emu_start(0x140037fd0,0x140038077,count=1000)
        actual=bytes(m.mem_read(n.vm,0x10b0));assert actual.hex()==c['after'],(index,'enemy')
        for address,key in [(0x140a6ebd4,'lifeFraction'),(0x140a6ebdc,'segmentFraction')]:assert bytes(m.mem_read(address,4))==struct.pack('<f',c['bossState'][key]),(index,key,struct.unpack('<f',m.mem_read(address,4))[0],c['bossState'][key])
        digest.update(actual+bytes(m.mem_read(0x140a6ebd4,4))+bytes(m.mem_read(0x140a6ebdc,4)))
    report=dict(scope=__doc__,cases=len(cases),registrationCases=sum(c['kind']=='registration'for c in cases),gaugeCases=sum(c['kind']=='gauge'for c in cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/boss-state.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-boss-state-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
