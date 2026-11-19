"""Spell result menu c230/c950, native ANM and full retained owner bytes.

Compares input/navigation/retry/return/fades, localized publication requests,
ordered VM draws and replay-result creation/closing. Text paint/localization,
replay-result allocation/constructor/task registration and final 67f0 submission
are controlled boundaries. Screenshot capture and GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['spell-practice-result-menu','pause-menu','spell-practice-draw-effects','fade','anm-rebind','anm-vm'];hashes={'shared/th06nc/'+s+'.mjs':hashlib.sha256((ROOT/'shared/th06nc'/f'{s}.mjs').read_bytes()).hexdigest()for s in sources}
 subprocess.run(['node','tools/th06nc-spell-result-menu-cases.mjs'],cwd=ROOT,check=True);data=json.loads((ROOT/'tools/tmp/th06nc-spell-result-menu-cases.json').read_text(encoding='utf-8'));n=Native();n.load_title(data['refs']);m=n.m;heap=0x75000000;m.mem_map(heap,0x10000);fonts=[];draws=[];opened=0;accepted=False
 def normal_vm(raw):
  raw=bytearray(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
  return raw
 def normal_owner():
  raw=bytearray(m.mem_read(n.owner,0xda0))
  for p in [*range(0,10*288,288),0xb50,0xc70]:raw[p:p+288]=normal_vm(raw[p:p+288])
  return bytes(raw)
 def hook(m,a,size,u):
  nonlocal opened
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x140009d3a:m.reg_write(UC_X86_REG_RIP,0x140009e05);return
  if a==0x140007530:
   p=m.reg_read(UC_X86_REG_RDX);keyPtr=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];key=bytes(m.mem_read(keyPtr,100)).split(b'\0')[0].decode();colors=[m.reg_read(UC_X86_REG_R8)&0xffffffff,m.reg_read(UC_X86_REG_R9)&0xffffffff,*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))];fonts.append(dict(offset=p-n.owner,key=key,colors=colors));m.mem_write(p+0x10c,struct.pack('<4i',1,1,120,36));flags=struct.unpack('<I',m.mem_read(p+0xc4,4))[0];m.mem_write(p+0xc4,struct.pack('<I',flags|1))
  elif a==0x1400067f0:
   raw=normal_vm(m.mem_read(m.reg_read(UC_X86_REG_RDX),288));script=struct.unpack_from('<H',raw,0x38)[0];sprite=struct.unpack_from('<H',raw,0x34)[0];offset=0 if script in [0x775,0x776]else 0xc70 if script in [0x774,0x777] else(0x6c0+(sprite-0x740)*288);draws.append(dict(offset=offset,state=raw.hex()))
  elif a==0x1402bcf40:assert m.reg_read(UC_X86_REG_RCX)==0xbb48;m.reg_write(UC_X86_REG_RAX,heap)
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  elif a==0x14006df00:m.reg_write(UC_X86_REG_RAX,heap)
  elif a==0x14006dd20:
   opened+=1;assert m.mem_read(heap+0x9e9a,1)[0]==1;assert struct.unpack('<i',m.mem_read(heap+0x9e94,4))[0]==12;m.reg_write(UC_X86_REG_RAX,0 if accepted else 1)
   if not accepted:m.mem_write(0x140c22150,bytes(8))
  elif a not in [0x14007af40,0x1402bcf20]:raise AssertionError(hex(a))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140009d3a,0x140007530,0x1400067f0,0x1402bcf40,0x1402bdee2,0x14006df00,0x14006dd20,0x14007af40,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(address,rcx):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.emu_start(address,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 fields={'spellResultVisible':(0x1404f27b6,'B'),'resumeSpell':(0x1404f27b7,'B'),'spellRestartRequested':(0x140aa1e8c,'B'),'gameState':(0x140c21d9c,'i')};digest=hashlib.sha256();checked=0
 for index,s in enumerate(data['scenes']):
  accepted=s['captured'];opened=0;m.mem_write(n.owner,bytes(0xda0));m.mem_write(n.owner+0xd98,bytes([s['captured']]));m.mem_write(n.vm,bytes(0x10000));m.mem_write(0x140c22158,struct.pack('<Q',n.vm));m.mem_write(0x140c22150,struct.pack('<Q',heap if s['initialPresent']else 0));m.mem_write(0x1404f278c,bytes([s['replayPlayback']]));m.mem_write(0x140a6ec38,struct.pack('<Q',n.vm+0x1000));m.mem_write(n.vm+0x1070,struct.pack('<Q',1 if s['recordingAvailable']else 0));m.mem_write(0x140509670,struct.pack('<3i',*s['initialSounds']));m.mem_write(0x140509694,bytes([s['soundDisabled']]));m.mem_write(0x140c21e03,b'\0');m.mem_write(0x140c21e08,b'\0');m.mem_write(0x1404f27b6,b'\1\0');m.mem_write(0x140aa1e8c,b'\0');m.mem_write(0x140c21d9c,struct.pack('<i',3));previous=0
  for c in s['frames']:
   if c['externalClose']:m.mem_write(0x140c22150,bytes(8));m.mem_write(n.vm+0x34,struct.pack('<i',2));m.mem_write(n.vm+0x28,struct.pack('<i',255))
   m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],previous));previous=c['held'];fonts.clear();draws.clear();run(0x140075af0,n.vm);run(0x14000c230,n.owner);run(0x14000c950,n.owner);actual=normal_owner();wanted=bytes.fromhex(c['state'])
   assert actual==wanted,(index,c['frame'],'owner',[(hex(i),x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y][:20]);assert fonts==c['fonts'],(index,c['frame'],'fonts',fonts,c['fonts']);assert draws==c['calls'],(index,c['frame'],'draw',[(i,a['offset'],b['offset'],[(hex(j),x,y)for j,(x,y)in enumerate(zip(bytes.fromhex(a['state']),bytes.fromhex(b['state'])))if x!=y][:10])for i,(a,b)in enumerate(zip(draws,c['calls']))if a!=b],len(draws),len(c['calls']));assert bytes(m.mem_read(n.vm,56)).hex()==c['fade'],(index,c['frame'],'fade');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['sounds'],(index,c['frame'],'sound');assert opened==c['opened'];assert bool(struct.unpack('<Q',m.mem_read(0x140c22150,8))[0])==c['present']
   for key,(address,fmt)in fields.items():assert struct.unpack('<'+fmt,m.mem_read(address,struct.calcsize(fmt)))[0]==int(c['environment'][key]),(index,c['frame'],key)
   assert bool(m.mem_read(0x1404f27b6,1)[0])==c['active'];digest.update(actual);checked+=1
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=checked,drawRequests=sum(len(c['calls'])for s in data['scenes']for c in s['frames']),fontRequests=sum(len(c['fonts'])for s in data['scenes']for c in s['frames']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-spell-result-menu-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
