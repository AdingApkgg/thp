"""Native spell-practice ID lookup, unlock, completion and list viewport.

Executes 466d0/46740/46850/46900 with the separately verified catalog projection.
Catalog lazy initialization is controlled; full menu input/draw/launch excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/spell-practice-table.mjs','shared/th06nc/messagepack.mjs','shared/th06nc/spell-record.mjs']
 hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{readFileSync}from'node:fs';import{readSpellPracticeTable,findSpellPractice,spellPracticeOrderUnlocked,spellPracticeStageComplete,spellPracticeViewport}from'./shared/th06nc/spell-practice-table.mjs';import{createSpellRecord}from'./shared/th06nc/spell-record.mjs';
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),ids=[],viewports=[],cases=[];
for(const id of [-1,...Array.from({length:256},(_,i)=>i),256,511,2147483647])ids.push({id,expected:findSpellPractice(table,id)?.id??null});
for(const stage of [-1,0,1,2,3,4,5,6,7,8,256])for(const selection of [-2147483648,-3,-1,...Array.from({length:22},(_,i)=>i),2147483647])for(const scroll of [-2,0,1,3,10,2147483647])viewports.push({stage,selection,scroll,expected:spellPracticeViewport(table,stage,selection,scroll)});
for(let mode=0;mode<5;mode++){
 const records=new Map(Array.from({length:134},(_,id)=>{const r=createSpellRecord();r.attempts=mode?1:0;if(mode>=2)r.practiceCaptures.fill(1);if(mode===3&&[0,9,20,37,84,100,118].includes(id))r.attempts=0;if(mode===4)for(let i=0;i<20;i++)r.practiceCaptures[i]=i%4===0?1:0;return[id,r];}));
 const unlocked=[],complete=[];for(const stage of [-1,0,1,2,3,4,5,6,7]){for(let order=-1;order<=17;order++)unlocked.push({stage,order,expected:spellPracticeOrderUnlocked(table,records,stage,order)});for(const [character,shot]of [[0,0],[0,1],[1,0],[1,1],[2,0],[255,255]])complete.push({stage,character,shot,expected:spellPracticeStageComplete(table,records,stage,character,shot)});}
 cases.push({mode,bytes:Buffer.concat([...records.values()].map(r=>r.bytes)).toString('hex'),unlocked,complete});
}
console.log(JSON.stringify({table,ids,viewports,cases}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);name=r['name'].encode();b[7:7+len(name)]=name;m.mem_write(n.assets+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',n.assets));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])))
 def initialize(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 m.hook_add(UC_HOOK_CODE,initialize,begin=0x140076b90,end=0x140076b90)
 def call(address,rcx=0,rdx=0,r8=0,r9=0):
  for reg,value in [(UC_X86_REG_RCX,rcx),(UC_X86_REG_RDX,rdx),(UC_X86_REG_R8,r8),(UC_X86_REG_R9,r9),(UC_X86_REG_RSP,n.stack+0x8000)]:m.reg_write(reg,value&0xffffffffffffffff)
  m.mem_write(n.stack+0x8000,struct.pack('<Q',n.stack+0xf000));m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;return m.reg_read(UC_X86_REG_RAX)
 for c in data['ids']:
  pointer=call(0x1400466d0,c['id']);actual=bytes(m.mem_read(pointer,1))[0]if pointer else None;assert actual==c['expected'],c
 for c in data['viewports']:
  call(0x140046900,n.owner,c['stage'],c['selection'],c['scroll']);values=struct.unpack('<4i',m.mem_read(n.owner,16));assert values==tuple(c['expected'][k]for k in ['count','start','visible','end']),(c,values)
 for case in data['cases']:
  m.mem_write(0x1404f27c8,bytes.fromhex(case['bytes']))
  for c in case['unlocked']:assert bool(call(0x140046850,c['stage'],c['order'])&255)==c['expected'],(case['mode'],c)
  for c in case['complete']:
   m.mem_write(0x1404f1e80,bytes([c['character'],c['shot']]));assert bool(call(0x140046740,c['stage'])&255)==c['expected'],(case['mode'],c)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 counts=dict(idLookups=len(data['ids']),viewports=len(data['viewports']),unlocks=sum(len(c['unlocked'])for c in data['cases']),stageCompletions=sum(len(c['complete'])for c in data['cases']))
 report=dict(scope=__doc__,**counts,stateSha256=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-query-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(counts|{'passed':True,'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
