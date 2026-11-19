"""Actual 747a4..74a3a non-HSCR score chunk writer.

Compares complete output plus every mutated raw global owner. Synthetic owners
exercise filtering, index rewrites, preserved payload/padding and nonzero uint64
selection. Loading, gameplay stat producers, whole writer and browser excluded;
the optional 24-byte record owner's gameplay meaning is not inferred.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/score-stat-chunks.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{serializeScoreStatChunks}from'./shared/th06nc/score-stat-chunks.mjs';
const cases=[],hex=b=>Buffer.from(b).toString('hex');let state=123456789;const byte=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state&255;};
for(let i=0;i<32;i++){const owners=Object.fromEntries(Object.entries({cleared:96,cardAttack:134*384,optionalRecords:96*24,music:16}).map(([k,n])=>[k,Uint8Array.from({length:n},byte)]));const c=new DataView(owners.cardAttack.buffer),o=new DataView(owners.optionalRecords.buffer);for(let j=0;j<134;j++)c.setUint32(j*384,(i===0||i>1&&(j+i)%3!==0)?0x4b544143:0,true);for(let j=0;j<96;j++)o.setBigUint64(j*24+12,i===1||i>1&&(j+i)%4===0?0n:[1n,0x8000000000000000n,0xffffffffffffffffn][j%3],true);const before=Object.fromEntries(Object.entries(owners).map(([k,b])=>[k,hex(b)])),records=serializeScoreStatChunks(owners);cases.push({before,after:Object.fromEntries(Object.entries(owners).map(([k,b])=>[k,hex(b)])),output:hex(Buffer.concat(records)),records:records.length});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();total=0
    addresses={'cleared':0x1404ff0f4,'cardAttack':0x1404f27c8,'optionalRecords':0x1404f1e8c,'music':0x1404ff154}
    for i,c in enumerate(cases):
        for key,addr in addresses.items():m.mem_write(addr,bytes.fromhex(c['before'][key]))
        m.mem_write(n.assets,bytes(0x20000))
        for reg,value in [(UC_X86_REG_RBP,n.assets),(UC_X86_REG_EBX,32),(UC_X86_REG_R12,0),(UC_X86_REG_R14,3),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x1400747a4,0x140074a3a,count=1000000)
        assert m.reg_read(UC_X86_REG_RIP)==0x140074a3a,(i,'stop')
        actual=bytes(m.mem_read(n.assets+32,m.reg_read(UC_X86_REG_EBX)-32));assert actual==bytes.fromhex(c['output']),(i,'output',len(actual),len(bytes.fromhex(c['output'])))
        digest.update(actual);total+=c['records']
        for key,addr in addresses.items():
            expected=bytes.fromhex(c['after'][key]);actual=bytes(m.mem_read(addr,len(expected)));assert actual==expected,(i,key);digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),emittedRecords=total,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-stat-chunks-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'emittedRecords':total}))
if __name__=='__main__':main()
