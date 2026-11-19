"""Boss enemy death phase 37b86..37fd0, effects/items observed as services.

Full enemy state, event order, score, item cycle counters and sound queue are
compared. Boss projectile conversion is included; actual effect/item/score-label entities are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{createHash}from'node:crypto';import{bindHudPopup}from'./shared/th06nc/hud-notifications.mjs';import{cancelBossProjectiles}from'./shared/th06nc/projectile-cancel.mjs';import{createBossState}from'./shared/th06nc/boss-state.mjs';import{finishOrdinaryEnemyDeath}from'./shared/th06nc/enemy-death.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(let kind=0;kind<8;kind++)for(const life of [-5,0,1])for(const enabled of [false,true])for(const item of [-128,-2,-1,0,7,127])for(const sub of [-1,0,3])for(const critical of [false,true]){
const index=cases.length,enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),events=[],soundSlots=[[-1,-1,-1],[2,-1,-1],[4,5,6],[4,3,-1]][index%4].slice(),soundDisabled=index%7===0,bossState={...createBossState(),active:true},environment={spellCounter:index%3,spellPractice:index%2===0,spellFinished:false,score:18446744073709551610n,enemyDeathCount:[0,1,2,65535][index%4],itemDropIndex:index%32};
const hudBytes=new Uint8Array(0x4228),hud={bytes:hudBytes,v:new DataView(hudBytes.buffer)};bindHudPopup(hud,bossState,'bonusPopup',0x6c0);
v.setUint8(0xbc,0xc2);v.setUint8(0xbd,(kind<<5)|0x1e|(enabled?1:0));v.setInt32(0x234,life,true);v.setInt32(0xc50,index%2?-100:300,true);v.setInt32(0xa0,77,true);v.setInt32(0xc54,888,true);v.setUint8(0x38,7);v.setUint8(0x39,8);v.setInt8(0x10a8,item);v.setInt32(0xbe0,sub,true);v.setFloat32(0xb0,100.5,true);v.setFloat32(0xb4,200.25,true);v.setFloat32(0xb8,-2,true);v.setInt32(0x240,5,true);v.setInt32(0x40,123,true);v.setInt32(0x44,456,true);v.setUint32(0xbdc,0x87654321,true);v.setUint32(0x1080,0x12345678,true);v.setFloat32(0xa8,-2,true);v.setFloat32(0xac,3,true);v.setBigUint64(0x88,400n,true);
const before=hex(enemy),prior={...environment,score:String(environment.score)},soundsBefore=[...soundSlots],dispatch={program:{subroutines:[{offset:512},{offset:528},{offset:544},{offset:560}]},services:{soundSlots,soundDisabled},pointer:p=>v.setBigUint64(0x88,BigInt(p),true)},slot=index%2;
const bullets=new Uint8Array(640*0x620),lasers=new Uint8Array(64*0x298),b=new DataView(bullets.buffer),l=new DataView(lasers.buffer);for(let i=0;i<3;i++){b.setUint16(i*0x620+0x44,1,true);[i+0.5,i*2+0.25,-i].forEach((x,k)=>b.setFloat32(i*0x620+0x30+k*4,x,true));}l.setUint8(0x274,1);l.setUint8(0x290,0);l.setInt32(8,-17,true);l.setInt32(0xc,42,true);
finishOrdinaryEnemyDeath({enemy,v,dispatch,slot},{environment,bossState,cancelBossProjectiles:()=>cancelBossProjectiles({bullets,lasers,publishScore:e=>events.push({kind:'points',...e})}),critical,spawnEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e})});
cases.push({hudSha256:createHash('sha256').update(hud.bytes).digest('hex'),before,after:hex(enemy),prior,environment:{...environment,score:String(environment.score)},soundsBefore,soundSlots,soundDisabled,slot,critical,events,bossState,bulletSha256:createHash('sha256').update(bullets).digest('hex'),laserSha256:createHash('sha256').update(lasers).digest('hex')});}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;enemy=n.owner;owner=n.manager;programBase=n.assets;table=n.vm+0x8000;events=[];digest=hashlib.sha256()
    for i in range(4):m.mem_write(table+i*8,struct.pack('<Q',programBase+512+i*16))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table));m.mem_write(0x140a6ec08,struct.pack('<Q',n.vm))
    def hook(m,a,size,u):
        if a not in [0x14002b0d0,0x1400426e0,0x140009bd0]:return
        position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
        if a==0x14002b0d0:
            color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]
            events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=color))
        elif a==0x140009bd0:events.append(dict(kind='points',position=position,value=m.reg_read(UC_X86_REG_R8D),color=m.reg_read(UC_X86_REG_R9D)))
        else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))))
        m.reg_write(UC_X86_REG_RAX,0);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        bullets=bytearray(640*0x620);lasers=bytearray(64*0x298)
        for i in range(3):struct.pack_into('<H',bullets,i*0x620+0x44,1);struct.pack_into('<3f',bullets,i*0x620+0x30,i+0.5,i*2+0.25,-float(i))
        lasers[0x274]=1;struct.pack_into('<2i',lasers,8,-17,42);m.mem_write(0x1403ec2a8,bytes(bullets));m.mem_write(0x1404e12b8,bytes(lasers));m.mem_write(0x140badf60,struct.pack('<i',c['prior']['spellCounter']));m.mem_write(0x1404f27b5,bytes([c['prior']['spellPractice']]));m.mem_write(0x140aa1e8e,b'\0');m.mem_write(0x140a6ec14,b'\1');m.mem_write(n.vm,bytes(0x4228));m.mem_write(n.stack+0x8140,struct.pack('<Q',owner));m.mem_write(n.stack+0x8150,struct.pack('<i',c['slot']))
        before=bytearray.fromhex(c['before']);struct.pack_into('<Q',before,0x88,programBase+400);m.mem_write(enemy,bytes(before));m.mem_write(owner+4,struct.pack('<HH',c['prior']['enemyDeathCount'],c['prior']['itemDropIndex']));m.mem_write(0x1404f2798,struct.pack('<Q',int(c['prior']['score'])));m.mem_write(0x140509670,struct.pack('<3i',*c['soundsBefore']));m.mem_write(0x140509694,bytes([c['soundDisabled']]))
        m.reg_write(UC_X86_REG_RBX,enemy);m.reg_write(UC_X86_REG_R12,owner);m.reg_write(UC_X86_REG_R13D,c['slot']);m.reg_write(UC_X86_REG_R14D,0);m.reg_write(UC_X86_REG_EDI,int(c['critical']));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140037b86,0x140037fd0,count=10000)
        actual=bytearray(m.mem_read(enemy,0x10b0));ptr=struct.unpack_from('<Q',actual,0x88)[0];struct.pack_into('<Q',actual,0x88,ptr-programBase);wanted=bytes.fromhex(c['after']);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,diff)
        assert events==c['events'],(index,events,c['events']);assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['environment']['score'],(index,'score');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(index,'sound')
        assert struct.unpack('<HH',m.mem_read(owner+4,4))==(c['environment']['enemyDeathCount'],c['environment']['itemDropIndex']),(index,'cycle');digest.update(actual)
        assert bool(m.mem_read(0x140a6ec14,1)[0])==c['bossState']['active'],(index,'boss active');assert bool(m.mem_read(0x140aa1e8e,1)[0])==c['environment']['spellFinished'],(index,'spell finished')
        assert hashlib.sha256(bytes(m.mem_read(n.vm,0x4228))).hexdigest()==c['hudSha256'],(index,'aliased HUD owner')
        popup=bytearray(28)
        if c['bossState'].get('bonusPopup'):
            p=c['bossState']['bonusPopup'];struct.pack_into('<iiB',popup,0,p['previous'],p['frame'],p['active']);struct.pack_into('<3fi',popup,12,*p['position'],p['value'])
        assert bytes(m.mem_read(n.vm+0x6c0,28))==popup,(index,'popup');assert hashlib.sha256(m.mem_read(0x1403ec2a8,len(bullets))).hexdigest()==c['bulletSha256'],(index,'bullets');assert hashlib.sha256(m.mem_read(0x1404e12b8,len(lasers))).hexdigest()==c['laserSha256'],(index,'lasers')
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/enemy-death.mjs','shared/th06nc/projectile-cancel.mjs','shared/th06nc/hud-notifications.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-boss-death-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
