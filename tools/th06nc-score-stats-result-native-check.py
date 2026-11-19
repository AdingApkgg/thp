"""Actual Result 7430c..74457 loading gates and practice best update.

Complete shared global span compares for state 9/17 and other states, all
profiles/stages/difficulties, unsigned score edges and readonly original chunks.
Existing globals and decoded input are controlled. Real CATK/CLRD/PSCR code
executes together; result scene construction, gameplay and persistence excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-stats','score-stat-load','score-file','spell-record']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{decodeScoreFile}from'./shared/th06nc/score-file.mjs';import{ScoreStats}from'./shared/th06nc/score-stats.mjs';
const hex=b=>Buffer.from(b).toString('hex'),original=decodeScoreFile(readFileSync('H:/Games/th/06nc/score.dat')).records,cases=[];let r=123456789;const byte=()=>{r^=r<<13;r^=r>>>17;r^=r<<5;return r&255;};for(let profile=0;profile<4;profile++)for(let stage=1;stage<=6;stage++)for(let difficulty=0;difficulty<4;difficulty++)for(const state of [0,9,17]){const n=cases.length,initial=Uint8Array.from({length:0xd2d8},byte),p=((profile*6+stage-1)*4+difficulty)*24+12,edges=[0n,1n,0x7fffffffffffffffn,0x8000000000000000n,0xffffffffffffffffn],previous=edges[n%5],score=edges[(n*3)%5];new DataView(initial.buffer).setBigUint64(p,previous,true);const owner=new ScoreStats(initial),environment={state,character:profile>>1,shot:profile&1,stage,difficulty,score:String(score)},records=n%2?original:[];owner.loadResult(records,environment);cases.push({initial:hex(initial),original:Boolean(n%2),environment,expected:hex(owner.bytes)});}console.log(JSON.stringify({original:original.map(hex),cases}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for i,c in enumerate(data['cases']):
        body=b''.join(bytes.fromhex(r)for r in data['original'])if c['original']else b'';m.mem_write(n.assets,struct.pack('<6I',24,0,0,0,len(body)+24,0)+body);m.mem_write(0x1404f1e8c,bytes.fromhex(c['initial']));e=c['environment'];m.mem_write(n.owner+0x4440,struct.pack('<Q',n.assets));m.mem_write(n.owner+0x9e94,struct.pack('<i',e['state']));m.mem_write(0x1404f1e80,bytes([e['character'],e['shot']]));m.mem_write(0x1404f1e84,struct.pack('<i',e['stage']));m.mem_write(0x1404f27c0,struct.pack('<i',e['difficulty']));m.mem_write(0x1404f2798,struct.pack('<Q',int(e['score'])))
        # Environment fields live inside the compared span; mirror those
        # explicit native input writes in the expected shared memory as well.
        expected=bytearray.fromhex(c['expected']);initial=bytearray.fromhex(c['initial'])
        for addr,value in [(0x1404f1e80,bytes([e['character'],e['shot']])),(0x1404f1e84,struct.pack('<i',e['stage'])),(0x1404f27c0,struct.pack('<i',e['difficulty'])),(0x1404f2798,struct.pack('<Q',int(e['score'])))]:
            offset=addr-0x1404f1e8c
            if offset>=0:expected[offset:offset+len(value)]=value
        m.reg_write(UC_X86_REG_RBP,n.owner);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007430c,0x140074457,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x140074457,(i,'stop');actual=bytes(m.mem_read(0x1404f1e8c,0xd2d8));assert actual==expected,(i,'globals');digest.update(actual)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-stats-result-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(data['cases'])}))
if __name__=='__main__':main()
