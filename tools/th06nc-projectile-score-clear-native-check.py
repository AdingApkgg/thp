"""Entire F300 scored projectile clear with real score-item ANM allocation.

All bullet/laser and 1025 item slot bytes, pool pressure and cursor wrap;
shared fixed trig. Full score popup rings, score and HUD; item update and rendering excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/projectile-clear.mjs','shared/th06nc/item-pool.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{ItemPool}from'./shared/th06nc/item-pool.mjs';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';import{clearProjectilesWithScore}from'./shared/th06nc/projectile-clear.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[],hash=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const items of [false,true])for(const occupied of [0,1020,1024])for(const cursor of [0,1023,1024])for(const variant of [0,1,2,3]){
 const pool=new ItemPool({anmBank:bank,environment:{rng:new NativeRng(0xbeef,99)}});pool.cursor=cursor;for(let s=0;s<occupied;s++)pool.entry(s).v.setUint8(0,1);const bullets=new Uint8Array(640*0x620),lasers=new Uint8Array(64*0x298),b=new DataView(bullets.buffer),l=new DataView(lasers.buffer);for(let s=0;s<640;s+=37){const p=s*0x620;bullets.fill(0x55,p,p+0x620);b.setUint16(p+0x44,(s+variant)%6,true);[100+s,200-s,.5].forEach((x,k)=>b.setFloat32(p+0x30+k*4,x,true));}for(let s=0;s<64;s+=11){const p=s*0x298; l.setUint8(p+0x274,1);l.setUint8(p+0x290,(s+variant)%3);l.setInt32(p,123,true);l.setInt32(p+8,12,true);l.setInt32(p+0xc,13,true);l.setFloat32(p+0x260,.75,true);l.setFloat32(p+0x10,variant*16,true);l.setFloat32(p+0x14,variant===3?-10:100,true);[100,200,.5].forEach((x,k)=>l.setFloat32(p+0x278+k*4,x,true));}const beforeBullets=Buffer.from(bullets).toString('base64'),beforeLasers=Buffer.from(lasers).toString('base64');const popups=new ScorePopupPool(),env={score:0xfffffffffffffff0n},bossState={},total=clearProjectilesWithScore({bullets,lasers,items,itemPool:pool,popups,environment:env,bossState,sin:()=>.25,cos:()=>.75});cases.push({total,popups:hash(popups.storage),popupCursor:popups.cursor,score:String(env.score),bossState,items,occupied,cursor,variant,beforeBullets,beforeLasers,bullets:hash(bullets),lasers:hash(lasers),pool:hash(pool.storage),next:pool.cursor,rng:pool.environment.rng});
}console.log(JSON.stringify({refs,cases}));
"""
    import base64
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',.75 if a==0x1402be071 else .25),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(data['cases']):
        initial=bytearray(1025*0x160)
        for slot in range(c['occupied']):initial[slot*0x160]=1
        m.mem_write(0x1403de870,bytes(515*40));m.mem_write(0x1403de628,bytes(8));m.mem_write(0x1404f2798,struct.pack('<Q',0xfffffffffffffff0));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(n.owner,bytes(0x1000));m.mem_write(0x140baf0d8,bytes(initial));m.mem_write(0x140c07238,struct.pack('<i',c['cursor']));m.mem_write(0x1403ec2a8,base64.b64decode(c['beforeBullets']));m.mem_write(0x1404e12b8,base64.b64decode(c['beforeLasers']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_R8D,int(c['items']));m.emu_start(0x14000f300,n.stack+0xf000,count=10000000)
        assert m.reg_read(UC_X86_REG_EAX)==c['total']&0xffffffff,(index,'total');assert str(struct.unpack('<Q',m.mem_read(0x1404f2798,8))[0])==c['score'];assert hashlib.sha256(m.mem_read(0x1403de870,515*40)).hexdigest()==c['popups'];assert struct.unpack('<i',m.mem_read(0x1403de628,4))[0]==c['popupCursor']
        if c['total']:assert bytes(m.mem_read(n.owner+0x6c0,28))==struct.pack('<iiB3x3fi',-999,0,1,620,32,0,c['total'])
        for addr,size,key in [(0x1403ec2a8,640*0x620,'bullets'),(0x1404e12b8,64*0x298,'lasers')]:assert hashlib.sha256(m.mem_read(addr,size)).hexdigest()==c[key],(index,key)
        actual=bytearray(m.mem_read(0x140baf0d8,1025*0x160))
        for slot in range(1025):
            offset=slot*0x160+0x38
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['pool'],(index,'items');assert struct.unpack('<i',m.mem_read(0x140c07238,4))[0]==c['next'],(index,'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-projectile-score-clear-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
