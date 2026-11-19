"""Native 6a8c0 bomb-area query, all slots and float edge comparisons.

Includes disabled widths, touching boundaries, negative and nonfinite fields.
No projectile motion or conversion behavior is claimed by this query check.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/player-bomb-cancel.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{queryPlayerBombCancel}from'./shared/th06nc/player-bomb-cancel.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const slot of [0,7,15])for(const width of [0,-0,48,-48,Infinity,-Infinity,NaN])for(const height of [0,32,-32,NaN])for(const x of [100,NaN])for(const rect of [[76,84,124,116],[124,116,124,116],[125,117,130,140],[75,70,75,70],[NaN,80,110,120]]){const bytes=new Uint8Array(256),v=new DataView(bytes.buffer);[width,height,x,100].forEach((n,i)=>v.setFloat32(slot*16+i*4,n,true));const query=new Uint8Array(16),q=new DataView(query.buffer);rect.forEach((n,i)=>q.setFloat32(i*4,n,true));const player={v:new DataView(new ArrayBuffer(0x7854))};new Uint8Array(player.v.buffer).set(bytes,0x7754);cases.push({bytes:hex(bytes),query:hex(query),result:queryPlayerBombCancel(player,{left:rect[0],top:rect[1],right:rect[2],bottom:rect[3]})});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for i,c in enumerate(cases):
        raw=bytes.fromhex(c['bytes']);query=bytes.fromhex(c['query']);m.mem_write(n.owner+0x7754,raw);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.assets));m.mem_write(sp+0x28,query[12:16]);m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner)
        for reg,p in [(UC_X86_REG_XMM1,0),(UC_X86_REG_XMM2,4),(UC_X86_REG_XMM3,8)]:m.reg_write(reg,int.from_bytes(query[p:p+4],'little'))
        m.emu_start(0x14006a8c0,n.assets,count=1000);assert m.reg_read(UC_X86_REG_RIP)==n.assets;assert bool(m.reg_read(UC_X86_REG_AL))==c['result'],(i,c);assert bytes(m.mem_read(n.owner+0x7754,256))==raw;digest.update(bytes([int(c['result'])]))
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),resultSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-bomb-cancel-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
