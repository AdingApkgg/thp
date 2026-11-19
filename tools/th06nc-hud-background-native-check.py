"""HUD frame initialization, priority-12 frame tick and ordinary background draw.

Real frame.anm with complete owner storage. Draw/camera/cover requests are
observed boundaries; native screenshot overlay and GPU pixels are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['hud-background','message-state','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{MessageState}from'./shared/th06nc/message-state.mjs';import{hudFrameAsset,initializeHudBackground,advanceHudBackground,drawHudBackground}from'./shared/th06nc/hud-background.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');
for(const hidden of [false,true])for(const color of [0,0x80402010,0xffffff]){
 const bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06CM.dat/frame.anm')),hudFrameAsset.base,{slot:hudFrameAsset.slot});const state=new MessageState({uniqueScripts:[]},{anmBank:bank,storage:new Uint8Array(0x4228)}),before=hex(state.bytes);initializeHudBackground(state);const initialized=hex(state.bytes),frames=[];
 for(let frame=1;frame<=120;frame++){advanceHudBackground(state);const calls=[];drawHudBackground(state,(vm,r)=>calls.push({kind:'draw',offset:r.offset,state:hex(vm.state)}),{hidden,color,setupCamera:r=>calls.push({kind:'camera',...r}),drawCover:r=>calls.push({kind:'cover',...r})});if([1,2,15,30,60,90,120].includes(frame))frames.push({frame,state:hex(state.bytes),calls});}scenes.push({hidden,color,before,initialized,frames});
}console.log(JSON.stringify(scenes));
"""
    scenes=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([dict(archive='th06CM.dat',file='frame.anm',slot=54,base=0x779)]);calls=[];digest=hashlib.sha256();checked=0
    def normalize(raw):
        raw=bytearray(raw)
        for offset in [0x31e0,0x480,0x5a0,0x3300]:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-n.assets)
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==0x140002a80:
            ptr=m.reg_read(UC_X86_REG_RDX);assert m.reg_read(UC_X86_REG_R8)&255==255 and m.reg_read(UC_X86_REG_R9)&255==255 and bytes(m.mem_read(sp+0x28,1))==b'\1';calls.append(dict(kind='draw',offset=ptr-n.owner,state=normalize(bytes(m.mem_read(n.owner,0x4228)))[ptr-n.owner:ptr-n.owner+288].hex()))
        elif a==0x14007b120:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0]))
        elif a==0x140075be0:calls.append(dict(kind='cover',rect=list(struct.unpack('<4f',m.mem_read(m.reg_read(UC_X86_REG_RCX),16))),color=m.reg_read(UC_X86_REG_EDX)))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x140002a80,0x14007b120,0x140075be0,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,s in enumerate(scenes):
        m.mem_write(n.owner,bytes.fromhex(s['before']));m.mem_write(n.vm+0x38,struct.pack('<Q',n.owner));m.reg_write(UC_X86_REG_RBX,n.vm);m.reg_write(UC_X86_REG_R10,n.manager);m.reg_write(UC_X86_REG_R13D,0x779);m.reg_write(UC_X86_REG_EDI,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003dbdf,0x14003dcc3,count=1000000);assert normalize(bytes(m.mem_read(n.owner,0x4228))).hex()==s['initialized'],(index,'init')
        m.mem_write(0x140c21dc0,bytes([0x10 if s['hidden'] else 0]));m.mem_write(0x140509ba0,struct.pack('<I',s['color']));m.mem_write(0x140a6ec64,b'\0');byFrame={c['frame']:c for c in s['frames']}
        for frame in range(1,121):
            m.reg_write(UC_X86_REG_RCX,n.vm);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003fcdc,0x14003fcf6,count=1000000);calls.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.vm);m.emu_start(0x1400415d0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
            if frame not in byFrame:continue
            c=byFrame[frame];actual=normalize(bytes(m.mem_read(n.owner,0x4228)));assert actual.hex()==c['state'],(index,frame,'state');assert calls==c['calls'],(index,frame,calls,c['calls']);digest.update(actual);checked+=1
    assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}==hashes;report=dict(scope=__doc__,scenes=len(scenes),frames=len(scenes)*120,checkpoints=checked,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-hud-background-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
