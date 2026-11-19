"""ECL 121 custom entries 0/1, original dispatch and real sprite rebinding.

Complete 640-bullet pool, enemy bytes, ordered effect/shot requests and RNG.
Real resource bindings, eligible states and mode branches; library trig shared.
Effect creation and ordinary shot creation are observed service boundaries.
"""
import hashlib,json,struct,subprocess,base64
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-command.mjs','shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-custom-projectiles.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{BulletPool}from'./shared/th06nc/bullet-pool.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),cases=[],hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const index of [0,1])for(const mode of index===0?[-1,0,1,2]:[-128,0,1,128])for(const seed of [0,0xbeef,0xffff]){const environment={rng:new NativeRng(seed,99),playerPosition:[192,400,0]},pool=new BulletPool({anmBank:bank,environment,sin:()=>.25,cos:()=>.75,atan2:()=>.875}),descriptor=new Uint8Array(108),d=new DataView(descriptor.buffer);d.setInt16(0x18,1,true);d.setInt16(0x1a,1,true);d.setFloat32(4,3.7,true);d.setFloat32(8,.4,true);d.setFloat32(0xc,100,true);d.setFloat32(0x10,100,true);d.setFloat32(0x34,.5,true);d.setFloat32(0x38,.6,true);for(let type=0;type<10;type++){d.setInt16(0x2c,type,true);const e=pool.spawn(descriptor)[0];e.v.setUint16(0x44,type%6,true);}const beforePool=Buffer.from(pool.storage).toString('base64'),enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setFloat32(p,(p%37)-15.75,true);[100.5,200.25,-2].forEach((n,k)=>v.setFloat32(0xb0+k*4,n,true));const args=new Uint8Array(8),a=new DataView(args.buffer);a.setInt32(0,index,true);a.setInt32(4,mode,true);const initialSeed=environment.rng.seed,initialCount=environment.rng.count,before=hex(enemy),events=[];applyEclCommand(enemy,{opcode:121,args},{gameEnvironment:environment,bulletPool:pool,sin:()=>.25,cos:()=>.75,spawnEffect:r=>events.push({kind:'effect',...r}),fireBullets:(e,s)=>events.push({kind:'shot',descriptor:hex(s)})});cases.push({index,mode,beforePool,before,after:hex(enemy),poolSha:sha(pool.storage),events,initialSeed,initialCount,rng:{seed:environment.rng.seed,count:environment.rng.count}});}console.log(JSON.stringify({refs,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;events=[];digest=hashlib.sha256();base=0x1403ec2a8
    def normalize(block,encode=False):
        for slot in range(640):
            for j in range(5):
                offset=slot*0x620+0x50+j*0x120;script=struct.unpack_from('<H',block,offset+0x38)[0]
                for field in [0xf0,0xf8]:
                    p=offset+field;ptr=struct.unpack_from('<Q',block,p)[0]
                    if ptr:struct.pack_into('<Q',block,p,(n.assetByFile['etama4.anm'if script>=698 else'etama3.anm']+ptr)if encode else ptr-next(a for a,b in n.ranges if a<=ptr<b))
                p=offset+0x100;ptr=struct.unpack_from('<Q',block,p)[0]
                if ptr:struct.pack_into('<Q',block,p,n.manager+0x608+(ptr-1)*64 if encode else(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14002b0d0:events.append(dict(kind='effect',type=m.reg_read(UC_X86_REG_EDX),position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_R8),12))),count=m.reg_read(UC_X86_REG_R9D),color=struct.unpack('<I',m.mem_read(sp+0x28,4))[0]));m.reg_write(UC_X86_REG_RAX,0)
        elif a==0x14000f870:events.append(dict(kind='shot',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex()))
        else:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',.75 if a==0x1402be071 else .25),'little'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14002b0d0,0x14000f870,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(data['cases']):
        pool=bytearray(base64.b64decode(c['beforePool']));normalize(pool,True);m.mem_write(base,bytes(pool));m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(n.assets+0x100000,struct.pack('<ihH4Bii',0,121,20,0,255,0,0,c['index'],c['mode']));m.mem_write(0x140a6ec40,struct.pack('<IH',c['initialCount'],c['initialSeed']));events.clear()
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+0x10000c),(UC_X86_REG_R14,n.assets+0x100000),(UC_X86_REG_R10,0x140000000)]:m.reg_write(reg,value)
        m.emu_start(0x140028150,0x140025d7d,count=3000000);assert events==c['events'],(index,'events',events,c['events']);assert bytes(m.mem_read(n.owner,0x10b0)).hex()==c['after'],(index,'enemy');actual=bytearray(m.mem_read(base,640*0x620));normalize(actual);assert hashlib.sha256(actual).hexdigest()==c['poolSha'],(index,'bullet pool');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'RNG',seed,count,c['rng']);digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-custom-stage2-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
