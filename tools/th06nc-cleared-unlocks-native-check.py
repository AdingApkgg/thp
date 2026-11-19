"""Native title Extra availability and per-shot clear checks, all 4096 masks.

Executes 4818b..481fc and each 4b958..4b986 comparison block. Exact 99 values,
all twelve eligible markers, ignored Easy/Extra/secondary markers, selection
and pulse results compare. Remaining menu update/ANM/browser are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/cleared-unlocks.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{clearedUnlocks}from'./shared/th06nc/cleared-unlocks.mjs';const cases=[];for(let mask=0;mask<4096;mask++){const bytes=new Uint8Array(96).fill(99);for(let p=0;p<4;p++)for(let d=1;d<=3;d++)bytes[p*24+12+d]=(mask&(1<<(p*3+d-1)))?99:[0,1,98,100,255][(mask+p+d)%5];cases.push({bytes:Buffer.from(bytes).toString('hex'),...clearedUnlocks(bytes)});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for i,c in enumerate(cases):
        m.mem_write(0x1404ff0f4,bytes.fromhex(c['bytes']));m.mem_write(n.owner+0x28,struct.pack('<i',1));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_EAX,1);m.emu_start(0x14004818b,0x1400481fc,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x1400481fc;available=struct.unpack('<i',m.mem_read(n.owner+0x28,4))[0]==1;assert available==c['extraAvailable'],(i,'global');digest.update(bytes([available]))
        for p in range(4):
            shot=p&1;unlocked=c['extraUnlockedShots'][p>>1][shot];m.mem_write(n.owner+0x28,struct.pack('<2i',shot,123));m.reg_write(UC_X86_REG_R12,0x140000000);m.reg_write(UC_X86_REG_RCX,p*3);m.reg_write(UC_X86_REG_EDX,shot);m.reg_write(UC_X86_REG_EBP,0);m.emu_start(0x14004b958,0x14004b986,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x14004b986;selection,pulse=struct.unpack('<2i',m.mem_read(n.owner+0x28,8));assert selection==(shot if unlocked else 1-shot)and pulse==(123 if unlocked else 0),(i,p,'shot');digest.update(struct.pack('<2i',selection,pulse))
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),comparisonBlocks=len(cases)*5,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-cleared-unlocks-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
