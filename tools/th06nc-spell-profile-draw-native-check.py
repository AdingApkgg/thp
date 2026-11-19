"""Spell profile preview 4f3c0 and labels 4f5b0 with nested helper 4fc00.

Real sprite resources, ordered complete VM draw requests, and retained state.
Final 2a80/36c0 submission, cookie, memset and texture availability controlled;
no GPU or CRT trigonometric equivalence claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 source='shared/th06nc/spell-practice-profile-draw.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();subprocess.run(['node','tools/th06nc-spell-profile-draw-cases.mjs'],cwd=ROOT,check=True)
 data=json.loads((ROOT/'tools/tmp/th06nc-spell-profile-draw-cases.json').read_text(encoding='utf-8'));n=Native();n.load_title(data['refs']);m=n.m;requests=[]
 for i in range(256):m.mem_write(n.manager+0x20620+i*8,struct.pack('<2i',0,-1))
 def normal(p):
  state=bytearray(m.mem_read(p,288))
  for o in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',state,o)[0]
   if ptr:struct.pack_into('<Q',state,o,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',state,0x100)[0]
  if ptr:struct.pack_into('<Q',state,0x100,(ptr-n.manager-0x608)//64+1)
  return state.hex()
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a in [0x140002a80,0x1400036c0]:
   wrapper=a==0x1400036c0;requests.append(dict(state=normal(m.reg_read(UC_X86_REG_RDX)),snap=bool(m.reg_read(UC_X86_REG_R8)&255)if wrapper else bool(m.mem_read(sp+0x28,1)[0]),topAlpha=255 if wrapper else m.reg_read(UC_X86_REG_R8)&255,bottomAlpha=255 if wrapper else m.reg_read(UC_X86_REG_R9)&255))
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140002a80,0x1400036c0,0x1402bcf20,0x1402bdee2]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 fields={'state':0x168b0,'frame':0x9638,'pulse':0x30,'stageTransition':0x168ec,'orderTransition':0x168f4,'stageDirection':0x168f0,'orderDirection':0x168f8};digest=hashlib.sha256();total=0
 for index,c in enumerate(data['cases']):
  requests.clear();m.mem_write(n.owner,bytes(0x20000))
  for key,offset in fields.items():m.mem_write(n.owner+offset,struct.pack('<i',c['state'][key]))
  m.mem_write(n.owner+0x168d4,bytes([c['state']['fastEntry']]));m.mem_write(0x1404f1e80,bytes([c['options']['character'],c['options']['shot']]))
  m.mem_write(0x140c21e44,struct.pack('<2I',c['options']['width'],c['options']['height']))
  for slot in c['before']:
   state=bytearray.fromhex(slot['state'])
   for o in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',state,o)[0]
    if ptr:struct.pack_into('<Q',state,o,ptr+n.assetByFile[slot['file']])
   ptr=struct.unpack_from('<Q',state,0x100)[0]
   if ptr:struct.pack_into('<Q',state,0x100,n.manager+0x608+(ptr-1)*64)
   m.mem_write(n.owner+slot['offset'],bytes(state))
  for address in [0x14004f3c0,0x14004f5b0]:
   sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(address,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  if requests!=c['requests']:
   for i,(a,b)in enumerate(zip(requests,c['requests'])):
    if a!=b:raise AssertionError((index,c['state'],'request',i,len(requests),len(c['requests']),[(hex(j),x,y)for j,(x,y)in enumerate(zip(bytes.fromhex(a['state']),bytes.fromhex(b['state'])))if x!=y]))
   raise AssertionError((index,'count',len(requests),len(c['requests'])))
  for slot in c['after']:
   actual=normal(n.owner+slot['offset']);assert actual==slot['state'],(index,'retained',hex(slot['offset']));digest.update(bytes.fromhex(actual))
  total+=len(requests)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(data['cases']),drawRequests=total,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-spell-profile-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
