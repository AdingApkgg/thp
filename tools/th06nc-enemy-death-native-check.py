"""Ordinary enemy death phase 37b86..37fd0, effects/items observed as services.

Full enemy state, event order, score, item cycle counters and sound queue are
compared. Boss death and actual effect/item entities are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{finishOrdinaryEnemyDeath}from'./shared/th06nc/enemy-death.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(let kind=0;kind<8;kind++)for(const life of [-5,0,1])for(const enabled of [false,true])for(const item of [-128,-2,-1,0,7,127])for(const sub of [-1,0,3])for(const critical of [false,true]){
const index=cases.length,enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),events=[],soundSlots=[[-1,-1,-1],[2,-1,-1],[4,5,6],[4,3,-1]][index%4].slice(),soundDisabled=index%7===0,environment={score:18446744073709551610n,enemyDeathCount:[0,1,2,65535][index%4],itemDropIndex:index%32};
v.setUint8(0xbc,0xc2);v.setUint8(0xbd,(kind<<5)|0x16|(enabled?1:0));v.setInt32(0x234,life,true);v.setInt32(0xc50,index%2?-100:300,true);v.setInt32(0xa0,77,true);v.setInt32(0xc54,888,true);v.setUint8(0x38,7);v.setUint8(0x39,8);v.setInt8(0x10a8,item);v.setInt32(0xbe0,sub,true);v.setFloat32(0xb0,100.5,true);v.setFloat32(0xb4,200.25,true);v.setFloat32(0xb8,-2,true);v.setInt32(0x240,5,true);v.setInt32(0x40,123,true);v.setInt32(0x44,456,true);v.setUint32(0xbdc,0x87654321,true);v.setUint32(0x1080,0x12345678,true);v.setFloat32(0xa8,-2,true);v.setFloat32(0xac,3,true);v.setBigUint64(0x88,400n,true);
const before=hex(enemy),prior={...environment,score:String(environment.score)},soundsBefore=[...soundSlots],dispatch={program:{subroutines:[{offset:512},{offset:528},{offset:544},{offset:560}]},services:{soundSlots,soundDisabled},pointer:p=>v.setBigUint64(0x88,BigInt(p),true)},slot=index%2;
finishOrdinaryEnemyDeath({enemy,v,dispatch,slot},{environment,critical,spawnEffect:e=>events.push({kind:'effect',...e}),dropItem:e=>events.push({kind:'item',...e})});
cases.push({before,after:hex(enemy),prior,environment:{...environment,score:String(environment.score)},soundsBefore,soundSlots,soundDisabled,slot,critical,events});}
console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;enemy=n.owner;owner=n.manager;programBase=n.assets;table=n.vm+0x8000;events=[];digest=hashlib.sha256()
    for i in range(4):m.mem_write(table+i*8,struct.pack('<Q',programBase+512+i*16))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table))
    def hook(m,a,size,u):
        if a not in [0x14002b0d0,0x1400426e0]:return
        position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8 if a==0x14002b0d0 else UC_X86_REG_RDX),12)))
        if a==0x14002b0d0:
            color=struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_RSP)+0x28,4))[0]
            events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=position,count=m.reg_read(UC_X86_REG_R9D),color=color))
        else:events.append(dict(kind='item',type=m.reg_read(UC_X86_REG_R8D),position=position,critical=bool(m.reg_read(UC_X86_REG_R9D))))
        m.reg_write(UC_X86_REG_RAX,0);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        before=bytearray.fromhex(c['before']);struct.pack_into('<Q',before,0x88,programBase+400);m.mem_write(enemy,bytes(before));m.mem_write(owner+4,struct.pack('<HH',c['prior']['enemyDeathCount'],c['prior']['itemDropIndex']));m.mem_write(0x1404f2798,struct.pack('<Q',int(c['prior']['score'])));m.mem_write(0x140509670,struct.pack('<3i',*c['soundsBefore']));m.mem_write(0x140509694,bytes([c['soundDisabled']]))
        m.reg_write(UC_X86_REG_RBX,enemy);m.reg_write(UC_X86_REG_R12,owner);m.reg_write(UC_X86_REG_R13D,c['slot']);m.reg_write(UC_X86_REG_R14D,0);m.reg_write(UC_X86_REG_EDI,int(c['critical']));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);events.clear();m.emu_start(0x140037b86,0x140037fd0,count=10000)
        actual=bytearray(m.mem_read(enemy,0x10b0));ptr=struct.unpack_from('<Q',actual,0x88)[0];struct.pack_into('<Q',actual,0x88,ptr-programBase);wanted=bytes.fromhex(c['after']);diff=[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b];assert not diff,(index,diff)
        assert events==c['events'],(index,events,c['events']);assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['environment']['score'],(index,'score');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(index,'sound')
        assert struct.unpack('<HH',m.mem_read(owner+4,4))==(c['environment']['enemyDeathCount'],c['environment']['itemDropIndex']),(index,'cycle');digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/enemy-death.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-death-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
