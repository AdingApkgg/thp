"""Actual 1024-slot item owner from 42a3b, excluding C++ static TLS init.

Real item constructors/ANM, homing/scatter/falling, pickups and score rings
across 120 frames. Shared fixed trig; EF00 conversion observed, not executed.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/item-pool.mjs','shared/th06nc/item-motion.mjs','shared/th06nc/item-collect.mjs','shared/th06nc/score-popup-pool.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{ItemPool}from'./shared/th06nc/item-pool.mjs';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),scenes=[];for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const hash=b=>createHash('sha256').update(b).digest('hex');
for(const mode of [0,1,2])for(const state of [0,1,2,3])for(const y of [100,128,400]){
 const env={rng:new NativeRng(0xbeef,99),playerPower:[7,127,128][scenes.length%3],difficulty:scenes.length%5,powerItemChain:29,bombs:7,lives:7,lifeProtection:false,deathCount:4,inputFlags:0x5ff,pointStageCount:65535,pointTotalCount:65534,stageGraze:99,grazeCountersDisabled:false,score:0xfffffffffffffff0n},initial={...env,rng:null,score:String(env.score)},pool=new ItemPool({anmBank:bank,environment:env}),popups=new ScorePopupPool(),sounds=[-1,-1,-1],cancels=[],player={position:[192,y,.5],state},drops=[];for(let type=0;type<7;type++){const drop={type,mode,position:[160+type*10,y-20+(type%3)*10,.5]};drops.push(drop);pool.spawn(drop);}const frames=[];
 for(let frame=1;frame<=120;frame++){pool.tick({player,popups,soundSlots:sounds,cancelBullets:r=>cancels.push(r),sin:()=>.25,cos:()=>.75,atan2:()=>.875});if([1,2,30,60,61,120].includes(frame))frames.push({frame,pool:hash(pool.storage),popups:hash(popups.storage),activeCount:pool.activeCount,cursor:pool.cursor,popupCursor:popups.cursor,smallCursor:popups.smallCursor,sounds:[...sounds],cancels:[...cancels],env:{...env,rng:{...env.rng},score:String(env.score)}});}scenes.push({mode,state,y,initial,drops,frames});
}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;base=0x140baf0d8;size=1025*0x160;digest=hashlib.sha256();cancels=[];checked=0
    fields={'playerPower':(0x4f1e88,'H'),'difficulty':(0x4f27c0,'i'),'powerItemChain':(0x4ff0dd,'B'),'bombs':(0x4ff0f1,'B'),'lives':(0x4ff0f0,'B'),'lifeProtection':(0x4f27c4,'B'),'deathCount':(0x4f1e60,'i'),'inputFlags':(0xa6ec18,'I'),'pointStageCount':(0x4f27ba,'H'),'pointTotalCount':(0x4f27bc,'H'),'stageGraze':(0x4ff0cc,'i'),'grazeCountersDisabled':(0x509268,'B'),'score':(0x4f2798,'Q')}
    def hook(m,a,size,u):
        if a==0x14000ef00:cancels.append({'items':bool(m.reg_read(UC_X86_REG_DL))})
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',.875 if a==0x1402be065 else .75 if a==0x1402be071 else .25),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000ef00,0x1402be065,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,s in enumerate(data['scenes']):
        cancels.clear();m.mem_write(base-8,bytes(size+12));m.mem_write(0x1403de870,bytes(515*40));m.mem_write(0x1403de628,bytes(8));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f27b5,b'\0');m.mem_write(n.owner,bytes(0x1000));m.mem_write(0x140a6ec08,struct.pack('<Q',n.owner));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,b'\0');m.mem_write(0x140506c38,bytes([s['state']]));m.mem_write(0x140506ad0,struct.pack('<3f',192,s['y'],.5));m.mem_write(0x14050963c,struct.pack('<3f',186,s['y']-6,0));m.mem_write(0x140509648,struct.pack('<3f',198,s['y']+6,1));m.mem_write(0x140c25510,struct.pack('<3f',16,16,16))
        for key,(off,fmt)in fields.items():m.mem_write(0x140000000+off,struct.pack('<'+fmt,int(s['initial'][key])))
        sp=n.stack+0x8000
        for drop in s['drops']:
            m.mem_write(n.vm,struct.pack('<3f',*drop['position']));m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8D,drop['type']);m.reg_write(UC_X86_REG_R9D,drop['mode']);m.emu_start(0x1400426e0,n.stack+0xf000,count=1000000)
        last=0
        for c in s['frames']:
            for frame in range(last+1,c['frame']+1):
                m.mem_write(sp+0xe8,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_R14,base);m.reg_write(UC_X86_REG_XMM6,0);m.emu_start(0x140042a3b,n.stack+0xf000,count=1000000)
            last=c['frame'];actual=bytearray(m.mem_read(base,size))
            for slot in range(7):
                offset=slot*0x160+0x38
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                    if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
                p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
            assert hashlib.sha256(actual).hexdigest()==c['pool'],(index,s['mode'],s['state'],s['y'],last,'pool',actual[:64].hex());assert hashlib.sha256(m.mem_read(0x1403de870,515*40)).hexdigest()==c['popups'],(index,last,'popups')
            assert struct.unpack('<i',m.mem_read(base-8,4))[0]==c['activeCount'],(index,last,'activeCount');assert struct.unpack('<i',m.mem_read(0x140c07238,4))[0]==c['cursor'];assert struct.unpack('<2i',m.mem_read(0x1403de628,8))==(c['popupCursor'],c['smallCursor']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,last,'sounds');assert cancels==c['cancels']
            for key,(off,fmt)in fields.items():
                value=struct.unpack('<'+fmt,m.mem_read(0x140000000+off,struct.calcsize(fmt)))[0];assert value==int(c['env'][key]),(index,last,key,value,c['env'][key])
            count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['env']['rng'];digest.update(actual);checked+=1
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,scenes=len(data['scenes']),frames=len(data['scenes'])*120,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-item-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
