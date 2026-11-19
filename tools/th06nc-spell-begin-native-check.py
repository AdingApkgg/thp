"""Spell-start state segment 279a3..27bcf and original base bonus table.

Compares complete enemy/record bytes, sound, background controls and clear request.
Alternates copied records and nonzero-offset shared views. Localization lookup,
font/HUD ANM publication and actual projectile pools excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{beginSpell,createSpellState}from'./shared/th06nc/spell-state.mjs';import{createSpellRecord}from'./shared/th06nc/spell-record.mjs';import{spellBaseBonuses}from'./shared/th06nc/spell-bonus.mjs';const cases=[],keys=['ST_ECLDATA1_SUB9_0','月符',''],hex=b=>Buffer.from(b).toString('hex');
for(const id of [-1,0,19,20,36,37,83,84,99,100,103,104,120,121,130,133,134,32767])for(const practice of [false,true])for(const replay of [false,true])for(const match of [false,true])for(const attempts of [0,9998,9999,65535]){
 const index=cases.length,key=keys[index%3],encoded=new TextEncoder().encode(key),checksum=encoded.reduce((s,x)=>s+x,0)&255,args=new Uint8Array(5+encoded.length),a=new DataView(args.buffer);a.setInt16(0,index%3-1,true);a.setInt16(2,id,true);args.set(encoded,4);
 const bytes=new Uint8Array(0x10b0),v=new DataView(bytes.buffer);for(const p of [0xa8,0xac,0xbdc,0x1080])v.setUint32(p,0x12345678,true);
 const raw=Uint8Array.from({length:0x184},(_,i)=>(i*13)%256),record=createSpellRecord(raw.subarray(4),{copy:Boolean(index&1)});record.key='old';record.checksum=match?checksum:checksum^255;record.attempts=attempts;record.captures=65535;record.practiceAttempts.fill([0,999999998,999999999,0xffffffff][index%4]);
 const recordBefore=hex(record.bytes),before=hex(bytes),environment={spellPractice:practice,replayPlayback:replay,character:1,shot:index%2,difficulty:index%5},spellState=createSpellState(),soundDisabled=index%7===0,soundSlots=index%3?[14,-1,-1]:[-1,-1,-1],soundBefore=[...soundSlots],events=[];if(id>=0&&id<134)spellState.records.set(id,record);
 beginSpell({v},args,{environment,spellState,soundDisabled,soundSlots,cancelBullets:e=>events.push(e)});cases.push({id,args:hex(args),key,recordBefore,before,after:hex(bytes),recordAfter:hex(record.bytes),environment,background:{clock:spellState.backgroundClock,frame:spellState.backgroundFrame,active:spellState.backgroundActive},soundDisabled,soundBefore,soundSlots,events});
}console.log(JSON.stringify({bonuses:spellBaseBonuses,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();assert tuple(data['bonuses'])==struct.unpack('<134i',m.mem_read(0x140308290,536))
    def hook(m,a,size,u):
        if a==0x14000ef00:events.append(dict(items=bool(m.reg_read(UC_X86_REG_DL))))
        elif a==0x1402bdee2:
            dst=m.reg_read(UC_X86_REG_RCX);value=m.reg_read(UC_X86_REG_EDX)&255;length=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([value])*length);m.reg_write(UC_X86_REG_RAX,dst)
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for address in [0x14000ef00,0x1402bdee2]:m.hook_add(UC_HOOK_CODE,hook,begin=address,end=address)
    for index,c in enumerate(data['cases']):
        raw=bytes.fromhex(c['args']);m.mem_write(n.assets,bytes(12)+raw);m.mem_write(n.owner,bytes.fromhex(c['before']));recordAddress=0x1404f27c8+c['id']*0x180 if 0<=c['id']<134 else None
        if recordAddress:m.mem_write(recordAddress,bytes.fromhex(c['recordBefore']))
        env=c['environment'];m.mem_write(0x1404f27b5,bytes([env['spellPractice']]));m.mem_write(0x1404f278c,bytes([env['replayPlayback']]));m.mem_write(0x1404f27c0,struct.pack('<i',env['difficulty']));m.mem_write(0x1404f1e80,bytes([env['character'],env['shot']]));m.mem_write(0x140509694,bytes([c['soundDisabled']]));m.mem_write(0x140509670,struct.pack('<3i',*c['soundBefore']));m.mem_write(0x140509c18,struct.pack('<2i',77,0));m.mem_write(0x140509b60,struct.pack('<i',88));sp=n.stack+0x8000;m.mem_write(sp+0x48,struct.pack('<Q',n.assets))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R14,n.assets),(UC_X86_REG_RBX,n.assets+16),(UC_X86_REG_R12,0)]:m.reg_write(reg,value)
        events.clear();m.emu_start(0x1400279a3,0x140025d7d,count=100000);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],(index,'enemy');assert events==c['events'],(index,'events');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(index,'sound')
        assert struct.unpack('<i',m.mem_read(0x140badf60,4))[0]==env['spellCounter'],(index,'counter');assert bool(m.mem_read(0x140badf6c,1)[0])==env['spellActive'],(index,'active');assert struct.unpack('<i',m.mem_read(0x140badf68,4))[0]==env['spellId'],(index,'id');assert struct.unpack('<i',m.mem_read(0x140badf70,4))[0]==env['spellBonus'],(index,'bonus')
        assert struct.unpack('<i',m.mem_read(0x140509c18,4))[0]==c['background']['clock'],(index,'background clock');assert bool(m.mem_read(0x140509c1c,1)[0])==c['background']['active'],(index,'background active');assert struct.unpack('<i',m.mem_read(0x140509b60,4))[0]==c['background']['frame'],(index,'background frame');digest.update(actual)
        if recordAddress:
            actual=bytes(m.mem_read(recordAddress,0x180));wanted=bytes.fromhex(c['recordAfter']);diff=[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,'record',diff);digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),baseBonuses=len(data['bonuses']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/spell-state.mjs','shared/th06nc/spell-record.mjs','shared/th06nc/spell-bonus.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-spell-begin-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
