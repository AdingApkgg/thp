"""Life-threshold and timeout transitions, with ordinary enemies and boss countdown, including other enemy resets and spell-practice completion.

Actual manager phase and timeout helper execute. Bullet pools are empty; the
cancellation entry is observed. Boss UI and live bullet cancellation excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{advanceOrdinaryEnemyPhase}from'./shared/th06nc/enemy-phase.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(const spellPractice of [false,true])for(const boss of [false,true])for(const threshold of [-1,0,10])for(const life of [-2,0,5,10,20])for(const timeout of [-1,5])for(const timer of [0,5,9])for(const suppressCancel of [false,true]){
 const entries=[],index=cases.length,environment={spellPractice,spellFinished:false,spellCounter:index%2?3:0,spellActive:true},bossState={remainingSeconds:123};
 for(let slot=0;slot<5;slot++){
 const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);v.setUint8(0xbc,slot===3?0:128);v.setUint8(0xbd,[boss?9:1,0,8,0,1][slot]);v.setInt32(0x238,456,true);v.setInt32(0xbe0,3,true);v.setBigUint64(0x88,400n,true);v.setInt32(0x40,111,true);v.setInt32(0x44,222,true);v.setInt32(0x240,4,true);v.setInt32(0xa0,threshold,true);v.setInt16(0xa4,2,true);v.setInt32(0x234,life,true);v.setInt32(0xc54,timeout,true);v.setInt32(0xc58,1,true);v.setInt32(0,99,true);v.setInt32(4,timer,true);v.setUint8(0xbe,suppressCancel?16:0);v.setFloat32(0xa8,-2,true);v.setFloat32(0xac,3,true);v.setUint32(0xbdc,0x87654321,true);v.setUint32(0x1080,0x12345678,true);
 entries.push({enemy,v,dispatch:{program:{subroutines:[{offset:512},{offset:528},{offset:544},{offset:560}]},pointer:p=>v.setBigUint64(0x88,BigInt(p),true)}});
 }
 const before=entries.map(e=>hex(e.enemy)),prior={...environment};let cancelled=0;
 advanceOrdinaryEnemyPhase(entries[0],{entries,environment,bossState,cancelBullets:()=>cancelled++});
 cases.push({before,after:entries.map(e=>hex(e.enemy)),prior,environment,bossState,cancelled});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;owner=0x140aa1e90;enemy=owner+8;programBase=n.assets;table=n.vm+0x8000;digest=hashlib.sha256();events=[]
    for i in range(4):m.mem_write(table+i*8,struct.pack('<Q',programBase+512+i*16))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table))
    def hook(m,a,size,u):
        if a==0x140037039:events.append('cancel')
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        m.mem_write(owner,bytes(0x10d1e0))
        for slot,state in enumerate(c['before']):
            raw=bytearray.fromhex(state);struct.pack_into('<Q',raw,0x88,programBase+400);m.mem_write(enemy+slot*0x10b0,bytes(raw))
        m.mem_write(0x1404f27b5,bytes([c['prior']['spellPractice']]));m.mem_write(0x140aa1e8e,b'\0');m.mem_write(0x140a6ec1c,struct.pack('<i',123));m.mem_write(0x140badf60,struct.pack('<i',c['prior']['spellCounter']));m.mem_write(0x140badf6c,bytes([c['prior']['spellActive']]))
        m.reg_write(UC_X86_REG_RBX,enemy);m.reg_write(UC_X86_REG_R14D,0);m.reg_write(UC_X86_REG_EDI,0xffffffff);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140037693,0x1400377a4,count=100000)
        for slot,state in enumerate(c['after']):
            actual=bytearray(m.mem_read(enemy+slot*0x10b0,0x10b0));ptr=struct.unpack_from('<Q',actual,0x88)[0];struct.pack_into('<Q',actual,0x88,ptr-programBase);wanted=bytes.fromhex(state);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,slot,diff,bytes(m.mem_read(enemy,16)).hex(),hex(m.reg_read(UC_X86_REG_R9)),hex(m.reg_read(UC_X86_REG_RCX)));digest.update(actual)
        assert struct.unpack('<i',m.mem_read(0x140a6ec1c,4))[0]==c['bossState']['remainingSeconds'],(index,'countdown');assert len(events)==c['cancelled'],(index,'cancel',events,c['cancelled']);assert struct.unpack('<i',m.mem_read(0x140badf60,4))[0]==c['environment']['spellCounter'],(index,'spell counter');assert bool(m.mem_read(0x140badf6c,1)[0])==c['environment']['spellActive'],(index,'spell active')
        assert bool(m.mem_read(0x140aa1e8e,1)[0])==c['environment']['spellFinished'],(index,'spell finished')
    report=dict(scope=__doc__,cases=len(cases),enemyStateComparisons=len(cases)*5,stateSha256=digest.hexdigest(),sourceSha256={'shared/th06nc/enemy-phase.mjs':hashlib.sha256((ROOT/'shared/th06nc/enemy-phase.mjs').read_bytes()).hexdigest()},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-phase-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
