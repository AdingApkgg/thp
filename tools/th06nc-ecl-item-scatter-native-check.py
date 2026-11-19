"""Whole ECL 119 allocation, including its inline high-power ordinary point.

Uses StageWorld's actual item services. Compare all 1025 slots, cursor and RNG
across power/practice, count, positions, pressure and wrap. No item updates/GPU.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/stage-world.mjs','shared/th06nc/ecl-command.mjs','shared/th06nc/item-pool.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{readAnm}from'./shared/th06nc/anm.mjs';import{commonProjectileAssetPlan}from'./shared/th06nc/common-layout.mjs';import{readEcl}from'./shared/th06nc/ecl.mjs';import{StageWorld}from'./shared/th06nc/stage-world.mjs';import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';import{EclOperands}from'./shared/th06nc/ecl-operands.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const refs=commonProjectileAssetPlan(),bank=new AnmBank(),program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata4.ecl')),cases=[],sha=b=>createHash('sha256').update(b).digest('hex');for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});
for(const count of [-1,0,1,3,8])for(const power of [0,128])for(const practice of [false,true])for(const occupied of [0,1020,1024])for(const cursor of [0,1023,1024])for(const position of [[100.5,200.25,-2],[-1000,500,.49]]){const environment={rng:new NativeRng(0xbeef,99),playerPower:power,spellPractice:practice},stage=new StageWorld(program,{anmBank:bank,environment}),pool=stage.items;pool.cursor=cursor;for(let i=0;i<occupied;i++)pool.entry(i).v.setUint8(0,1);const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer),args=new Uint8Array(4);position.forEach((n,k)=>v.setFloat32(0xb0+k*4,n,true));new DataView(args.buffer).setInt32(0,count,true);applyEclCommand(enemy,{opcode:119,args},{...stage.enemies.services,operands:new EclOperands(enemy,environment),gameEnvironment:environment});cases.push({count,power,practice,occupied,cursor,position,debug:count===1&&power===128&&!practice&&occupied===0&&cursor===0?Buffer.from(pool.storage).toString('base64'):null,poolSha:sha(pool.storage),next:pool.cursor,rng:{seed:environment.rng.seed,count:environment.rng.count}});}console.log(JSON.stringify({refs,cases}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256();base=0x140baf0d8
    for index,c in enumerate(data['cases']):
        initial=bytearray(1025*0x160)
        for slot in range(c['occupied']):initial[slot*0x160]=1
        m.mem_write(base,bytes(initial));m.mem_write(0x140c07238,struct.pack('<i',c['cursor']));m.mem_write(n.owner,bytes(0x10b0));m.mem_write(n.owner+0xb0,struct.pack('<3f',*c['position']));m.mem_write(n.assets+0x100000,struct.pack('<i',c['count']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));m.mem_write(0x1404f1e88,struct.pack('<H',c['power']));m.mem_write(0x1404f27b5,bytes([c['practice']]));sp=n.stack+0x8000
        for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RBP,n.stack+0x9000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+0x100000),(UC_X86_REG_R12,0),(UC_X86_REG_RBX,0x9630),(UC_X86_REG_R8,base),(UC_X86_REG_XMM14,int.from_bytes(struct.pack('<f',2**-32),'little')),(UC_X86_REG_XMM15,int.from_bytes(struct.pack('<f',376),'little'))]:m.reg_write(reg,value)
        m.emu_start(0x140027e62,0x140025d7d,count=3000000);actual=bytearray(m.mem_read(base,1025*0x160))
        for slot in range(1025):
            offset=slot*0x160+0x38
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-next(a for a,b in n.ranges if a<=ptr<b))
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(actual).hexdigest()==c['poolSha'],(index,'item pool',[(p//0x160,hex(p%0x160),a,b)for p,(a,b)in enumerate(zip(actual,__import__('base64').b64decode(c['debug']or'')))if a!=b][:40]);assert struct.unpack('<i',m.mem_read(0x140c07238,4))[0]==c['next'],(index,'cursor');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,'RNG');digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-item-scatter-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
