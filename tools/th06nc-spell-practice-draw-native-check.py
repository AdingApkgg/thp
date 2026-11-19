"""Complete spell-menu drawing 53500..54869 against ordered draw requests.

Runs native list/fade/highlight/transition/edge helpers, sprite setters and
catalog/record queries. Inputs include text VMs from the separately captured
native font publisher. Controls cookie, catalog lazy initialization, texture
availability, f32 trigonometry and final 2a80/36c0 draw submission. Compares
all requested VM bytes and retained VM state, not native CRT/GPU pixels.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['spell-practice-draw','spell-practice-draw-list','spell-practice-draw-effects','spell-practice-highlight','spell-practice-table','anm-vm'];hashes={'shared/th06nc/'+s+'.mjs':hashlib.sha256((ROOT/'shared/th06nc'/f'{s}.mjs').read_bytes()).hexdigest()for s in sources}
 subprocess.run(['node','tools/th06nc-spell-practice-draw-cases.mjs'],cwd=ROOT,check=True)
 data=json.loads((ROOT/'tools/tmp/th06nc-spell-practice-draw-cases.json').read_text(encoding='utf-8'));n=Native();n.load_title(data['refs']);m=n.m;catalog=n.vm+0x8000;requests=[]
 for i,r in enumerate(data['table']):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);name=r['name'].encode();b[7:7+len(name)]=name;m.mem_write(catalog+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',catalog));m.mem_write(0x140c2208c,struct.pack('<I',len(data['table'])))
 for i in range(256):m.mem_write(n.manager+0x20620+i*8,struct.pack('<2i',0,-1))
 fields={'state':0x168b0,'frame':0x9638,'pulse':0x30,'spellStage':0x168dc,'spellOrder':0x168e0,'spellScroll':0x168e4,'spellDifficulty':0x168e8,'profileTransition':0x16900,'difficultyTransition':0x168fc,'orderDirection':0x168f8,'completeStage':0x1691c,'completeClock':0x16924,'noticeClock':0x16914}
 byte_fields={'fastEntry':0x168d4,'completePending':0x16918,'completeProfile':0x16920,'noticePending':0x16904,'noticeProfile':0x16910}
 def normalized(p):
  state=bytearray(m.mem_read(p,288))
  for o in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',state,o)[0]
   if ptr:struct.pack_into('<Q',state,o,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',state,0x100)[0]
  if ptr:struct.pack_into('<Q',state,0x100,(ptr-n.manager-0x608)//64+1)
  return state.hex()
 def ret():
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 def hook(m,a,size,u):
  if a in [0x1402be07d,0x1402be071]:
   key=('sin'if a==0x1402be07d else'cos')+':'+str(m.reg_read(UC_X86_REG_XMM0)&0xffffffff);assert key in data['trig'],key;m.reg_write(UC_X86_REG_XMM0,data['trig'][key])
  elif a in [0x140002a80,0x1400036c0]:
   wrapper=a==0x1400036c0;sp=m.reg_read(UC_X86_REG_RSP);requests.append(dict(state=normalized(m.reg_read(UC_X86_REG_RDX)),snap=bool(m.reg_read(UC_X86_REG_R8)&255)if wrapper else bool(m.mem_read(sp+0x28,1)[0]),topAlpha=255 if wrapper else m.reg_read(UC_X86_REG_R8)&255,bottomAlpha=255 if wrapper else m.reg_read(UC_X86_REG_R9)&255))
  ret()
 for a in [0x1402be07d,0x1402be071,0x1402bcf20,0x140076b90,0x140002a80,0x1400036c0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 digest=hashlib.sha256();total=0
 for index,c in enumerate(data['cases']):
  requests.clear();m.mem_write(n.owner,bytes(0x20000));state=c['state']
  for key,offset in fields.items():m.mem_write(n.owner+offset,struct.pack('<i',state[key]))
  for key,offset in byte_fields.items():m.mem_write(n.owner+offset,bytes([int(state[key])]))
  m.mem_write(n.owner+0x16928,bytes(state['completeFlags']));record=state['noticeRecord'];m.mem_write(n.owner+0x16908,struct.pack('<Q',catalog+record*40 if record is not None else 0))
  m.mem_write(0x1404f1e80,bytes([c['description']['profile']>>1,c['description']['profile']&1]));m.mem_write(0x1404f27c8,bytes.fromhex(c['records']))
  for slot in c['before']:
   b=bytearray.fromhex(slot['state'])
   for offset in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',b,offset)[0]
    if ptr:struct.pack_into('<Q',b,offset,ptr+n.assetByFile[slot['file']])
   ptr=struct.unpack_from('<Q',b,0x100)[0]
   if ptr:struct.pack_into('<Q',b,0x100,n.manager+0x608+(ptr-1)*64)
   m.mem_write(n.owner+slot['offset'],bytes(b))
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x140053500,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  if requests!=c['requests']:
   for i,(actual,wanted)in enumerate(zip(requests,c['requests'])):
    if actual!=wanted:
     diff=[(hex(j),x,y)for j,(x,y)in enumerate(zip(bytes.fromhex(actual['state']),bytes.fromhex(wanted['state'])))if x!=y];raise AssertionError((index,c['description'],'request',i,len(requests),len(c['requests']),diff,{k:v for k,v in actual.items()if k!='state'},{k:v for k,v in wanted.items()if k!='state'}))
   raise AssertionError((index,'request count',len(requests),len(c['requests'])))
  for slot in c['after']:
   actual=normalized(n.owner+slot['offset']);assert actual==slot['state'],(index,c['description'],'retained',hex(slot['offset']),[(hex(j),x,y)for j,(x,y)in enumerate(zip(bytes.fromhex(actual),bytes.fromhex(slot['state'])))if x!=y]);digest.update(bytes.fromhex(actual))
  total+=len(requests)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),drawRequests=total,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-practice-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
