"""Boot music and contiguous title stats load into actual shared globals.

Complete 4f1e8c..4ff164 span compares after boot and after 55f9a..560be.
Includes PSCR writes into CATK's first slot and the resulting initialization
gate, initialized/partial/zero globals, and readonly original score.dat.
memset is controlled. Gameplay producers, result lifecycle and browser excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-stats','score-stat-load','score-file','spell-record']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createScoreChunk,decodeScoreFile}from'./shared/th06nc/score-file.mjs';import{ScoreStats}from'./shared/th06nc/score-stats.mjs';
const hex=b=>Buffer.from(b).toString('hex'),cases=[];let state=123456789;const byte=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state&255;};for(let i=0;i<16;i++){const records=[],initial=i%4?Uint8Array.from({length:0xd2d8},byte):new Uint8Array(0xd2d8);if(i%4===2)new DataView(initial.buffer).setUint32(0x93c,0x4b544143,true);if(i===15)records.push(...decodeScoreFile(readFileSync('H:/Games/th/06nc/score.dat')).records);else if(i){for(let j=0;j<8;j++){const c=createScoreChunk('CATK',384);for(let k=9;k<c.length;k++)c[k]=byte();new DataView(c.buffer).setUint16(16,j*17,true);records.push(c);}const p=createScoreChunk('PSCR',24);p[20]=3;p[21]=i%5;p[22]=6;new DataView(p.buffer).setUint32(12,0x4b544143,true);records.push(p);const c=createScoreChunk('CLRD',24);c[22]=i%4;c[12]=i;records.push(c);const m=createScoreChunk('MUSC',16);m[12]=i;records.push(m);}const owner=new ScoreStats(initial);owner.loadBoot(records);const boot=hex(owner.bytes);owner.loadTitle(records);cases.push({initial:hex(initial),records:records.map(hex),boot,title:hex(owner.bytes)});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    def memset(m,a,size,u):
        dst=m.reg_read(UC_X86_REG_RCX);count=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([m.reg_read(UC_X86_REG_RDX)&255])*count);m.reg_write(UC_X86_REG_RAX,dst);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,memset,begin=0x1402bdee2,end=0x1402bdee2)
    for i,c in enumerate(cases):
        body=b''.join(bytes.fromhex(r)for r in c['records']);m.mem_write(n.assets,struct.pack('<6I',24,0,0,0,len(body)+24,0)+body);m.mem_write(0x1404f1e8c,bytes.fromhex(c['initial']));m.reg_write(UC_X86_REG_RSI,n.assets);m.reg_write(UC_X86_REG_XMM0,0);m.emu_start(0x140045776,0x1400457cd,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x1400457cd,(i,'boot stop');actual=bytes(m.mem_read(0x1404f1e8c,0xd2d8));assert actual==bytes.fromhex(c['boot']),(i,'boot globals');digest.update(actual)
        for reg,value in [(UC_X86_REG_R14,n.assets),(UC_X86_REG_R15,0),(UC_X86_REG_R9,0x1404ff0f4),(UC_X86_REG_ECX,0),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x140055f9a,0x1400560be,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x1400560be,(i,'title stop');actual=bytes(m.mem_read(0x1404f1e8c,0xd2d8));assert actual==bytes.fromhex(c['title']),(i,'title globals');digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(cases),completeGlobalComparisons=2*len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-stats-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'globalComparisons':2*len(cases)}))
if __name__=='__main__':main()
