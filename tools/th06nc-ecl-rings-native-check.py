"""ECL 121 custom 7: full enemy, 48 ordered laser/shot requests and RNG.

Real original dispatch and callback body. Covers four difficulties, zero and
nonzero modes, seeds and positions. Host sine/cosine shared; entity allocation,
GPU and full combat excluded from this request-boundary comparison.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom-rings.mjs','shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-command.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const difficulty of [0,1,2,3])for(const mode of [-1,0,1,2])for(const seed of [0,0xbeef,0xffff])for(const position of [[100.5,200.25,-2],[-32,16,.49]]){const enemy=Uint8Array.from({length:0x10b0},(_,i)=>i&255),v=new DataView(enemy.buffer);position.forEach((x,i)=>v.setFloat32(0xb0+i*4,x,true));const before=hex(enemy),rng=new NativeRng(seed,99),args=new Uint8Array(8),a=new DataView(args.buffer),events=[];a.setInt32(0,7,true);a.setInt32(4,mode,true);applyEclCommand(enemy,{opcode:121,args},{gameEnvironment:{difficulty,rng},spawnLaser:d=>events.push({kind:'laser',descriptor:hex(d)}),fireBullets:(e,d)=>events.push({kind:'shot',descriptor:hex(d)})});cases.push({difficulty,mode,seed,before,after:hex(enemy),events,rng:{seed:rng.seed,count:rng.count}});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a in [0x14000f870,0x1400105e0]:events.append(dict(kind='shot'if a==0x14000f870 else'laser',descriptor=bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108 if a==0x14000f870 else 0x44)).hex()))
        elif a!=0x1402bcf20:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',math.cos(x)if a==0x1402be071 else math.sin(x)),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000f870,0x1400105e0,0x1402bcf20,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,c['seed']));m.mem_write(n.assets,struct.pack('<ihH4Bii',0,121,20,0,255,0,0,7,c['mode']));events.clear()
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R10,0x140000000)]:m.reg_write(reg,value)
        m.emu_start(0x140028150,0x140025d7d,count=500000);assert events==c['events'],(i,c['mode'],c['difficulty'],'requests',[(j,a,b)for j,(a,b)in enumerate(zip(events,c['events']))if a!=b][:1]);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],(i,'enemy');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(i,'RNG');digest.update(actual);digest.update(''.join(e['descriptor']for e in events).encode())
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-rings-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
