"""Replay background 7583c initialization, five native ANM ticks and draw order.

Actual select00d resource, 180 frames each for open/closing paths, 75ad0 close,
75a50 back layers and 557c6 front layer. Ordered complete draw VMs and persistent
VM bytes compared. Resource I/O, title dispatcher and GPU pixels excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['title-replay-background','anm-bank','anm-vm'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names}
 script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{TitleReplayBackground,titleReplayBackgroundAsset}from'./shared/th06nc/title-replay-background.mjs';const ref=titleReplayBackgroundAsset,resource=readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file)),hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex'),scenes=[];
for(const closing of [false,true]){const background=new TitleReplayBackground(new AnmBank(),resource),initial=background.vms.map(vm=>hex(vm.state)),frames=[];for(let frame=0;frame<180;frame++){if(closing&&frame===60)background.close();background.tick();const calls=[];background.draw((vm,r)=>calls.push({...r,state:hex(vm.state)}));background.drawFront((vm,r)=>calls.push({...r,state:hex(vm.state)}));frames.push({calls,sha256:sha(Buffer.concat(background.vms.map(vm=>Buffer.from(vm.state))))});}scenes.push({closing,initial,frames});}console.log(JSON.stringify({ref,scenes}));
 """
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title([data['ref']]);base=n.owner+0x15ab0;calls=[];digest=hashlib.sha256()
 def normal(raw):
  raw=bytearray(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,ptr-n.assets)
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
  return raw
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(snap=True,offset=ptr-n.owner,path='flat'if a==0x140002a80 else'rotated',state=normal(m.mem_read(ptr,288)).hex()));m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x140002a80,0x1400036c0]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(a,rcx,rdx=0):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.reg_write(UC_X86_REG_RDX,rdx);m.emu_start(a,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 for scene in data['scenes']:
  m.mem_write(n.owner,bytes(0x20000))
  for i in range(5):m.mem_write(base+i*288+0x108,struct.pack('<H',0xf0f))
  m.reg_write(UC_X86_REG_RDI,0x7da);m.reg_write(UC_X86_REG_RBX,base);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14007583c,0x140075a34,count=1000000)
  for i,wanted in enumerate(scene['initial']):assert normal(m.mem_read(base+i*288,288)).hex()==wanted,('init',i)
  for frame,c in enumerate(scene['frames']):
   if scene['closing']and frame==60:run(0x140075ad0,base)
   for i in range(5):run(0x1400069b0,n.manager,base+i*288)
   calls.clear();run(0x140075a50,base);m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R11,n.manager);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x1400557c6,0x1400557e1,count=100000);assert calls==c['calls'],(scene['closing'],frame,'draw');raw=b''.join(normal(m.mem_read(base+i*288,288))for i in range(5));assert hashlib.sha256(raw).hexdigest()==c['sha256'],(scene['closing'],frame,'owner');digest.update(raw)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),frames=360,drawRequests=1800,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-replay-background-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'frames':360,'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
