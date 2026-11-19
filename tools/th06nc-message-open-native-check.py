"""Original message open 3ece0, every script ID in all seven files.

Full HUD owner bytes, alias script pointers, projectile pools and special ANM
load requests compared. ANM loading is observed; message execution excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/message.mjs','shared/th06nc/message-open.mjs'];hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readMessage}from'./shared/th06nc/message.mjs';import{openMessage}from'./shared/th06nc/message-open.mjs';import{cancelTimeoutProjectiles}from'./shared/th06nc/projectile-cancel.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex'),hash=b=>createHash('sha256').update(b).digest('hex');
for(let file=1;file<=7;file++){const program=readMessage(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/msg'+file+'.dat'));for(let id=0;id<=program.count;id++)for(const stageIndex of [0,6,7])for(const fill of [0,85]){
 const bytes=new Uint8Array(0x4000).fill(fill),v=new DataView(bytes.buffer),environment={stageIndex};v.setBigUint64(0x38f8,1n,true);v.setBigUint64(0x3b58,1n,true);const bullets=new Uint8Array(640*0x620),lasers=new Uint8Array(64*0x298),b=new DataView(bullets.buffer),l=new DataView(lasers.buffer);for(let s=0;s<640;s++)b.setUint16(s*0x620+0x44,s%6,true);for(let s=0;s<64;s++){const p=s*0x298;l.setUint8(p+0x274,s%2);l.setUint8(p+0x290,s%3);l.setInt32(p,123,true);l.setInt32(p+8,12,true);l.setInt32(p+0xc,13,true);}const loads=[];let cancels=0;const result=openMessage({bytes,v,program},id,{environment,loadAnm:r=>loads.push(r),cancelProjectiles:()=>{cancels++;cancelTimeoutProjectiles({bullets,lasers});}});cases.push({file,id,stageIndex,fill,result,cancels,loads,after:hex(bytes),bullets:hash(bullets),lasers:hash(lasers)});
}}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;loads=[];digest=hashlib.sha256()
    def hook(m,a,size,u):
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        else:
            ptr=m.reg_read(UC_X86_REG_R8);name=bytes(m.mem_read(ptr,64)).split(b'\0')[0].decode().split('/')[-1];loads.append(dict(archive='th06ST.dat',file=name,slot=m.reg_read(UC_X86_REG_EDX),base=m.reg_read(UC_X86_REG_R9D)))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1400020b0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    current=None
    for index,c in enumerate(cases):
        if current!=c['file']:
            current=c['file'];raw=(ROOT/f'runtimes/th06nc/artifacts/scripts/th06ST.dat/msg{current}.dat').read_bytes();m.mem_write(n.assets,raw);count=struct.unpack_from('<I',raw)[0]
            for i in range(count):m.mem_write(n.vm+i*8,struct.pack('<Q',n.assets+struct.unpack_from('<I',raw,4+i*4)[0]))
        initial=bytearray([c['fill']])*0x4000;struct.pack_into('<Q',initial,0x38f8,n.assets);struct.pack_into('<Q',initial,0x3b58,n.vm);m.mem_write(n.owner,bytes(initial));m.mem_write(0x1404f1e84,struct.pack('<i',c['stageIndex']));bullets=bytearray(640*0x620);lasers=bytearray(64*0x298)
        for s in range(640):struct.pack_into('<H',bullets,s*0x620+0x44,s%6)
        for s in range(64):
            p=s*0x298;lasers[p+0x274]=s%2;lasers[p+0x290]=s%3;struct.pack_into('<i',lasers,p,123);struct.pack_into('<2i',lasers,p+8,12,13)
        m.mem_write(0x1403ec2a8,bytes(bullets));m.mem_write(0x1404e12b8,bytes(lasers));loads.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_EDX,c['id']);m.emu_start(0x14003ece0,n.stack+0xf000,count=1000000);actual=bytearray(m.mem_read(n.owner,0x4000));struct.pack_into('<Q',actual,0x38f8,1);struct.pack_into('<Q',actual,0x3b58,1)
        if c['result']:struct.pack_into('<Q',actual,0x3668,struct.unpack_from('<Q',actual,0x3668)[0]-n.assets)
        wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,c['file'],c['id'],[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);assert loads==c['loads'],(index,loads,c['loads']);assert hashlib.sha256(m.mem_read(0x1403ec2a8,len(bullets))).hexdigest()==c['bullets'];assert hashlib.sha256(m.mem_read(0x1404e12b8,len(lasers))).hexdigest()==c['lasers'];digest.update(actual)
    assert hashes=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources}
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-message-open-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
