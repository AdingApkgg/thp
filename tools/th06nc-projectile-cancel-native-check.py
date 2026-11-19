"""Boss-death projectile conversion: all bullet/laser slots and score requests.

Original inline conversion block executes. Floating score labels are observed;
projectile movement, collision, lifetime after cancellation and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    script="""
import{createHash}from'node:crypto';import{cancelBossProjectiles,bulletBytes,bulletCapacity,laserBytes,laserCapacity}from'./shared/th06nc/projectile-cancel.mjs';const cases=[],hash=b=>createHash('sha256').update(b).digest('hex');
for(const active of [0,1,2,7,639,640])for(const state of [1,5,65535]){
 const bullets=new Uint8Array(bulletBytes*bulletCapacity),lasers=new Uint8Array(laserBytes*laserCapacity),b=new DataView(bullets.buffer),l=new DataView(lasers.buffer),events=[];
 for(let i=0;i<bulletCapacity;i++){const p=i*bulletBytes;b.setUint16(p+0x44,i<active?state:0,true);[i+0.5,i*2+0.25,-i].forEach((x,k)=>b.setFloat32(p+0x30+k*4,x,true));}
 for(let i=0;i<laserCapacity;i++){const p=i*laserBytes;l.setUint8(p+0x274,i%3);l.setUint8(p+0x290,[0,1,2,3,255][i%5]);l.setInt32(p,444,true);l.setInt32(p+8,-17,true);l.setInt32(p+0xc,42,true);}
 const score=cancelBossProjectiles({bullets,lasers,publishScore:e=>events.push(e)});cases.push({active,state,score,events,bulletSha256:hash(bullets),laserSha256:hash(lasers)});
}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();bulletBase=0x1403ec2a8;laserBase=0x1404e12b8
    def hook(m,a,size,u):
        if a!=0x140009bd0:return
        events.append(dict(position=list(struct.unpack('<3f',m.mem_read(m.reg_read(UC_X86_REG_RDX),12))),value=m.reg_read(UC_X86_REG_R8D),color=m.reg_read(UC_X86_REG_R9D)));sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RAX,0);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook)
    for index,c in enumerate(cases):
        bullets=bytearray(640*0x620);lasers=bytearray(64*0x298)
        for i in range(640):p=i*0x620;struct.pack_into('<H',bullets,p+0x44,c['state']if i<c['active']else 0);struct.pack_into('<3f',bullets,p+0x30,i+0.5,i*2+0.25,-float(i))
        for i in range(64):p=i*0x298;lasers[p+0x274]=i%3;lasers[p+0x290]=[0,1,2,3,255][i%5];struct.pack_into('<i',lasers,p,444);struct.pack_into('<2i',lasers,p+8,-17,42)
        m.mem_write(bulletBase,bytes(bullets));m.mem_write(laserBase,bytes(lasers));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_R14,0);events.clear();m.emu_start(0x140037daa,0x140037e5f,count=100000)
        assert m.reg_read(UC_X86_REG_R14D)==c['score'],(index,'score');assert events==c['events'],(index,'events');actual=bytes(m.mem_read(bulletBase,len(bullets)));assert hashlib.sha256(actual).hexdigest()==c['bulletSha256'],(index,'bullets');digest.update(actual);actual=bytes(m.mem_read(laserBase,len(lasers)));assert hashlib.sha256(actual).hexdigest()==c['laserSha256'],(index,'lasers');digest.update(actual)
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/projectile-cancel.mjs').read_bytes()).hexdigest(),executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-projectile-cancel-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
