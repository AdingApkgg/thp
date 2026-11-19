"""All seven item pickup branches against original 42d5a..43796.

Whole item and popup rings, counters, power, sound and HUD popup compared.
EF00 conversion is an observed service boundary; movement and owner excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/item-collect.mjs','shared/th06nc/score-popup-pool.mjs','shared/th06nc/hud-notifications.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}
    script="""
import{createHash}from'node:crypto';import{bindHudPopup}from'./shared/th06nc/hud-notifications.mjs';import{collectItem}from'./shared/th06nc/item-collect.mjs';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';const cases=[];
for(let type=0;type<7;type++)for(const power of [0,7,8,15,16,120,127,128,200])for(let difficulty=0;difficulty<6;difficulty++)for(const y of [-10,127.9,128,400])for(let extra=0;extra<2;extra++){
 const index=cases.length,env={playerPower:power,difficulty,powerItemChain:extra?255:29,bombs:extra?8:7,lives:extra?8:7,lifeProtection:!!extra,deathCount:4,inputFlags:0x5ff,pointStageCount:65535,pointTotalCount:65534,stageGraze:extra?99999:99,grazeCountersDisabled:index%3===0,score:0xfffffffffffffff0n};const initial={...env,score:String(env.score)},bytes=new Uint8Array(0x160),v=new DataView(bytes.buffer);v.setUint8(0,1);v.setInt32(8,13,true);v.setInt8(0x34,type);[100,y,.5].forEach((x,k)=>v.setFloat32(0x10+k*4,x,true));const hudBytes=new Uint8Array(0x4228),hud={bytes:hudBytes,v:new DataView(hudBytes.buffer)};bindHudPopup(hud,env,'powerPopup',0x6dc);const before=Buffer.from(bytes).toString('hex'),pool=new ScorePopupPool();pool.cursor=511;pool.smallCursor=2;const sounds=[-1,-1,-1],cancels=[],soundDisabled=index%7===0,pointValue=collectItem({v},{environment:env,popups:pool,cancelBullets:r=>cancels.push(r),soundSlots:sounds,soundDisabled,pointValue:4242});cases.push({hudSha256:createHash('sha256').update(hud.bytes).digest('hex'),type,initial,before,soundDisabled,env:{...env,score:String(env.score)},sounds,cancels,pointValue,after:Buffer.from(bytes).toString('hex'),popupSha:createHash('sha256').update(pool.storage).digest('hex'),cursor:pool.cursor,smallCursor:pool.smallCursor});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;base=0x1403de870;digest=hashlib.sha256();cancels=[]
    fields={'playerPower':(0x4f1e88,'H'),'difficulty':(0x4f27c0,'i'),'powerItemChain':(0x4ff0dd,'B'),'bombs':(0x4ff0f1,'B'),'lives':(0x4ff0f0,'B'),'lifeProtection':(0x4f27c4,'B'),'deathCount':(0x4f1e60,'i'),'inputFlags':(0xa6ec18,'I'),'pointStageCount':(0x4f27ba,'H'),'pointTotalCount':(0x4f27bc,'H'),'stageGraze':(0x4ff0cc,'i'),'grazeCountersDisabled':(0x509268,'B'),'score':(0x4f2798,'Q')}
    def hook(m,a,size,u):
        cancels.append({'items':bool(m.reg_read(UC_X86_REG_DL))});sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x14000ef00,end=0x14000ef00)
    starts=[0x42d5a,0x4306b,0x4318e,0x433c7,0x4347d,0x433f6,0x43676]
    for index,c in enumerate(cases):
        cancels.clear();m.mem_write(base,bytes(515*40));m.mem_write(0x1403de628,struct.pack('<2i',511,2));m.mem_write(n.vm,bytes.fromhex(c['before']));m.mem_write(n.owner,bytes(0x4228));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,bytes([c['soundDisabled']]))
        for key,(off,fmt) in fields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(c['initial'][key])))
        for reg,value in [(UC_X86_REG_RSI,0x140000000),(UC_X86_REG_R14,n.vm),(UC_X86_REG_RBP,0),(UC_X86_REG_EDX,128),(UC_X86_REG_R10D,0xffffff00),(UC_X86_REG_R9D,100),(UC_X86_REG_R15D,4242),(UC_X86_REG_EDI,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.mem_write(n.stack+0x80f0,bytes(4));m.emu_start(0x140000000+starts[c['type']],0x140043796,count=100000)
        assert bytes(m.mem_read(n.vm,0x160)).hex()==c['after'],(index,'item')
        for key,(off,fmt) in fields.items():
            actual=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert actual==int(c['env'][key]),(index,c['type'],key,actual,c['env'][key])
        actual=bytes(m.mem_read(base,515*40));assert hashlib.sha256(actual).hexdigest()==c['popupSha'],(index,c['type'],'popup',[(hex(p),a)for p,a in enumerate(actual)if a][:100]);assert struct.unpack('<2i',m.mem_read(0x1403de628,8))==(c['cursor'],c['smallCursor'])
        assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,'sounds');assert cancels==c['cancels'],(index,'cancel');assert m.reg_read(UC_X86_REG_R15D)==c['pointValue']&0xffffffff,(index,'pointValue')
        assert hashlib.sha256(bytes(m.mem_read(n.owner,0x4228))).hexdigest()==c['hudSha256'],(index,'aliased HUD owner')
        if c['env'].get('powerPopup'):
            assert bytes(m.mem_read(n.owner+0x6dc,28))==struct.pack('<iiB3x3fi',-999,0,1,620,232,0,0),(index,'powerPopup')
        digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-item-collect-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
