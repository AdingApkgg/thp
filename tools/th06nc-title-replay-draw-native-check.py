"""Title replay ANM initialization and text/difficulty draw 55266..556a7.

Real replay00/difficulty/ASCII resources, native VM setters, native text cache
and UCRT formatting. Complete ASCII bytes and ordered difficulty VMs compared.
File records and decoded replay are controlled. GPU/common title draw excluded.
"""
import ctypes,hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['title-replay-layout','title-replay-draw','ascii-text','score-popup-draw','anm-bank','anm-rebind','anm-vm'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names}
 script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readAnm}from'./shared/th06nc/anm.mjs';import{AnmBank}from'./shared/th06nc/anm-bank.mjs';import{initializeTitleReplayAnimations,titleReplayResources}from'./shared/th06nc/title-replay-layout.mjs';import{drawTitleReplay}from'./shared/th06nc/title-replay-draw.mjs';import{createAsciiTextState}from'./shared/th06nc/ascii-text.mjs';const refs=[...titleReplayResources,{file:'ascii.anm',slot:1,base:0,archive:'th06IN.dat'}],resources=new Map(refs.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+(r.archive??'th06TL.dat')+'/'+r.file))])),bank=new AnmBank();bank.load(resources.get('ascii.anm'),0,{slot:1});const group={bank,slots:new Map()},hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex');initializeTitleReplayAnimations(group,resources);const initialized=[...group.slots].map(([offset,vm])=>({offset,state:hex(vm.state)}));for(const vm of group.slots.values()){vm.v.setFloat32(0xc8,12.25,true);vm.v.setFloat32(0xcc,33.5,true);vm.v.setFloat32(0xd0,.25,true);}const baseline=[...group.slots].map(([offset,vm])=>({offset,state:hex(vm.state)})),records=Array.from({length:60},(_,i)=>{const header=new Uint8Array(120);header[6]=i%4;header[7]=i%4;header[8]=i%6;header.set(new TextEncoder().encode('11/15/26'),20);header.set(new TextEncoder().encode(i%2?'PLAYER  ':'X'),29);return {header,label:'No.'+String(i+1).padStart(2,'0')};}),bytes=new Uint8Array(120+7*32),dv=new DataView(bytes.buffer),stageOffsets=Array.from({length:7},(_,i)=>i%2?null:120+i*32);dv.setFloat32(52,12.125,true);for(let i=0;i<7;i++)if(stageOffsets[i]!==null)dv.setBigInt64(stageOffsets[i],[123n,-1n,9999999999n,-9223372036854775808n][i>>1],true);const decoded={bytes,stageOffsets},scenes=[];
