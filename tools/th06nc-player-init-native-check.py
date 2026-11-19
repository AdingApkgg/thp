"""Actual player initializer 68160..687e2, both characters/shots and intro flags.

Real player ANM scripts execute; full owner bytes and RNG compared. Asset loader
uses already published bank. Main loop, shots, bombs and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-init.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{initializePlayer,playerAssetPlan}from'./shared/th06nc/player-init.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';const cases=[];for(const character of [0,1])for(const shot of [0,1])for(const skipIntro of [false,true]){const ref=playerAssetPlan(character),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const state=new Uint8Array(0xa300),rng=new NativeRng(0xbeef,99);initializePlayer(state,{anmBank:bank,environment:{rng},character,shot,skipIntro});cases.push({ref,character,shot,skipIntro,rng,sha256:createHash('sha256').update(state).digest('hex'),state:Buffer.from(state).toString('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(cases):
        n.load_title([c['ref']]);m.mem_write(n.owner,bytes(0xa300));m.mem_write(0x1404f1e80,bytes([c['character'],c['shot']]));m.mem_write(0x140c21d9c,struct.pack('<i',3));m.mem_write(0x1404f27b5,bytes([c['skipIntro']]));m.mem_write(0x140a6ec40,struct.pack('<IH',99,0xbeef));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x140068160,n.stack+0xf000,count=1000000);actual=bytearray(m.mem_read(n.owner,0xa300))
        for offset in [0x78c8,0x9f38,0xa058]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',actual,p)[0]
                if ptr:struct.pack_into('<Q',actual,p,ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-n.manager-0x608)//64+1)
        wanted=bytes.fromhex(c['state']);assert actual==wanted,(index,[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-player-init-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
