"""New-run stats composition: native CATK defaults, CATK load, then PSCR load.
Compares the complete shared d2d8-byte stat span and RNG. Includes original
read-only score records, CATK saturation/scan stop and PSCR-to-CATK aliasing.
Score file decoding, HSCR and other game initializer fields are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+p+'.mjs'for p in ['score-stats','gameplay-card-attack','score-stat-load','rng']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
 import{readFileSync}from'node:fs';import{ScoreStats}from'./shared/th06nc/score-stats.mjs';import{NativeRng}from'./shared/th06nc/rng.mjs';import{createScoreChunk,decodeScoreFile}from'./shared/th06nc/score-file.mjs';
 const cases=[];for(let i=0;i<6;i++){const before=new Uint8Array(0xd2d8).fill(i*31),stats=new ScoreStats(before),rng=new NativeRng(0xbeef+i,0xffffffff-i),records=i===1?decodeScoreFile(readFileSync('H:/Games/th/06nc/score.dat')).records:[];
 if(i>=2){const card=createScoreChunk('CATK',384),v=new DataView(card.buffer);v.setUint16(16,37,true);v.setUint16(60,65535,true);v.setUint16(62,10000,true);v.setUint32(0x130,0xffffffff,true);records.push(card);}
 if(i>=3){const p=createScoreChunk('PSCR',24);p[20]=3;p[21]=4;p[22]=6;p.fill(90,12,20);records.push(p);}
 if(i>=4){const bad=createScoreChunk('CATK',384);new DataView(bad.buffer).setUint16(16,134,true);records.unshift(bad);}
 if(i===5){const bad=createScoreChunk('PSCR',24);bad[20]=4;records.unshift(bad);}
 stats.loadRun(records,rng);cases.push({seed:0xbeef+i,count:0xffffffff-i,before:Buffer.from(before).toString('hex'),records:records.map(r=>Buffer.from(r).toString('hex')),after:Buffer.from(stats.bytes).toString('hex'),rng});}console.log(JSON.stringify(cases));
 """
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 def memset(m,a,size,u):
  dst=m.reg_read(UC_X86_REG_RCX);m.mem_write(dst,bytes([m.reg_read(UC_X86_REG_EDX)&255])*m.reg_read(UC_X86_REG_R8));m.reg_write(UC_X86_REG_RAX,dst);sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,memset,begin=0x1402bdee2,end=0x1402bdee2)
 for c in cases:
  m.mem_write(n.owner,bytes.fromhex(c['before']));m.mem_write(0x140a6ec40,struct.pack('<IH',c['count'],c['seed']));m.reg_write(UC_X86_REG_RSI,n.owner+0x93c);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,0x6553);m.reg_write(UC_X86_REG_RBP,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14003aaf6,0x14003abcd,count=1000000)
  body=b''.join(bytes.fromhex(r)for r in c['records']);m.mem_write(n.assets,struct.pack('<6I',24,0,0,0,len(body)+24,0)+body)
  for start,dst in [(0x14006cc40,n.owner+0x93c),(0x14006ce20,n.owner)]:
   sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.assets);m.reg_write(UC_X86_REG_RDX,dst);m.emu_start(start,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=bytes(m.mem_read(n.owner,0xd2d8));assert actual.hex()==c['after'];count,seed=struct.unpack('<IH',m.mem_read(0x140a6ec40,6));assert dict(seed=seed,count=count)==c['rng'];digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-run-stats-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