for(const kind of [18,19,20,26])for(const selected of [0,14,15,59])for(const pulse of [0,29,30,42,71])for(const count of [0,1,17,60]){for(const b of baseline)group.slots.get(b.offset).state.set(Buffer.from(b.state,'hex'));const ascii=createAsciiTextState(bank),calls=[],state={state:kind,replaySelection:selected,selection:selected%7,pulse};drawTitleReplay(group,(vm,r)=>calls.push({...r,state:hex(vm.state)}),{state,records:records.slice(0,count),decoded,ascii});scenes.push({state,count,calls,fontSha256:sha(ascii.bytes),difficulty:hex(group.slots.get(0x16050).state)});}console.log(JSON.stringify({refs,initialized,baseline,records:records.map(r=>({...r,header:hex(r.header)})),decoded:{bytes:hex(bytes),stageOffsets},scenes}));
 """
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;n.load_title(data['refs']);fontBase=0x1403de620;fileBase=n.vm+0x3000;shim=n.vm+0x9000;m.mem_write(shim,b'\xc3');m.mem_write(0x1402c0528,struct.pack('<Q',shim));crt=ctypes.CDLL('ucrtbase');formatter=crt.__stdio_common_vsprintf;formatter.restype=ctypes.c_int;formatter.argtypes=[ctypes.c_uint64,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_void_p];calls=[];digest=hashlib.sha256()
 def normal(raw):
  raw=bytearray(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,(ptr-n.manager-0x608)//64+1)
  return raw
 def native_vm(raw):
  raw=bytearray.fromhex(raw)
  for p in [0xf0,0xf8]:
   ptr=struct.unpack_from('<Q',raw,p)[0]
   if ptr:struct.pack_into('<Q',raw,p,n.assetByFile['replay00.anm']+ptr)
  ptr=struct.unpack_from('<Q',raw,0x100)[0]
  if ptr:struct.pack_into('<Q',raw,0x100,n.manager+0x608+(ptr-1)*64)
  return bytes(raw)
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP)
  if a==shim:
   fmt=bytes(m.mem_read(m.reg_read(UC_X86_REG_R9),100)).split(b'\0')[0];va=struct.unpack('<Q',m.mem_read(sp+0x30,8))[0];args=list(struct.unpack('<8Q',m.mem_read(va,64)));buffers=[]
   indices=[0,1,2,3,4]if fmt.startswith(b'%s %8s')else [0]if fmt.startswith(b'%s ')else []
   for i in indices:
    raw=bytes(m.mem_read(args[i],100)).split(b'\0')[0];buffers.append(ctypes.create_string_buffer(raw));args[i]=ctypes.addressof(buffers[-1])
   argument=(ctypes.c_uint64*8)(*args);out=ctypes.create_string_buffer(512);length=formatter(m.reg_read(UC_X86_REG_RCX),out,512,fmt,None,argument);assert length>=0;m.mem_write(m.reg_read(UC_X86_REG_RDX),out.value+b'\0');m.reg_write(UC_X86_REG_RAX,length)
  elif a==0x140002a80:
   ptr=m.reg_read(UC_X86_REG_RDX);calls.append(dict(snap=True,offset=ptr-n.owner,path='flat',state=normal(m.mem_read(ptr,288)).hex()))
  elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [shim,0x140002a80,0x1402bdee2,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def run(a,rcx,rdx=0,r8=0):
  sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,rcx);m.reg_write(UC_X86_REG_RDX,rdx);m.reg_write(UC_X86_REG_R8,r8);m.emu_start(a,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
 m.mem_write(n.owner,bytes(0x20000))
 for i in range(26):m.mem_write(n.owner+0x13ba0+i*288+0x108,struct.pack('<H',0xf0f))
 for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,0x193)]:m.reg_write(reg,value)
 m.emu_start(0x140048a2e,0x140048ab7,count=1000000)
 m.mem_write(n.owner+0x16050+0x108,struct.pack('<H',0xf0f));run(0x140001da0,n.owner+0x16050);run(0x140002980,n.manager,n.owner+0x16050,0x792);m.reg_write(UC_X86_REG_RBX,n.owner+0x16050);m.emu_start(0x14005588c,0x1400558af,count=10000)
 for slot in data['initialized']:
  actual=normal(m.mem_read(n.owner+slot['offset'],288));wanted=bytes.fromhex(slot['state']);assert actual==wanted,('initialization',hex(slot['offset']),[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:12]);digest.update(actual)
 file=bytearray.fromhex(data['decoded']['bytes'])
 for i,p in enumerate(data['decoded']['stageOffsets']):
  if p is not None:struct.pack_into('<Q',file,64+i*8,fileBase+p)
 for index,c in enumerate(data['scenes']):
  m.mem_write(n.owner,bytes(0x20000))
  for slot in data['baseline']:m.mem_write(n.owner+slot['offset'],native_vm(slot['state']))
  for i,r in enumerate(data['records']):m.mem_write(n.owner+0x7a18+i*120,bytes.fromhex(r['header']));m.mem_write(n.owner+0x7834+i*8,r['label'].encode()+b'\0')
  for p,key in [(0x168b0,'state'),(0x963c,'replaySelection'),(0x28,'selection'),(0x30,'pulse')]:m.mem_write(n.owner+p,struct.pack('<i',c['state'][key]))
  m.mem_write(n.owner+0x168b4,struct.pack('<i',c['count']));m.mem_write(n.owner+0x168b8,struct.pack('<Q',fileBase));m.mem_write(fileBase,bytes(file));m.mem_write(fontBase,bytes(0xdbb8));run(0x140009790,fontBase);calls.clear();m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R12,0x140000000);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140055266,0x1400556a7,count=1000000)
  assert calls==c['calls'],(index,'draw',calls[:1],c['calls'][:1]);assert normal(m.mem_read(n.owner+0x16050,288)).hex()==c['difficulty'],(index,'difficulty');font=bytearray(m.mem_read(fontBase,0xdbb8))
  for p in [0x10,0x130]:font[p:p+288]=normal(font[p:p+288])
  assert hashlib.sha256(font).hexdigest()==c['fontSha256'],(index,'ASCII');digest.update(font)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,scenes=len(data['scenes']),initializedVms=27,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-replay-draw-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'scenes':len(data['scenes']),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
