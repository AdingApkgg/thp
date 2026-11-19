"""Result summary states 15/16, full native dispatcher tick and common tail.

Real result/result00..03/difficulty/text ANMs; complete bb48-byte owner
with script/resource/sprite pointer normalization.
Original 7583c, 73e93 and 6e3a0 execute. Controlled state/input requests;
record lists, other dispatcher states, drawing, loading I/O and full UI excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['result-summary','result-state','anm-bank','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{advanceResultSummary}from'./shared/th06nc/result-summary.mjs';import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ResultState,resultAssets,resultTextAsset,advanceResultCommon}from'./shared/th06nc/result-state.mjs';const refs=[...resultAssets,resultTextAsset],sha=b=>createHash('sha256').update(b).digest('hex'),scenes=[];
for(const kind of [15,16])for(const clock of [-1,0,29,30,31,89,90,91,2147483647])for(const held of [0,256,512,768])for(const previous of [0,256,512,768]){const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new ResultState(bank),initialized=sha(state.bytes),initialBytes=scenes.length===0?Buffer.from(state.bytes).toString('hex'):null;state.v.setInt32(0x9e94,kind,true);state.v.setInt32(0x4450,clock,true);state.v.setInt32(0x4454,70,true);advanceResultSummary(state,{held,previous});advanceResultCommon(state,kind);scenes.push({kind,clock,held,previous,initialized,initialBytes,expected:sha(state.bytes)});}console.log(JSON.stringify({refs,scenes}));
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
        m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['initialized'],(index,'init',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,bytes.fromhex(data['scenes'][0]['initialBytes'])))if a!=b][:25]);digest.update(actual);m.mem_write(n.owner+0x9e94,struct.pack('<i',s['kind']));m.mem_write(n.owner+0x4450,struct.pack('<2i',s['clock'],70));m.mem_write(0x140a6ec60,struct.pack('<2I',s['held'],s['previous']))
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14006e3a0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['expected'],(index,s,'owner');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,animationVms=60,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-summary-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
