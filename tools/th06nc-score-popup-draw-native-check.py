"""Numeric popup font init 9790 and draw 92a0, original ASCII ANM sprites.

Shared font VM and every observed draw compared, including caption UV changes,
reverse digits, small ring, colors and inactive entries. GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/score-popup-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ScorePopupPool}from'./shared/th06nc/score-popup-pool.mjs';import{createScorePopupFont,drawScorePopups,scorePopupAssetPlan}from'./shared/th06nc/score-popup-draw.mjs';const ref=scorePopupAssetPlan(),bank=new AnmBank(),cases=[],hex=b=>Buffer.from(b).toString('hex');bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});for(const value of [-1,0,1,10,12800,2147483647])for(const color of [0xffffffff,0xff80c0ff,0x00abcdef])for(const active of [false,true]){const pool=new ScorePopupPool(),font=createScorePopupFont(bank),initial=hex(font.state);for(const [slot,small]of [[0,false],[1,false],[512,true]]){if(small)pool.publishSmall({position:[100.5,200.25,.5],value});else pool.publish({position:[100.5+slot,200.25,.5],value,color});if(!active)pool.storage[slot*40+0x1c]=0;}const calls=[];drawScorePopups(pool,font,(vm,{snap})=>calls.push({snap,state:hex(vm.state)}),{anmBank:bank});cases.push({value,color,active,initial,pool:hex(pool.storage),calls,after:hex(font.state)});}console.log(JSON.stringify({ref,cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title([data['ref']]);m=n.m;calls=[];digest=hashlib.sha256()
    def normalize(state):
        ptr=struct.unpack_from('<Q',state,0x100)[0]
        if ptr:struct.pack_into('<Q',state,0x100,(ptr-n.manager-0x608)//64+1)
    def hook(m,a,size,u):
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        elif a==0x1400067f0:
            state=bytearray(m.mem_read(m.reg_read(UC_X86_REG_RDX),288));normalize(state);calls.append(dict(snap=bool(m.reg_read(UC_X86_REG_R8B)),state=state.hex()))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1400067f0,0x14007af40]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    def run(addr):
        sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(addr,n.stack+0xf000,count=1000000)
    for index,c in enumerate(data['cases']):
        m.mem_write(n.owner,bytes(0x10000));run(0x140009790);state=bytearray(m.mem_read(n.owner+0x130,288));normalize(state);assert state.hex()==c['initial'],(index,'font init',[(hex(p),a,b)for p,(a,b)in enumerate(zip(state,bytes.fromhex(c['initial'])))if a!=b]);m.mem_write(n.owner+0x250,bytes.fromhex(c['pool']));calls.clear();run(0x1400092a0);assert calls==c['calls'],(index,'draw',calls[:1],c['calls'][:1]);state=bytearray(m.mem_read(n.owner+0x130,288));normalize(state);assert state.hex()==c['after'],(index,'font after');assert bytes(m.mem_read(n.owner+0x250,515*40)).hex()==c['pool'];digest.update(state)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(data['cases']),drawCalls=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-popup-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
