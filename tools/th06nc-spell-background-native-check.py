"""Spell STD preparation 77550 with actual seven ECL/STD programs and ANMs.

All 131 catalog IDs execute actual 77bb0 background updates. Compares full
STD owner, mutable file and ANM-pool hashes, direction, fog requests and number
of preparation ticks. Controlled resource transport/allocations, fog calls and
catalog lazy init; rendering, GPU, complete game startup and Power cache excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['spell-practice-background','std-state','std-update','std','spell-practice-table'];hashes={'shared/th06nc/'+s+'.mjs':hashlib.sha256((ROOT/'shared/th06nc'/f'{s}.mjs').read_bytes()).hexdigest()for s in sources}
 subprocess.run(['node','tools/th06nc-spell-background-cases.mjs'],cwd=ROOT,check=True);data=json.loads((ROOT/'tools/tmp/th06nc-spell-background-cases.json').read_text(encoding='utf-8'));n=Native();m=n.m;rawBase=n.assets+0x80000;eclBase=n.assets+0x100000;catalog=n.vm+0x8000;owner=0x140509b60;table=n.owner+0x400;pool=n.owner+0x1000;fog=[];allocs=[];frames=0
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);m.mem_write(catalog+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',catalog));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])))
 def hook(m,a,size,u):
  nonlocal frames
  if a==0x140077bb0:frames+=1;return
  if a==0x1400020b0:m.reg_write(UC_X86_REG_RAX,0)
  elif a==0x1400387a0:m.reg_write(UC_X86_REG_RAX,rawBase)
  elif a==0x1402bd4a0:
   size=m.reg_read(UC_X86_REG_RCX);ptr=table if not allocs else pool;allocs.append(size);m.mem_write(ptr,bytes(size));m.reg_write(UC_X86_REG_RAX,ptr)
  elif a==0x1400969c0:fog.append(bytes([99]+[m.reg_read(r)&255 for r in [UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_R8]]))
  elif a==0x140096b00:fog.append(b'r'+b''.join((m.reg_read(r)&0xffffffff).to_bytes(4,'little')for r in [UC_X86_REG_XMM0,UC_X86_REG_XMM1]))
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140077bb0,0x1400020b0,0x1400387a0,0x1402bd4a0,0x1400969c0,0x140096b00,0x140076b90]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(address):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,owner);m.emu_start(address,n.stack+0xf000,count=30000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,hex(m.reg_read(UC_X86_REG_RIP))
 digest=hashlib.sha256();total=0;last_stage=0
 for c in data['cases']:
  stage=c['stage'];n.load_title([c['ref']]);raw=(ROOT/f'runtimes/th06nc/artifacts/scripts/th06ST.dat/stage{stage}.std').read_bytes();ecl=(ROOT/f'runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata{stage}.ecl').read_bytes();m.mem_write(rawBase,raw);m.mem_write(eclBase,ecl);m.mem_write(0x140a6eb70,struct.pack('<Q',eclBase+struct.unpack_from('<I',ecl,4)[0]));m.mem_write(owner,bytes(0x220));m.mem_write(0x1404f1e84,struct.pack('<i',stage));m.mem_write(0x1404f27b8,bytes([c['id']]));m.mem_write(0x1404f27b9,b'\0');m.mem_write(0x1404ff26c,bytes(12));allocs.clear();fog.clear();frames=0
  run(0x1400785c0);fog.clear();run(0x140077550);assert frames==c['result']['frames'],(c['id'],'ticks',frames,c['result']);assert len(fog)==c['fogRequests'],(c['id'],'fog count');assert hashlib.sha256(b''.join(fog)).hexdigest()==c['fogSha256'],(c['id'],'fog')
  actual=bytearray(m.mem_read(owner,0x220))
  for p in [0x28,0x1f0]:struct.pack_into('<Q',actual,p,struct.unpack_from('<Q',actual,p)[0]-rawBase)
  for p in [0x70,0x88,0xa8]:struct.pack_into('<Q',actual,p,1)
  wanted=bytes.fromhex(c['owner']);assert actual==wanted,(c['id'],'owner',[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y]);digest.update(actual)
  actual=bytearray(m.mem_read(pool,c['primitives']*288))
  for i in range(c['primitives']):
   for p in [0xf0,0xf8]:
    offset=i*288+p;ptr=struct.unpack_from('<Q',actual,offset)[0]
    if ptr:struct.pack_into('<Q',actual,offset,ptr-n.assets)
   offset=i*288+0x100;ptr=struct.unpack_from('<Q',actual,offset)[0]
   if ptr:struct.pack_into('<Q',actual,offset,(ptr-n.manager-0x608)//64+1)
  assert hashlib.sha256(actual).hexdigest()==c['poolSha256'],(c['id'],'pool');assert hashlib.sha256(m.mem_read(rawBase,len(raw))).hexdigest()==c['fileSha256'],(c['id'],'file');assert list(struct.unpack('<3f',m.mem_read(0x1404ff26c,12)))==c['direction'],(c['id'],'direction');digest.update(actual);total+=frames
  if stage!=last_stage:print(json.dumps({'stage':stage,'id':c['id'],'passed':True}),flush=True);last_stage=stage
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(data['cases']),frames=total,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-background-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
