"""Custom callback 17 (direct jump to 10), original body with real boss and effect ANM binding.

Full enemy and 513 effect slots, cursor, ordered requests and RNG compare.
Bomb/no-bomb, life, animation, countdown, particle scheduling, release/exhausted
pool are included. Host-library trig is supplied; drawing/audio are excluded.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-custom-particles.mjs','shared/th06nc/ecl-custom-boss.mjs','shared/th06nc/anm-rebind.mjs','shared/th06nc/enemy-pool.mjs','shared/th06nc/effect-pool.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{executeEclCustomCallback}from'./shared/th06nc/ecl-custom.mjs';import{EffectPool}from'./shared/th06nc/effect-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';const refs=[{archive:'th06CM.dat',file:'etama4.anm',slot:7,base:698},{archive:'th06ST.dat',file:'stg6enm.anm',slot:8,base:256},{archive:'th06ST.dat',file:'stg6enm2.anm',slot:9,base:256}],bank=new AnmBank(),cases=[],hex=b=>Buffer.from(b).toString('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const life of [-1,0,1])for(const bomb of [false,true])for(const automatic of [-1,161])for(const clock of [-1,0,1,2,60])for(const time of [0,1,120])for(const same of [false])for(const angle of [.78])for(const seed of [0xbeef])for(const occupied of [0,512])for(const release of [false,true]){const rng=new NativeRng(seed,99),pool=new EffectPool({anmBank:bank,rng}),enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);for(let i=0;i<occupied;i++)pool.entry(i).v.setUint8(0x14,1);v.setBigUint64(0x98,0x140035a20n,true);v.setUint8(0xbe,release?8:0);v.setInt32(0x1090,3,true);v.setBigUint64(0xbe8,1n,true);v.setBigUint64(0xbf8,3n,true);v.setFloat32(0x228,angle,true);v.setInt32(0x2d0,time,true);v.setInt32(0x2cc,same?time:-999,true);[100.5,200.25,-2].forEach((n,i)=>v.setFloat32(0xb0+i*4,n,true));v.setInt32(0x234,life,true);v.setInt16(0xf6c,automatic,true);v.setInt32(0x1098,clock,true);v.setUint8(0xbd,0xff);const before=hex(enemy),events=[];executeEclCustomCallback(enemy,{environment:{rng,bombActive:bomb},anmBank:bank,enemyAnms:new Map(),linkedEffects:new Map([[1n,pool.entry(0)],[3n,pool.entry(2)]]),spawnEffect:r=>{events.push(r);return pool.spawn(r);}});cases.push({life,bomb,automatic,clock,time,same,angle,seed,occupied,release,before,after:hex(enemy),events,poolSha:createHash('sha256').update(pool.storage).digest('hex'),cursor:pool.cursor,rng:{seed:rng.seed,count:rng.count}});}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;events=[];digest=hashlib.sha256();base=0x140a6ecd0
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14002b0d0:
            events.append(dict(type=m.reg_read(UC_X86_REG_EDX),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12))),count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0]));return
        x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];value=math.cos(x)if a==0x1402be071 else math.sin(x);m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14002b0d0,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(data['cases']):
        pool=bytearray(0x331a0)
        for slot in range(c['occupied']):pool[slot*0x198+0x14]=1
        m.mem_write(base,bytes(pool));enemy=bytearray.fromhex(c['before'])
        for field in [0xbe8,0xbf0,0xbf8]:
            ptr=struct.unpack_from('<Q',enemy,field)[0]
            if ptr:struct.pack_into('<Q',enemy,field,base+(ptr-1)*0x198)
        m.mem_write(0x140509268,bytes([int(c['bomb'])]));m.mem_write(n.owner,bytes(enemy));m.mem_write(0x140a6ec40,struct.pack('<IH',99,c['seed']));events.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets+0x100000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140035a20,n.assets+0x100000,count=1000000)
        actualEnemy=bytearray(m.mem_read(n.owner,0x10b0))
        for field in [0xbe8,0xbf0,0xbf8]:
            ptr=struct.unpack_from('<Q',actualEnemy,field)[0]
            if ptr:struct.pack_into('<Q',actualEnemy,field,(ptr-base)//0x198+1)
        for field in [0x1f8,0x200]:
            ptr=struct.unpack_from('<Q',actualEnemy,field)[0]
            if ptr:struct.pack_into('<Q',actualEnemy,field,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
        ptr=struct.unpack_from('<Q',actualEnemy,0x208)[0]
        if ptr:struct.pack_into('<Q',actualEnemy,0x208,(ptr-n.manager-0x608)//64+1)
        assert actualEnemy.hex()==c['after'],(i,c['life'],c['bomb'],c['automatic'],c['clock'],'enemy',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actualEnemy,bytes.fromhex(c['after'])))if a!=b][:25]);assert events==c['events'],(i,'requests',events,c['events']);actual=bytearray(m.mem_read(base,513*0x198))
        for slot in range(513):
            for field in [0x130,0x138]:
                p=slot*0x198+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=slot*0x198+0x140;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['poolSha'],(i,c['time'],c['occupied'],'pool');assert struct.unpack('<i',m.mem_read(base+0x3319c,4))[0]==c['cursor'],(i,'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(i,'RNG');digest.update(actual);digest.update(actualEnemy)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-extra-boss-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
