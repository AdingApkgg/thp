"""Result resource VM initialization and common animation/counter tail.

Real result/result00..03/difficulty/text ANMs; complete bb48-byte owner
with script/resource/sprite pointer normalization.
Original 7583c, 73e93 and 72743 execute. Controlled state/interrupt requests;
record lists, result dispatch, drawing, loading I/O and full UI excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['result-state','anm-bank','anm-rebind','anm-vm']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ResultState,resultAssets,resultTextAsset,advanceResultCommon}from'./shared/th06nc/result-state.mjs';const refs=[...resultAssets,resultTextAsset],sha=b=>createHash('sha256').update(b).digest('hex'),scenes=[];
for(const interrupt of [0,1,2,3,4,7,10,16])for(const pair of [[0,0],[0,1],[1,1],[9,9],[9,15]]){const bank=new AnmBank();for(const r of refs)bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+r.archive+'/'+r.file)),r.base,{slot:r.slot});const state=new ResultState(bank),initialized=sha(state.bytes),initialBytes=scenes.length===0?Buffer.from(state.bytes).toString('hex'):null,frames=[];state.v.setInt32(0x9e94,pair[1],true);state.v.setInt32(0x4450,2147483600,true);state.v.setInt32(0x4454,70,true);for(let i=0;i<38;i++)state.vm(0xb0+i*288).interrupt(interrupt);for(let i=0;i<5;i++)state.vm(0x3d70+i*288).interrupt(interrupt);for(let frame=1;frame<=120;frame++){advanceResultCommon(state,pair[0]);frames.push(sha(state.bytes));}scenes.push({interrupt,pair,initialized,initialBytes,frames});}console.log(JSON.stringify({refs,scenes}));
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
    for index,s in enumerate(data['scenes']):
        m.mem_write(n.owner,bytes(0xbb48));m.mem_write(n.owner+0x9e7c,struct.pack('<i',1));m.reg_write(UC_X86_REG_RDI,0x7d0);m.reg_write(UC_X86_REG_RBX,n.owner+0x3d70);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000);m.reg_write(UC_X86_REG_R15,n.owner);m.reg_write(UC_X86_REG_R13,0);m.reg_write(UC_X86_REG_R12D,0x798);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140073e93,0x140073ff3,count=1000000);actual=normalized();assert hashlib.sha256(actual).hexdigest()==s['initialized'],(index,'init',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,bytes.fromhex(data['scenes'][0]['initialBytes'])))if a!=b][:25]);digest.update(actual);m.mem_write(n.owner+0x9e94,struct.pack('<i',s['pair'][1]));m.mem_write(n.owner+0x4450,struct.pack('<2i',2147483600,70))
        for offset in [0xb0+i*288 for i in range(38)]+[0x3d70+i*288 for i in range(5)]:m.mem_write(n.owner+offset+0x8a,struct.pack('<h',s['interrupt']))
        for frame,expected in enumerate(s['frames'],1):
            sp=n.stack+0x8000;m.mem_write(sp+0x50,struct.pack('<i',s['pair'][0]));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RSI,n.owner);m.emu_start(0x140072743,0x1400727ef,count=1000000);actual=normalized();assert hashlib.sha256(actual).hexdigest()==expected,(index,frame,'owner');digest.update(actual);checked+=1
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,animationVms=60,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-result-animation-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
