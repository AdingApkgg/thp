"""Music Room owner/input update 584a0/57f30.

Full retained owner bytes, fade56, exit global and request order compared.
Original navigation, warning/repeat-confirm playback, exit and counters run.
Six ANM update bodies, description/localization publisher, audio transport,
UCRT path scanner and cookie are controlled services. Scanner policy is also
covered by the separate native music-unlock verifier. No UI/draw claim.
"""
import hashlib,json,re,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['music-room-update','music-room-table','music-unlock','fade']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 data=json.loads(subprocess.check_output(['node','tools/th06nc-music-room-update-cases.mjs'],cwd=ROOT));n=Native();m=n.m;fade=n.vm;calls=[];digest=hashlib.sha256()
 fields={'selection':0,'playingIndex':0x2408,'count':0x2420,'exitClock':0x2428,'pulse':0x242c,'warnedIndex':0x2430,'clock':0x2440,'entryTicks':0x2444,'scroll':0x2b08,'state':0x3d10}
 def cstring(address):
  result=bytearray()
  for i in range(512):
   b=m.mem_read(address+i,1)[0]
   if not b:return result.decode('utf-8')
   result.append(b)
  raise AssertionError('unterminated native string')
 def hook(m,a,size,u):
  if a==0x1400069b0:calls.append(dict(kind='animation',offset=m.reg_read(UC_X86_REG_RDX)-n.owner))
  elif a==0x1400591e0:calls.append(dict(kind='description',key=cstring(m.reg_read(UC_X86_REG_RDX)),initial=bool(m.reg_read(UC_X86_REG_R8)&255)))
  elif a==0x14007bc80:calls.append(dict(kind='music',file=cstring(m.reg_read(UC_X86_REG_RDX))))
  elif a==0x14003a180:
   text=cstring(m.reg_read(UC_X86_REG_RCX));found=re.match(r'^data/bgm/th06_[\t\n\v\f\r ]*([+-]?\d+)',text)
   if found:
    value=max(-0x8000000000000000,min(0x7fffffffffffffff,int(found[1])));value=((value+0x80000000)&0xffffffff)-0x80000000;m.mem_write(m.reg_read(UC_X86_REG_R8),struct.pack('<i',value))
   m.reg_write(UC_X86_REG_EAX,int(bool(found)))
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x1400069b0,0x1400591e0,0x14007bc80,0x14003a180,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 previousSet=None
 for index,c in enumerate(data['cases']):
  if previousSet!=c['set']:previousSet=c['set'];m.mem_write(n.assets,bytes.fromhex(data['recordSets'][previousSet]['bytes']))
  before=c['before'];m.mem_write(n.owner,bytes([c['fill']])*0x3d18)
  for key,offset in fields.items():m.mem_write(n.owner+offset,struct.pack('<i',before[key]))
  m.mem_write(n.owner+0x2424,bytes([before['leaving'],before['playMark']]));m.mem_write(n.owner+0x2438,struct.pack('<Q',n.assets));m.mem_write(0x140a6ec60,struct.pack('<2I',c['held'],c['previous']));m.mem_write(0x1404ff160,struct.pack('<I',before['unlockedMask']));m.mem_write(0x140c22158,struct.pack('<Q',fade if c['beforeFade']else 0));m.mem_write(0x140c21d9c,struct.pack('<i',9))
  if c['beforeFade']:m.mem_write(fade,bytes(c['beforeFade']))
  calls.clear();sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x1400584a0,n.stack+0xf000,count=10000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
  actual=bytearray(m.mem_read(n.owner,0x3d18));struct.pack_into('<Q',actual,0x2438,0x1000)
  assert hashlib.sha256(actual).hexdigest()==c['ownerSha256'],(index,before,calls,c['calls'],{key:struct.unpack_from('<i',actual,o)[0]for key,o in fields.items()})
  assert calls==c['calls'],(index,calls,c['calls']);assert m.reg_read(UC_X86_REG_EAX)==c['result'],(index,'return');assert struct.unpack('<i',m.mem_read(0x140c21d9c,4))[0]==c['gameState']
  if c['afterFade']:assert bytes(m.mem_read(fade,56))==bytes(c['afterFade']),(index,'fade')
  digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(data['cases']),requests=sum(len(c['calls'])for c in data['cases']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-music-room-update-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['passed','cases','requests','stateSha256']}))

if __name__=='__main__':main()
