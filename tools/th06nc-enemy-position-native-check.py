"""World manager position integration and movement bounds, original x64 phase."""
import hashlib,json,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
def main():
    script="""
import{integrateEnemyPosition}from'./shared/th06nc/enemy-position.mjs';const cases=[];
for(const position of [-100,0,100,400,512])for(const speed of [-10,0,0.25,10])for(const mirror of [false,true])for(const bounds of [null,[0,0,384,448],[100,200,-20,-30]]){
const enemy=new Uint8Array(0x10b0),v=new DataView(enemy.buffer);v.setUint8(0xbc,0x80|(mirror?64:0));if(bounds){v.setUint8(0xbe,1);bounds.forEach((x,i)=>v.setFloat32(0x28+i*4,x,true));}for(let i=0;i<3;i++){v.setFloat32(0xb0+i*4,position+i*2.5,true);v.setFloat32(0x1084+i*4,speed+i*0.25,true);}const before=Buffer.from(enemy).toString('hex');integrateEnemyPosition(enemy);cases.push({before,after:Buffer.from(enemy).toString('hex')});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for index,c in enumerate(cases):
        m.mem_write(n.owner,bytes.fromhex(c['before']));m.reg_write(UC_X86_REG_RBX,n.owner);m.reg_write(UC_X86_REG_RBP,n.owner+0xb0);m.emu_start(0x1400374b1,0x14003757c,count=10000);actual=bytes(m.mem_read(n.owner,0x10b0));assert actual.hex()==c['after'],index;digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/enemy-position.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-enemy-position-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
