"""Replay decode 6b00b..6b0e0 and assembled-file encode 6c908..6c93f.

Actual checksum, cipher, string termination and stage relocation execute.
Native pointer relocations are normalized to relative file offsets. File I/O,
record assembly/recording/playback and unsafe native bounds are excluded.
"""
import json,struct,subprocess,hashlib
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/replay-file.mjs';h=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{encodeReplayFile,decodeReplayFile}from'./shared/th06nc/replay-file.mjs';const scenes=[],hex=b=>Buffer.from(b).toString('hex');for(const size of [120,121,127,128,129,255,512,4096])for(const seed of [0,1,127,255]){const plain=Uint8Array.from({length:size},(_,i)=>(i*31+seed)&255),v=new DataView(plain.buffer);v.setUint32(0,0x50523654,true);v.setUint16(4,0x10f,true);plain[18]=seed;plain.set(new TextEncoder().encode('26/11/15\\0'),20);plain.set(new TextEncoder().encode('NATIVE  \\0'),29);for(let i=0;i<7;i++)v.setBigUint64(64+i*8,i===0&&size>120?120n:0n,true);const encoded=encodeReplayFile(plain),decoded=decodeReplayFile(encoded),bad=encoded.slice();bad[119]^=1;let rejected=false;try{decodeReplayFile(bad);}catch{rejected=true;}if(!rejected)throw Error('Corruption accepted');if(hex(encodeReplayFile(decoded.bytes))!==hex(encoded))throw Error('Round-trip mismatch');scenes.push({plain:hex(plain),encoded:hex(encoded),decoded:hex(decoded.bytes),bad:hex(bad)});}let truncated=0;for(const size of [0,4,18,119])try{decodeReplayFile(new Uint8Array(size));throw Error('Accepted');}catch(e){if(e.message==='Accepted')throw e;truncated++;}console.log(JSON.stringify({scenes,truncated}));
""";data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;buffer=n.assets+0x100000;rejected=False;digest=hashlib.sha256()
 def hook(m,a,size,u):
  nonlocal rejected
  rejected=True;m.reg_write(UC_X86_REG_RIP,0x14006b0e0)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x14006b0f3,end=0x14006b0f3)
 for i,s in enumerate(data['scenes']):
  plain=bytes.fromhex(s['plain']);m.mem_write(buffer,plain);m.reg_write(UC_X86_REG_R15,buffer);m.reg_write(UC_X86_REG_RSI,len(plain));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14006c908,0x14006c93f,count=1000000);encoded=bytes(m.mem_read(buffer,len(plain)));assert encoded.hex()==s['encoded'],(i,'encode');digest.update(encoded)
  for kind in ['encoded','bad']:
   rejected=False;m.mem_write(buffer,bytes.fromhex(s[kind]));m.reg_write(UC_X86_REG_RBX,buffer);m.reg_write(UC_X86_REG_ESI,len(plain));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14006b00b,0x14006b0e0,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==0x14006b0e0
   if kind=='bad':assert rejected,(i,'corruption');continue
   assert not rejected,(i,'decode');actual=bytearray(m.mem_read(buffer,len(plain)))
   for p in range(64,120,8):
    ptr=struct.unpack_from('<Q',actual,p)[0]
    if ptr:struct.pack_into('<Q',actual,p,ptr-buffer)
   assert actual.hex()==s['decoded'],(i,'decode',actual[:120].hex(),s['decoded'][:240]);digest.update(actual)
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==h;report=dict(scope=__doc__,encoded=len(data['scenes']),decoded=len(data['scenes']),corruptRejected=len(data['scenes']),strictTruncations=data['truncated'],stateSha256=digest.hexdigest(),sourceSha256={source:h},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-file-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
