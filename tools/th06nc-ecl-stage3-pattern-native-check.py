"""Custom 2 shared polygon snapshots, angles, ordered requests and RNG.

Original ECL 121 dispatch/body; JS immediate and registered callback routes.
Compare complete enemy, shared position/angle globals, sound queue and RNG.
Host trig supplied; ordinary bullet allocation, frame scheduling and GPU excluded.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom-stage3.mjs','shared/th06nc/ecl-custom.mjs','shared/th06nc/rng.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{advanceStageThreePattern,createStageThreePatternState}from'./shared/th06nc/ecl-custom-stage3.mjs';import{executeEclCustom,executeEclCustomCallback}from'./shared/th06nc/ecl-custom.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');
for(const clock of [-30,-1,0,1,6,24,30,36,59,60,90])for(const limit of [0,1,30,90])for(const seed of [0,0xbeef,0xffff])for(const player of [[32,-16,8],[192,400,0]])for(const sound of [[-1,-1,-1],[1,22,-1],[-1,22,-1],[1,2,3]])for(const disabled of [false,true]){
 const enemy=Uint8Array.from({length:0x10b0},(_,i)=>i&255),v=new DataView(enemy.buffer);v.setBigUint64(0x98,0x140032cf0n,true);v.setInt32(0x50,clock,true);v.setInt32(0x54,limit,true);v.setFloat32(0x64,60,true);v.setFloat32(0x270,3.7,true);v.setFloat32(0x274,1.25,true);[100.5,200.25,-2].forEach((n,i)=>v.setFloat32(0xb0+i*4,n,true));const shared=createStageThreePatternState(),p=new DataView(shared.positions.buffer),a=new DataView(shared.angles.buffer);[10.5,20.25,-2,0,320,380,1].forEach((n,i)=>p.setFloat32(i*4,n,true));p.setUint32(12,0xdeadbeef,true);[-3,-2,-1,0,1,2].forEach((n,i)=>a.setFloat32(i*4,n,true));const initialPositions=hex(shared.positions),initialAngles=hex(shared.angles),before=hex(enemy),events=[],soundSlots=[...sound],rng=new NativeRng(seed,99),services={environment:{rng,playerPosition:player,stageThreePatternState:shared},soundSlots,soundDisabled:disabled,fireBullets:(e,d)=>events.push(hex(d))},args=new Uint8Array(8);new DataView(args.buffer).setInt32(0,2,true);if(disabled)executeEclCustomCallback(enemy,services);else executeEclCustom(enemy,{opcode:121,args},services);cases.push({clock,limit,seed,player,sound,disabled,initialPositions,initialAngles,before,after:hex(enemy),positions:hex(shared.positions),angles:hex(shared.angles),events,soundSlots,rng:{seed:rng.seed,count:rng.count}});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x14000f870:events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex())
        else:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',math.cos(x)if a==0x1402be071 else math.sin(x)),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000f870,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x140aa1e70,bytes.fromhex(c['initialPositions']));m.mem_write(0x140a6eba0,bytes.fromhex(c['initialAngles']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,c['seed']));m.mem_write(0x140506ad0,struct.pack('<3f',*c['player']));m.mem_write(0x140509670,struct.pack('<3i',*c['sound']));m.mem_write(0x140509694,bytes([int(c['disabled'])]));m.mem_write(n.assets,struct.pack('<ihH4Bii',0,121,20,0,255,0,0,2,0));events.clear()
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R14,n.assets),(UC_X86_REG_R10,0x140000000)]:m.reg_write(reg,value)
        m.emu_start(0x140028150,0x140025d7d,count=500000);assert m.reg_read(UC_X86_REG_RIP)==0x140025d7d,(i,'instruction limit');actual=bytes(m.mem_read(n.owner,0x10b0));wanted=bytes.fromhex(c['after']);assert actual==wanted,(i,c['clock'],c['limit'],'enemy',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);assert events==c['events'],(i,c['clock'],'requests',[(j,a,b)for j,(a,b)in enumerate(zip(events,c['events']))if a!=b][:1]);positions=bytes(m.mem_read(0x140aa1e70,28));angles=bytes(m.mem_read(0x140a6eba0,24));assert positions.hex()==c['positions'],(i,'shared positions');assert angles.hex()==c['angles'],(i,'shared angles',angles.hex(),c['angles']);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(i,'sound');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(i,'RNG');digest.update(actual+positions+angles)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-stage3-pattern-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
