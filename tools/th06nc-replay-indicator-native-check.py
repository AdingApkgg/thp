"""Replay indicator 6bab0 init and ordinary 6bc30/6bf52 draw branch.

Actual text.anm sprite binding, complete 1a0 owner and ordered camera/draw
requests. Localization dictionary/font publication are services, with cache
present/absent cases. Debug 0x8000 statistics, font pixels and GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['replay-indicator','replay-playback','anm-bank','anm-rebind','anm-vm'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names};script="""
import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{ReplayPlayback}from'./shared/th06nc/replay-playback.mjs';import{initializeReplayIndicator,drawReplayIndicator}from'./shared/th06nc/replay-indicator.mjs';const ref={archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},bank=new AnmBank();bank.load(readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),ref.base,{slot:ref.slot});const hex=b=>Buffer.from(b).toString('hex'),scenes=[];
for(const reinitialize of [false,true])for(const cache of [false,true])for(const playbackFlag of [false,true])for(const replay of [false,true])for(const clock of [0,1,29,59,60,61,119,120,2147483647,4294967295]){const p=new ReplayPlayback({bytes:new Uint8Array(120),stageOffsets:Array(7).fill(null)});if(reinitialize){[2,3,97,28].forEach((x,i)=>p.v.setInt32(0x184+i*4,x,true));p.v.setFloat32(0x140,-20,true);p.v.setUint32(0x164,0x80ffccaa,true);p.v.setUint32(0x198,1234,true);}const initial=hex(p.bytes),events=[];initializeReplayIndicator(p,{anmBank:bank,publishText:(vm,r)=>{events.push({...r});if(cache){[1,1,120,36].forEach((x,i)=>vm.v.setInt32(0x10c+i*4,x,true));vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|1,true);}}});const initialized=hex(p.bytes);p.bytes[8]=Number(playbackFlag);p.v.setUint32(0x198,clock,true);const calls=[];const result=drawReplayIndicator(p,(vm,r)=>calls.push({kind:'draw',state:hex(vm.state)}),{replay,setupCamera:r=>calls.push({kind:'camera',...r})});scenes.push({cache,playbackFlag,replay,clock,initial,initialized,events,calls,result,after:hex(p.bytes)});}console.log(JSON.stringify({ref,scenes}));
 """;data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([data['ref']]);events=[];calls=[];cache=False;digest=hashlib.sha256()
 def normal(raw,owner=False):
  raw=bytearray(raw);base=0x78 if owner else 0
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,base+p)[0]
   if ptr:struct.pack_into('<Q',raw,base+p,ptr-n.assets)
  ptr=struct.unpack_from('<Q',raw,base+0x100)[0]
  if ptr:struct.pack_into('<Q',raw,base+0x100,(ptr-n.manager-0x608)//64+1)
  return raw
 def hook(m,a,size,u):
  if a==0x14006bb01:m.reg_write(UC_X86_REG_RDI,n.vm+0x5000);m.reg_write(UC_X86_REG_RIP,0x14006bba0);return
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==0x140007530:
   ptr=m.reg_read(UC_X86_REG_RDX);events.append(dict(key='EXE_REPLAY_INDICATOR',text='EXE_REPLAY_INDICATOR',colors=[m.reg_read(UC_X86_REG_R8D),m.reg_read(UC_X86_REG_R9D),struct.unpack('<I',m.mem_read(sp+0x28,4))[0],struct.unpack('<I',m.mem_read(sp+0x30,4))[0]]))
   if cache:m.mem_write(ptr+0x10c,struct.pack('<4i',1,1,120,36));m.mem_write(ptr+0xc4,struct.pack('<I',struct.unpack('<I',m.mem_read(ptr+0xc4,4))[0]|1))
  elif a==0x1400067f0:calls.append(dict(kind='draw',state=normal(m.mem_read(m.reg_read(UC_X86_REG_RDX),288)).hex()))
  elif a==0x14007af40:calls.append(dict(kind='camera',minZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM1)&0xffffffff))[0],maxZ=struct.unpack('<f',struct.pack('<I',m.reg_read(UC_X86_REG_XMM2)&0xffffffff))[0],perspective=bool(m.reg_read(UC_X86_REG_R9D))))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x14006bb01,0x140007530,0x1400067f0,0x14007af40,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(a):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(a,n.stack+0xf000,count=100000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;return m.reg_read(UC_X86_REG_RAX)&255
 m.mem_write(n.vm+0x5000,b'EXE_REPLAY_INDICATOR\0')
 for index,s in enumerate(data['scenes']):
  cache=s['cache'];events.clear();calls.clear();m.mem_write(n.owner,bytes.fromhex(s['initial']));run(0x14006bab0);actual=normal(m.mem_read(n.owner,0x1a0),True);wanted=bytes.fromhex(s['initialized']);assert actual==wanted,(index,'init',[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:12]);assert events==s['events'];m.mem_write(n.owner+8,bytes([s['playbackFlag']]));m.mem_write(n.owner+0x198,struct.pack('<I',s['clock']));m.mem_write(0x1404f278c,bytes([s['replay']]));m.mem_write(0x1404f27b0,b'\0');m.mem_write(0x140c21d9c,struct.pack('<i',2));m.mem_write(0x140a6ec60,bytes(4));result=run(0x14006bc30);assert result==s['result'];assert calls==s['calls'],(index,'calls',calls,s['calls']);actual=normal(m.mem_read(n.owner,0x1a0),True);assert actual.hex()==s['after'],(index,'after');digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-indicator-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'scenes':len(data['scenes']),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
