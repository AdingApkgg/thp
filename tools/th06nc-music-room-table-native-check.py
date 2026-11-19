"""Original Music Room table parser 58b50 and original musiccmt.txt.

Compares the entire retained 0x1080-byte allocation and returned row count,
including all original-file prefixes, CR/LF variants, incomplete records,
retained nonzero bytes and safely bounded overlapping field writes.
No localization, menu, rendering, sound or application handoff claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/music-room-table.mjs','shared/th06nc/music-unlock.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{readFileSync}from'node:fs';import{readMusicRoomTable}from'./shared/th06nc/music-room-table.mjs';const original=readFileSync('runtimes/th06nc/artifacts/scripts/th06MD.dat/musiccmt.txt'),inputs=[...Array.from({length:original.length+1},(_,n)=>original.subarray(0,n))];
for(const nl of ['\\n','\\r','\\r\\n','\\n\\r'])for(const count of [1,2,18,32])inputs.push(Buffer.from(Array.from({length:count},(_,i)=>'@data/bgm/th06_'+String(i+1).padStart(2,'0')+'.opus'+nl+'MD_'+i+'_TITLE'+nl+'MD_'+i+'_DESC'+nl).join(nl)));
for(const text of ['@','@\\n','@\\nA','@\\nA\\n','junk@path\\nTITLE\\nDESC','@'+('a'.repeat(70))+'\\n'+('b'.repeat(40))+'\\n'+('c'.repeat(38))+'\\n'])inputs.push(Buffer.from(text));
const cases=[];for(const input of inputs)for(const fill of [0,165]){const destination=new Uint8Array(0x1080).fill(fill),r=readMusicRoomTable(input,{destination});cases.push({input:Buffer.from(input).toString('hex'),fill,count:r.count,sha256:(await import('node:crypto')).createHash('sha256').update(r.bytes).digest('hex')});}console.log(JSON.stringify({cases,records:readMusicRoomTable(original).records}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for index,c in enumerate(data['cases']):
  raw=bytes.fromhex(c['input']);m.mem_write(n.assets,raw+bytes(1024));m.mem_write(n.owner,bytes([c['fill']])*0x1080);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000))
  for reg,value in [(UC_X86_REG_RSP,sp),(UC_X86_REG_RCX,n.owner),(UC_X86_REG_RDX,n.assets),(UC_X86_REG_R8,len(raw))]:m.reg_write(reg,value)
  m.emu_start(0x140058b50,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=bytes(m.mem_read(n.owner,0x1080));count=struct.unpack('<i',struct.pack('<I',m.reg_read(UC_X86_REG_EAX)))[0]+1
  assert count==c['count'],(index,count,c['count']);assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,len(raw),c['fill']);digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 original=ROOT/'runtimes/th06nc/artifacts/scripts/th06MD.dat/musiccmt.txt';report=dict(scope=__doc__,cases=len(data['cases']),records=data['records'],inputSha256=hashlib.sha256(original.read_bytes()).hexdigest(),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-music-room-table-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(data['cases']),tracks=len(data['records']))))

if __name__=='__main__':main()
