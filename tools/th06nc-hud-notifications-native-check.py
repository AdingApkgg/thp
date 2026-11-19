"""HUD notification update 3fffb and full draw/queue block 3d0cd..3d34d.

Boss Bonus/Full Power/Spell Card Bonus: full HUD bytes and entire ASCII
manager queue, native UCRT formatting, scales/colors/camera, expiry/overflow
and 255/256-entry capacity. Publishers and GPU rasterization excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-notifications','ascii-text','score-popup-draw']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{createAsciiTextState,enqueueAsciiText}from'./shared/th06nc/ascii-text.mjs';import{bindHudPopup,advanceHudNotifications,drawHudNotifications}from'./shared/th06nc/hud-notifications.mjs';const hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex'),bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/ascii.anm')),0,{slot:1});const scenes=[];
for(const frame of [-1,0,29,30,179,180,249,250,279,280,2147483647])for(let mask=0;mask<8;mask++)for(const value of [-1,0,2147483647])for(const cursor of [0,255,256]){
 const bytes=new Uint8Array(0x4228),state={bytes,v:new DataView(bytes.buffer)},boss={},env={},spell={};bindHudPopup(state,boss,'bonusPopup',0x6c0);bindHudPopup(state,env,'powerPopup',0x6dc);bindHudPopup(state,spell,'bonusPopup',0x6f8);for(const [target,key,active,position]of[[boss,'bonusPopup',mask&1,[620,32,.2]],[env,'powerPopup',mask&2,[620,232,.3]],[spell,'bonusPopup',mask&4,[428,16,.4]]])target[key]={previous:-999,frame,active:Boolean(active),position,value};const before=hex(bytes),font=createAsciiTextState(bank);font.v.setInt32(0x7bb0,cursor,true);advanceHudNotifications(state);drawHudNotifications(state,request=>enqueueAsciiText(font,request));scenes.push({frame,mask,value,cursor,before,after:hex(bytes),fontSha256:sha(font.bytes),count:font.v.getInt32(0x7bb0,true)});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06IN.dat',file='ascii.anm',slot=1,base=0)]);digest=hashlib.sha256();fontBase=0x1403de620;shim=n.vm+0x9000;m.mem_write(shim,b'\xc3');m.mem_write(0x1402c0528,struct.pack('<Q',shim));crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p]
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==shim:
            fmt=bytes(m.mem_read(m.reg_read(UC_X86_REG_R9),100)).split(b'\0')[0];assert fmt in [b'BONUS %8d',b'Full Power Mode!!',b'Spell Card Bonus!',b'+%d'];va=struct.unpack('<Q',m.mem_read(sp+0x30,8))[0];argument=ctypes.c_uint64(struct.unpack('<Q',m.mem_read(va,8))[0]);out=ctypes.create_string_buffer(512);length=formatter(m.reg_read(UC_X86_REG_RCX),out,512,fmt,None,ctypes.byref(argument));assert length>=0;m.mem_write(m.reg_read(UC_X86_REG_RDX),out.value+b'\0');m.reg_write(UC_X86_REG_RAX,length)
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1402bcf20,shim]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(address,rcx):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
    for index,s in enumerate(scenes):
        m.mem_write(n.owner,bytes.fromhex(s['before']));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_RDI,0xffffffffffffffff);m.reg_write(UC_X86_REG_EBP,0);m.emu_start(0x14003fffb,0x1400401a0,count=1000000);m.mem_write(fontBase,bytes(0xdbb8));run(0x140009790,fontBase);m.mem_write(fontBase+0x7bb0,struct.pack('<i',s['cursor']));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.reg_write(UC_X86_REG_RDI,n.vm);m.reg_write(UC_X86_REG_R14,fontBase);m.reg_write(UC_X86_REG_RBP,n.stack+0x8200);m.reg_write(UC_X86_REG_XMM7,struct.unpack('<I',struct.pack('<f',16))[0]);m.emu_start(0x14003d0cd,0x14003d34d,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x14003d34d;actual=bytes(m.mem_read(n.owner,0x4228));assert actual.hex()==s['after'],(index,'owner',[(hex(p),a,b)for p,(a,b)in enumerate(zip(actual,bytes.fromhex(s['after'])))if a!=b][:16]);font=bytearray(m.mem_read(fontBase,0xdbb8))
        for offset in [0x10,0x130]:
            p=offset+0x100;ptr=struct.unpack_from('<Q',font,p)[0]
            if ptr:struct.pack_into('<Q',font,p,(ptr-n.manager-0x608)//64+1)
        assert hashlib.sha256(font).hexdigest()==s['fontSha256'],(index,'font queue',struct.unpack_from('<i',font,0x7bb0)[0],s['count']);digest.update(actual);digest.update(font)
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-notifications-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
