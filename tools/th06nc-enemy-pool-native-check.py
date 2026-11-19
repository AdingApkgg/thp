"""Ordinary enemy pool spawn, original template constructor and initial ECL tick.

Stage 1 scripts/ANMs execute with shared supplied trig results. Memory copy/zero
and bullet requests are supplied services; drawing, collisions and gameplay excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{readFileSync}from'node:fs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{stageAssetPlan,loadStageEnemyBank}from'./shared/th06nc/stage-layout.mjs';import{EnemyPool,createEnemyTemplate}from'./shared/th06nc/enemy-pool.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';
const plan=stageAssetPlan(1),resources=new Map(plan.enemyAnimations.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+r.file))])),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl')),cases=[];
for(const occupied of [0,1,3])for(const life of [-1,8,32])for(const item of [-1,0,1])for(const score of [-1,300])for(const withContext of [false,true]){
const bank=new AnmBank();loadStageEnemyBank(bank,resources,1);const pool=new EnemyPool(program,{anmBank:bank,environment:{difficulty:1,rank:0,playerPosition:[192,400,0]},sin:()=>0.25,cos:()=>0.75,atan2:()=>0.875,fireBullets:()=>{}});pool.environment.rng=new NativeRng(0xbeef,99);
for(let i=0;i<occupied;i++)pool.storage[i*0x10b0+0xbc]=128;const context=withContext?new Uint8Array(64):null;if(context){const v=new DataView(context.buffer);for(let i=0;i<16;i++)v.setFloat32(i*4,i+0.25,true);}
const result=pool.spawn({sub:0,position:[60,-32,0],life,item,score,context});cases.push({occupied,life,item,score,context:context?Buffer.from(context).toString('hex'):null,slot:result.slot,after:Buffer.from(result.enemy).toString('hex'),rng:{seed:pool.environment.rng.seed,count:pool.environment.rng.count}});}
console.log(JSON.stringify({plan,template:Buffer.from(createEnemyTemplate()).toString('hex'),cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['plan']['enemyAnimations']);m=n.m;digest=hashlib.sha256();owner=0x140aa1e90;programBase=n.assets+0x100000;table=n.vm+0x8000
    program=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata1.ecl').read_bytes();m.mem_write(programBase,program)
    for i in range(struct.unpack_from('<H',program)[0]):m.mem_write(table+i*8,struct.pack('<Q',programBase+struct.unpack_from('<I',program,16+i*4)[0]))
    m.mem_write(0x140a6eb80,struct.pack('<Q',table))
    def hook(m,a,size,u):
        if a in [0x1402bdee2,0x1402bdee8]:
            dst=m.reg_read(UC_X86_REG_RCX);src=m.reg_read(UC_X86_REG_RDX);size=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([src&255])*size if a==0x1402bdee2 else bytes(m.mem_read(src,size)));m.reg_write(UC_X86_REG_RAX,dst)
        elif a in [0x1402be065,0x1402be071,0x1402be07d]:m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',{0x1402be065:0.875,0x1402be071:0.75,0x1402be07d:0.25}[a]),'little'))
        elif a==0x1402bcf20:pass
        elif a==0x14000f870:raise AssertionError('Unexpected initial emission in this script')
        else:return
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    def run(addr):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(addr,n.stack+0xf000,count=1000000)
    for index,c in enumerate(data['cases']):
        run(0x140035f50);assert bytes(m.mem_read(owner+0x10c130,0x10b0)).hex()==data['template'],'template mismatch'
        for i in range(c['occupied']):m.mem_write(owner+8+i*0x10b0+0xbc,b'\x80')
        m.mem_write(0x1404f27c0,struct.pack('<i',1));m.mem_write(0x1404ff27c,bytes(4));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x140506ad0,struct.pack('<3f',192,400,0));m.mem_write(n.vm,struct.pack('<3f',60,-32,0))
        if c['context']:m.mem_write(n.vm+256,bytes.fromhex(c['context']))
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<q',c['item']));m.mem_write(sp+0x30,struct.pack('<q',c['score']));m.mem_write(sp+0x38,struct.pack('<Q',n.vm+256 if c['context']else 0))
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RCX,owner),(UC_X86_REG_RDX,0),(UC_X86_REG_R8,n.vm),(UC_X86_REG_R9,c['life']&0xffff)]:m.reg_write(reg,value)
        m.emu_start(0x1400360d0,n.stack+0xf000,count=1000000);ptr=m.reg_read(UC_X86_REG_RAX);assert ptr==owner+8+c['slot']*0x10b0,(index,hex(ptr),c['slot'])
        actual=bytearray(m.mem_read(ptr,0x10b0));script=struct.unpack_from('<Q',actual,0x88)[0];struct.pack_into('<Q',actual,0x88,script-programBase)
        for p in [0xf0,0xf8]:
            value=struct.unpack_from('<Q',actual,0x108+p)[0]
            if value:struct.pack_into('<Q',actual,0x108+p,value-n.assetByFile['stg1enm.anm'])
        value=struct.unpack_from('<Q',actual,0x208)[0]
        if value:struct.pack_into('<Q',actual,0x208,(value-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['after']);diff=[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y];assert not diff,(index,diff)
        count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],index;digest.update(actual)
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['shared/th06nc/enemy-pool.mjs','shared/th06nc/ecl-tick.mjs','shared/th06nc/ecl-command.mjs','shared/th06nc/ecl-shot-config.mjs']},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-pool-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
