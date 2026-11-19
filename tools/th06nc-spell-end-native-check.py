"""Spell-end opcode 94: conversion request, bonus, HUD state and capture records.

Actual original dispatch block executes. Bullet conversion is observed, not
simulated; rendered UI, save-file persistence and complete spells are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{createHash}from'node:crypto';import{bindHudPopup}from'./shared/th06nc/hud-notifications.mjs';import{createSpellState,endSpell}from'./shared/th06nc/spell-state.mjs';const cases=[];function makeSpellHud(){const bytes=new Uint8Array(0x4228),hud={bytes,v:new DataView(bytes.buffer)},spellState=createSpellState();bindHudPopup(hud,spellState,'bonusPopup',0x6f8);Object.defineProperty(spellState,'hudCancelPending',{enumerable:true,configurable:true,get:()=>hud.v.getUint16(0x8c2,true),set:value=>hud.v.setUint16(0x8c2,value,true)});return {hud,spellState};}
for(const counter of [-1,0,1,2])for(const active of [false,true])for(const id of [0,120,121,130,133,134,0xffffffff])for(const practice of [false,true])for(const replay of [false,true])for(const remaining of [-3,0,12,2147483647]){
 const index=cases.length,{spellState,hud}=makeSpellHud(),record={captures:[0,9998,9999,65535][index%4],history:[7,6,5,4,3],practiceCaptures:new Uint32Array(20).fill([0,999999998,999999999,0xffffffff][index%4])},initialRecord={...record,history:[...record.history],practiceCaptures:[...record.practiceCaptures]},environment={spellCounter:counter,spellActive:active,spellId:id,spellBonus:index%2?-123:10000,score:18446744073709551610n,spellPractice:practice,replayPlayback:replay,character:1,shot:index%2,difficulty:index%5,spellFinished:false},prior={...environment,score:String(environment.score)},events=[];spellState.captures=123;spellState.extraCaptures=4;spellState.backgroundClock=77;if(id<134)spellState.records.set(id,record);
 endSpell({environment,spellState,bossState:{remainingSeconds:remaining},cancelBullets:request=>events.push(request)});const afterRecord=spellState.records.get(id);cases.push({hudSha256:createHash('sha256').update(hud.bytes).digest('hex'),prior,remaining,initialRecord,environment:{...environment,score:String(environment.score)},events,spellState:{...spellState,records:undefined},afterRecord:afterRecord?{...afterRecord,practiceCaptures:[...afterRecord.practiceCaptures]}:null});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner))
    def hook(m,a,size,u):
        if a!=0x14000f300:return
        events.append(dict(convert=bool(m.reg_read(UC_X86_REG_R8B))));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        env=c['prior'];record=bytearray(0x180);struct.pack_into('<H',record,0x3e,c['initialRecord']['captures']);record[0x13:0x18]=bytes(c['initialRecord']['history']);struct.pack_into('<20I',record,0x130,*c['initialRecord']['practiceCaptures'])
        if env['spellId']<134:m.mem_write(0x1404f27c8+env['spellId']*0x180,bytes(record))
        m.mem_write(n.owner,bytes(0x4228));m.mem_write(0x140badf60,struct.pack('<i',env['spellCounter']));m.mem_write(0x140badf68,struct.pack('<I',env['spellId']));m.mem_write(0x140badf6c,bytes([env['spellActive']]));m.mem_write(0x140badf70,struct.pack('<i',env['spellBonus']));m.mem_write(0x140a6ec1c,struct.pack('<i',c['remaining']));m.mem_write(0x1404f2798,struct.pack('<Q',int(env['score'])));m.mem_write(0x1404f278c,bytes([env['replayPlayback']]));m.mem_write(0x1404f27b5,bytes([env['spellPractice']]));m.mem_write(0x140aa1e8e,b'\0');m.mem_write(0x1404f1e80,bytes([env['character'],env['shot']]));m.mem_write(0x1404f27c0,struct.pack('<i',env['difficulty']));m.mem_write(0x1404f1e68,struct.pack('<2i',123,4));m.mem_write(0x140509c18,struct.pack('<i',77))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_R12,0),(UC_X86_REG_R15,1)]:m.reg_write(reg,value)
        events.clear();m.emu_start(0x140027bcf,0x140025d7d,count=100000);expected=c['spellState'];assert events==c['events'],(index,'events');assert struct.unpack('<i',m.mem_read(0x140badf60,4))[0]==c['environment']['spellCounter'],(index,'counter');assert bool(m.mem_read(0x140aa1e8e,1)[0])==c['environment']['spellFinished'],(index,'finished');assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['environment']['score'],(index,'score')
        assert struct.unpack('<2i',m.mem_read(0x1404f1e68,8))==(expected['captures'],expected['extraCaptures']),(index,'capture counters');assert struct.unpack('<i',m.mem_read(0x140509c18,4))[0]==expected['backgroundClock'],(index,'background');assert struct.unpack('<H',m.mem_read(n.owner+0x8c2,2))[0]==expected['hudCancelPending'],(index,'hud')
        assert hashlib.sha256(bytes(m.mem_read(n.owner,0x4228))).hexdigest()==c['hudSha256'],(index,'aliased HUD owner')
        popup=bytearray(28)
        if expected['bonusPopup']:
            p=expected['bonusPopup'];struct.pack_into('<iiB',popup,0,p['previous'],p['frame'],p['active']);struct.pack_into('<3fi',popup,12,*p['position'],p['value'])
        assert bytes(m.mem_read(n.owner+0x6f8,28))==popup,(index,'bonus popup')
        if c['afterRecord']:
            r=c['afterRecord'];wanted=bytearray(record);struct.pack_into('<H',wanted,0x3e,r['captures']);wanted[0x13:0x18]=bytes(r['history']);struct.pack_into('<20I',wanted,0x130,*r['practiceCaptures']);actual=bytes(m.mem_read(0x1404f27c8+env['spellId']*0x180,0x180));diff=[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,'record',diff);digest.update(actual)
        digest.update(bytes(popup))
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/spell-state.mjs','shared/th06nc/hud-notifications.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-spell-end-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
