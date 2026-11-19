"""Priority-14 screen-shake update 76310: owner, viewport and RNG bytes.

Frozen/expired/live owners, signed interpolation and sequential updates.
Task-list allocation/removal and final GPU viewport composition are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/screen-shake.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{ScreenShake}from'./shared/th06nc/screen-shake.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const scenes=[],hex=b=>Buffer.from(b.buffer,b.byteOffset,b.byteLength).toString('hex');for(const frames of [-1,0,1,2,16,60,200])for(const amplitude of [1,24,-17,2147483647])for(const endAmplitude of [0,7,-3])for(const seed of [0,0xbeef,65535])for(const clock of [0,frames-2]){const effect=new ScreenShake({frames,amplitude,endAmplitude}),v=effect.v;v.setInt32(8,clock,true);v.setInt32(0x34,123,true);const before=hex(effect.bytes),rng=new NativeRng(seed,99),viewport=new Float32Array([12,34,56,78]),steps=[];for(let i=0;i<8;i++){const timeStop=i===0||i===3,result=effect.tick(viewport,{rng,timeStop});steps.push({timeStop,result,state:hex(effect.bytes),viewport:hex(viewport),rng:{seed:rng.seed,count:rng.count}});}scenes.push({before,seed,steps});}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0
    for index,s in enumerate(scenes):
        m.mem_write(n.owner,bytes.fromhex(s['before']));m.mem_write(0x140a6ec40,struct.pack('<IH',99,s['seed']));m.mem_write(0x1404f1e70,struct.pack('<4f',12,34,56,78))
        for step,c in enumerate(s['steps']):
            m.mem_write(0x1404f27b9,bytes([c['timeStop']]));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140076310,n.assets,count=1000);assert m.reg_read(UC_X86_REG_RIP)==n.assets;assert m.reg_read(UC_X86_REG_EAX)==int(c['result']),(index,step,'return');actual=bytes(m.mem_read(n.owner,0x38));assert actual.hex()==c['state'],(index,step,'owner');assert bytes(m.mem_read(0x1404f1e70,16)).hex()==c['viewport'],(index,step,'viewport');count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'],(index,step,'rng');digest.update(actual);checked+=1
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,scenes=len(scenes),frames=checked,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-screen-shake-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
