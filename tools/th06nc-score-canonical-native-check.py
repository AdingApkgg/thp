"""Contiguous native score writer 744c2..74aa2 from controlled raw inputs.

Complete encoded file, marker/stat global mutations and RNG are compared.
Rank list allocation is controlled, with default/load semantics proved separately.
Input loading, gameplay stat producers, dirty/destructor gating, filesystem,
and browser integration are excluded; no claim about rank-node mutations.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-canonical','score-header','score-stat-chunks','score-file','score-tables','rng']]
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{encodeCanonicalScore}from'./shared/th06nc/score-canonical.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{createDefaultScoreTables,createHighScoreRecord,insertHighScore}from'./shared/th06nc/score-tables.mjs';
const hex=b=>Buffer.from(b).toString('hex'),cases=[];let state=123456789;const byte=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state&255;};for(let i=0;i<24;i++){const stats=Object.fromEntries(Object.entries({cleared:96,cardAttack:134*384,optionalRecords:96*24,music:16}).map(([k,n])=>[k,Uint8Array.from({length:n},byte)])),c=new DataView(stats.cardAttack.buffer),o=new DataView(stats.optionalRecords.buffer);for(let j=0;j<134;j++)c.setUint32(j*384,(j+i)%3?0x4b544143:0,true);for(let j=0;j<96;j++)o.setBigUint64(j*24+12,(j+i)%4?0xffffffffffffffffn:0n,true);const tables=createDefaultScoreTables();for(let mode=0;mode<3;mode++)for(let difficulty=0;difficulty<5;difficulty++)for(let character=0;character<4;character++)for(let rank=0;rank<i%13;rank++)insertHighScore(tables.get(`${mode}/${difficulty}/${character}`),createHighScoreRecord({score:BigInt(rank%2?0x100000000:1000000),mode,difficulty,character,name:'R'+rank,stage:rank+1}));const seed=(i*4051)&65535,count=i%2?0xffffffff:0,rng=new NativeRng(seed,count),allocation=Uint8Array.from({length:20},byte),marker=Uint8Array.from({length:12},byte),before={stats:Object.fromEntries(Object.entries(stats).map(([k,b])=>[k,hex(b)])),marker:hex(marker),allocation:hex(allocation)},rows=[...tables.values()].map(t=>t.map(hex)),output=encodeCanonicalScore({rng,tables,stats,marker,allocation});cases.push({seed,count,before,rows,output:hex(output),after:{stats:Object.fromEntries(Object.entries(stats).map(([k,b])=>[k,hex(b)])),marker:hex(marker),seed:rng.seed,count:rng.count}});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x400000);digest=hashlib.sha256();total=0
    addresses={'cleared':0x1404ff0f4,'cardAttack':0x1404f27c8,'optionalRecords':0x1404f1e8c,'music':0x1404ff154}
    for i,c in enumerate(cases):
        m.mem_write(n.owner,bytes(0x10000));cursor=heap
        for index,rows in enumerate(c['rows']):
            nodes=[]
            for raw in rows:
                record=cursor;node=cursor+48;cursor+=80;m.mem_write(record,bytes.fromhex(raw));nodes.append((node,record))
            for j,(node,record)in enumerate(nodes):m.mem_write(node,struct.pack('<QQQ',record,0,nodes[j+1][0]if j+1<len(nodes)else 0))
            m.mem_write(n.owner+0x4458+index*24+16,struct.pack('<Q',nodes[0][0]if nodes else 0))
        for key,addr in addresses.items():m.mem_write(addr,bytes.fromhex(c['before']['stats'][key]))
        m.mem_write(n.owner+0x9ea0,bytes.fromhex(c['before']['marker']));m.mem_write(n.assets,bytes(0x20000));m.mem_write(n.assets,bytes.fromhex(c['before']['allocation']));m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']))
        for reg,value in [(UC_X86_REG_RAX,n.assets),(UC_X86_REG_R15,n.owner),(UC_X86_REG_R12,0),(UC_X86_REG_R14,3),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value)
        m.emu_start(0x1400744c2,0x140074aa2,count=3000000)
        assert m.reg_read(UC_X86_REG_RIP)==0x140074aa2,(i,'stop')
        actual=bytes(m.mem_read(n.assets,m.reg_read(UC_X86_REG_EBX)));expected=bytes.fromhex(c['output']);assert actual==expected,(i,'encoded file',len(actual),len(expected));digest.update(actual);total+=len(actual)
        assert bytes(m.mem_read(n.owner+0x9ea0,12))==bytes.fromhex(c['after']['marker']),(i,'marker')
        assert bytes(m.mem_read(0x140a6ec40,6))==struct.pack('<IH',c['after']['count'],c['after']['seed']),(i,'rng')
        for key,addr in addresses.items():
            expected=bytes.fromhex(c['after']['stats'][key]);actual=bytes(m.mem_read(addr,len(expected)));assert actual==expected,(i,key);digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(cases),encodedBytes=total,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-canonical-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'encodedBytes':total}))
if __name__=='__main__':main()
