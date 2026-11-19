"""Custom callback 12 with real saved-laser lookup and shot-origin arithmetic.

Compare complete enemy bytes and ordered ordinary-shot requests. Shared host
sine/cosine; bullet creation, full combat and GPU excluded.
"""
import hashlib,json,struct,subprocess,math
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/ecl-custom-lasers.mjs','shared/th06nc/ecl-custom.mjs','shared/th06nc/ecl-command.mjs'];before={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};script="""
import{applyEclCommand}from'./shared/th06nc/ecl-command.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(const mode of [0,1,2,3])for(const angle of [-Math.PI,-.5,0,.75,Math.PI,2*Math.PI])for(const position of [[100.5,200.25,-2],[-32,16,.49]]){const enemy=Uint8Array.from({length:0x10b0},(_,i)=>i&255),v=new DataView(enemy.buffer),lasers=[],laserBindings=new Map(),events=[];position.forEach((x,k)=>v.setFloat32(0xb0+k*4,x,true));for(let i=0;i<8;i++){const bytes=new Uint8Array(0x298),l=new DataView(bytes.buffer);l.setFloat32(0x260,angle+i*.1,true);l.setUint8(0x274,mode===0?0:mode===1?1:i%2);const pointer=mode===3&&i%2===0?0n:BigInt(i+1);v.setBigUint64(0xf80+i*8,pointer,true);laserBindings.set(BigInt(i+1),{v:l});lasers.push(hex(bytes));}const initial=hex(enemy);const args=new Uint8Array(8);new DataView(args.buffer).setInt32(0,12,true);applyEclCommand(enemy,{opcode:121,args},{gameEnvironment:{},laserBindings,fireBullets:(e,d)=>events.push(hex(d))});cases.push({initial,lasers,after:hex(enemy),events});}console.log(JSON.stringify(cases));
""";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;events=[];digest=hashlib.sha256();laserBase=n.manager+0x10000
    def hook(m,a,size,u):
        if a==0x14000f870:events.append(bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),108)).hex())
        else:
            x=struct.unpack('<f',m.reg_read(UC_X86_REG_XMM0).to_bytes(16,'little')[:4])[0];m.reg_write(UC_X86_REG_XMM0,int.from_bytes(struct.pack('<f',math.cos(x)if a==0x1402be071 else math.sin(x)),'little'))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x14000f870,0x1402be071,0x1402be07d]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        state=bytearray.fromhex(c['initial'])
        for i,raw in enumerate(c['lasers']):
            m.mem_write(laserBase+i*0x298,bytes.fromhex(raw));p=0xf80+i*8;ptr=struct.unpack_from('<Q',state,p)[0]
            if ptr:struct.pack_into('<Q',state,p,laserBase+(ptr-1)*0x298)
        m.mem_write(n.owner,bytes(state));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_R14,n.assets);m.reg_write(UC_X86_REG_RSI,n.assets+12);m.reg_write(UC_X86_REG_R10,0x140000000);m.mem_write(n.assets,struct.pack('<ihH4Bii',0,121,20,0,255,0,0,12,0));events.clear();m.emu_start(0x140028150,0x140025d7d,count=100000);assert events==c['events'],(index,'shot requests');actual=bytearray(m.mem_read(n.owner,0x10b0))
        for i in range(8):
            p=0xf80+i*8;ptr=struct.unpack_from('<Q',actual,p)[0]
            if ptr:struct.pack_into('<Q',actual,p,(ptr-laserBase)//0x298+1)
        wanted=bytes.fromhex(c['after']);assert actual==wanted,(index,'enemy',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,wanted))if a!=b][:30]);digest.update(actual)
    assert before=={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in sources};report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=before,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-custom-lasers-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
