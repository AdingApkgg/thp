"""Result closing state 2 and task termination, full native dispatcher tick and common tail.

Real result/result00..03/difficulty/text ANMs; complete bb48-byte owner
with script/resource/sprite pointer normalization.
Original 7583c, 73e93 and 6e3a0 execute. Controlled state/input requests;
Real native fade requests/tick and supervisor game-state request; file writes and drawing excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['result-exit','fade','result-state','anm-bank','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{advanceResultExit}from'./shared/th06nc/result-exit.mjs';import{NativeFade}from'./shared/th06nc/fade.mjs';import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ResultState,resultAssets,resultTextAsset,advanceResultCommon}from'./shared/th06nc/result-state.mjs';const refs=[...resultAssets,resultTextAsset],sha=b=>createHash('sha256').update(b).digest('hex'),scenes=[];
for(const standalone of [false,true])for(const clock of [-1,0,29,30,31])for(const alpha of [0,128,255]){const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new ResultState(bank),initialized=sha(state.bytes),initialBytes=scenes.length===0?Buffer.from(state.bytes).toString('hex'):null,fade=new NativeFade(),frames=[];state.v.setInt32(0x9e94,2,true);state.v.setInt32(0x4450,clock,true);state.v.setInt32(0x4454,70,true);state.v.setUint8(0x9e9a,Number(standalone));fade.v.setInt32(0x28,alpha,true);fade.v.setInt32(0x34,alpha===255?2:0,true);for(let frame=1;frame<=100;frame++){fade.tick();const event=advanceResultExit(state,fade);if(!event)advanceResultCommon(state,2);frames.push({ownerSha256:sha(state.bytes),fadeSha256:sha(fade.state),event});if(event)break;}scenes.push({standalone,clock,alpha,initialized,initialBytes,frames});}console.log(JSON.stringify({refs,scenes}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);offsets=[0xb0+i*288 for i in range(38)]+[0x2b70+i*288 for i in range(16)]+[0x3d70+i*288 for i in range(5)]+[0x4310];digest=hashlib.sha256();checked=0
    def normalized():
        raw=bytearray(m.mem_read(n.owner,0xbb48))
        for offset in offsets:
            for field in [0xf0,0xf8]:
                p=offset+field;ptr=struct.unpack_from('<Q',raw,p)[0]
                if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
            p=offset+0x100;ptr=struct.unpack_from('<Q',raw,p)[0]
            if ptr:struct.pack_into('<Q',raw,p,(ptr-n.manager-0x608)//64+1)
        return bytes(raw)
    def hook(m,a,size,u):
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,hook,begin=0x1402bcf20,end=0x1402bcf20)
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['initialized'],(index,'init',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,bytes.fromhex(data['scenes'][0]['initialBytes'])))if a!=b][:25]);digest.update(actual);m.mem_write(n.owner+0x9e94,struct.pack('<i',2));m.mem_write(n.owner+0x4450,struct.pack('<2i',s['clock'],70));m.mem_write(n.owner+0x9e9a,bytes([s['standalone']]));fade=n.vm+0x1000;m.mem_write(0x140c22158,struct.pack('<Q',fade));m.mem_write(fade,bytes(56));m.mem_write(fade+0x28,struct.pack('<i',s['alpha']));m.mem_write(fade+0x34,struct.pack('<i',2 if s['alpha']==255 else 0));m.mem_write(0x140c21d9c,bytes(4))
        for frame,c in enumerate(s['frames'],1):
            for address,rcx in [(0x140075af0,fade),(0x14006e3a0,n.owner)]:
                sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
            actual=normalized();assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,frame,'owner');assert hashlib.sha256(bytes(m.mem_read(fade,56))).hexdigest()==c['fadeSha256'],(index,frame,'fade');assert m.reg_read(UC_X86_REG_EAX)==(0 if c['event']else 1),(index,frame,'return');assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==(1 if c['event']and not s['standalone']else 0),(index,frame,'gameState');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,animationVms=60,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-exit-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
