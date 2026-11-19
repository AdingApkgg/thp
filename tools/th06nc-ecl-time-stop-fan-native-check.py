"""Custom entry 5: ordered nine-shot descriptors, enemy counter and sound queue.

Original callback body, real resource-independent math. Shot allocation is an
observed boundary; only the initialized/consumed 0x50 descriptor bytes compare.
The remaining descriptor tail is uninitialized native stack, not shot input.
Both fixed trigonometric service results and host-library float results compare.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-custom-time-stop.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{executeEclCustomCallback}from'./shared/th06nc/ecl-custom.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const trig of ['fixed','real'])for(const clock of [-18,-9,-1,0,1,8,9,18,72,81,90,2147483647])for(const difficulty of [0,1,2,3])for(const target of [[192,400,0],[100,200,-2],[100.00000001,200,-2],[100.00000762939453,200,-2],[0,0,0],[100,200,-2.000000238418579]])for(const sound of [[-1,-1,-1],[1,7,-1],[-1,7,-1],[1,2,3]])for(const disabled of [false,true]){const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);v.setBigUint64(0x98,0x140033a30n,true);v.setInt32(0x50,clock,true);[100,200,-2].forEach((n,i)=>v.setFloat32(0xb0+i*4,n,true));const before=hex(enemy),events=[],soundSlots=[...sound];executeEclCustomCallback(enemy,{environment:{difficulty,playerPosition:target.map(Math.fround)},fireBullets:(e,d)=>events.push(hex(d.subarray(0,0x50))),soundSlots,soundDisabled:disabled,sin:trig==='fixed'?()=>.25:Math.sin,cos:trig==='fixed'?()=>.75:Math.cos});cases.push({trig,clock,difficulty,target:target.map(Math.fround),sound,disabled,before,after:hex(enemy),events,soundSlots});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];trig='fixed';digest=hashlib.sha256()
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x14000f870:events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),0x50)).hex())
        elif a!=0x1402bcf20:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];value=(math.cos(x)if a==0x1402be071 else math.sin(x))if trig=='real'else(.75 if a==0x1402be071 else .25);m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',value),'little'))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000f870,0x1402bcf20,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for i,c in enumerate(cases):
        trig=c['trig'];m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.mem_write(0x140506ad0,struct.pack('<3f',*c['target']));m.mem_write(0x140509670,struct.pack('<3i',*c['sound']));m.mem_write(0x140509694,bytes([int(c['disabled'])]));events.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140033a30,n.assets,count=100000)
        assert events==c['events'],(i,c['clock'],c['difficulty'],'shots',events[:1],c['events'][:1]);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],(i,'enemy');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['soundSlots'],(i,'sound');digest.update(actual);digest.update(''.join(events).encode())
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-time-stop-fan-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
