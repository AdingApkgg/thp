"""Native CATK/PSCR loaders, Result CLRD defaults/load, title CATK init and boot MUSC.

Complete destination spans compare, including CATK saturation, early scan stops,
PSCR aliases and the 101-slot accepted write span despite 96 initialized slots.
Raw valid-size chunks and initialized CATK globals are explicit inputs. The
original score.dat is read only. Title's first-slot CATK gate and boot's last
matching MUSC selection also compare. Full startup/global ownership, stat
producers, malformed undersized native memory reads and browser excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE

def main():
    sources=['shared/th06nc/score-stat-load.mjs','shared/th06nc/score-file.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    script="""
import{readFileSync}from'node:fs';import{createScoreChunk,decodeScoreFile}from'./shared/th06nc/score-file.mjs';import{loadCardAttackScores,loadPracticeScores,loadClearedScores,initializeTitleCardAttackScores,loadMusicScores}from'./shared/th06nc/score-stat-load.mjs';
const hex=b=>Buffer.from(b).toString('hex'),cases=[];let state=123456789;const byte=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state&255;};
for(let i=0;i<41;i++){const records=[];if(i===40)records.push(...decodeScoreFile(readFileSync('H:/Games/th/06nc/score.dat')).records);else if(i>0){for(let j=0;j<32;j++){const tag=['CATK','PSCR','CLRD','TEST'][j%4],r=createScoreChunk(tag,tag==='CATK'?384:24);for(let k=9;k<r.length;k++)r[k]=byte();if(tag==='CATK'){const v=new DataView(r.buffer);v.setUint16(16,(i+j)%134,true);for(const off of [60,62])v.setUint16(off,[0,9998,9999,10000,65535][(i+j+off)%5],true);for(let off=0xe0;off<0x180;off+=4)v.setUint32(off,[0,999999998,999999999,1000000000,0xffffffff][(i+j+off)%5],true);}if(tag==='PSCR'){r[20]=(i+j)%4;r[21]=(i+j)%5;r[22]=(i+j)%7;}if(tag==='CLRD')r[22]=(i+j)%4;if((i+j)%11===0)r[8]=20;records.push(r);}const invalid=createScoreChunk(['CATK','PSCR','CLRD'][i%3],i%3===0?384:24);if(i%3===0)new DataView(invalid.buffer).setUint16(16,134,true);if(i%3===1){invalid[20]=4;invalid[21]=0;invalid[22]=0;}if(i%3===2)invalid[22]=4;records.splice(i%16,0,invalid);}
if(i<40)for(let j=0;j<3;j++){const r=createScoreChunk('MUSC',16);for(let k=9;k<16;k++)r[k]=byte();if(j===2&&i%2)r[8]=20;records.push(r);}const card=Uint8Array.from({length:134*384},byte),practice=Uint8Array.from({length:101*24},byte),titleCard=Uint8Array.from({length:134*384},byte);if(i%2)new DataView(titleCard.buffer).setUint32(0,0x4b544143,true);const before={card:hex(card),practice:hex(practice),titleCard:hex(titleCard)},after={card:hex(loadCardAttackScores(records,card)),practice:hex(loadPracticeScores(records,practice)),cleared:hex(loadClearedScores(records)),titleCard:hex(initializeTitleCardAttackScores(records,titleCard)),music:hex(loadMusicScores(records))};cases.push({records:records.map(hex),before,after});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();comparisons=0
    def memset(m,a,size,u):
        dst=m.reg_read(UC_X86_REG_RCX);count=m.reg_read(UC_X86_REG_R8);m.mem_write(dst,bytes([m.reg_read(UC_X86_REG_RDX)&255])*count);m.reg_write(UC_X86_REG_RAX,dst);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    m.hook_add(UC_HOOK_CODE,memset,begin=0x1402bdee2,end=0x1402bdee2)
    for i,c in enumerate(cases):
        body=b''.join(bytes.fromhex(r)for r in c['records']);m.mem_write(n.assets,struct.pack('<6I',24,0,0,0,len(body)+24,0)+body)
        for key,start in [('card',0x14006cc40),('practice',0x14006ce20)]:
            initial=bytes.fromhex(c['before'][key]);m.mem_write(n.owner,initial);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.assets);m.reg_write(UC_X86_REG_RDX,n.owner);m.emu_start(start,n.stack+0xf000,count=1000000)
            assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(i,key,'stop');actual=bytes(m.mem_read(n.owner,len(initial)));assert actual==bytes.fromhex(c['after'][key]),(i,key,'destination');assert m.reg_read(UC_X86_REG_EAX)==0,(i,key,'return');digest.update(actual);comparisons+=1
        m.mem_write(0x1404ff0f4,b'\xa5'*96);m.reg_write(UC_X86_REG_R8,n.assets);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140074348,0x1400743f4,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x1400743f4,(i,'CLRD stop');actual=bytes(m.mem_read(0x1404ff0f4,96));assert actual==bytes.fromhex(c['after']['cleared']),(i,'CLRD destination');digest.update(actual);comparisons+=1
        m.mem_write(0x1404f27c8,bytes.fromhex(c['before']['titleCard']));m.reg_write(UC_X86_REG_R14,n.assets);m.reg_write(UC_X86_REG_R15,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140056042,0x1400560be,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x1400560be,(i,'title CATK stop');actual=bytes(m.mem_read(0x1404f27c8,134*384));assert actual==bytes.fromhex(c['after']['titleCard']),(i,'title CATK');digest.update(actual);comparisons+=1
        m.mem_write(0x1404ff154,b'\xa5'*16);m.reg_write(UC_X86_REG_RSI,n.assets);m.reg_write(UC_X86_REG_XMM0,0);m.emu_start(0x140045776,0x1400457cd,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x1400457cd,(i,'MUSC stop');actual=bytes(m.mem_read(0x1404ff154,16));assert actual==bytes.fromhex(c['after']['music']),(i,'MUSC destination');digest.update(actual);comparisons+=1
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
    report=dict(scope=__doc__,cases=len(cases),completeOwnerComparisons=comparisons,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-score-stat-load-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'ownerComparisons':comparisons}))
if __name__=='__main__':main()
