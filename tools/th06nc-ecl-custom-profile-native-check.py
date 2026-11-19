"""ECL 121 custom entry 3: character/shot dependent stage-four local variables.

Actual dispatch and callback execute; whole enemy state compared for all four
profiles and different previous byte patterns. No GPU or full-stage claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-command.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};script="""
import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const character of [0,1])for(const shot of [0,1])for(const word of [0,0xffffffff,0x80000000,0x12345678]){const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);for(let p=0;p<enemy.length;p+=4)v.setUint32(p,word,true);const before=hex(enemy),args=new Uint8Array(8);new DataView(args.buffer).setInt32(0,3,true);applyEclCommand(enemy,{opcode:121,args},{gameEnvironment:{character,shot}});cases.push({character,shot,before,after:hex(enemy)});}console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();m.mem_write(n.assets,struct.pack('<ihH4Bii',0,121,20,0,255,0,0,3,0))
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x1404f1e80,bytes([c['character'],c['shot']]))
        for reg,value in [(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,n.owner),(UC_X86_REG_R14,n.assets),(UC_X86_REG_RSI,n.assets+12),(UC_X86_REG_R10,0x140000000)]:m.reg_write(reg,value)
        m.emu_start(0x140028150,0x140025d7d,count=100000);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],index;digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-custom-profile-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
