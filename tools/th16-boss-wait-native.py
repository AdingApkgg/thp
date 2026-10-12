"""Retail TH16 boss ID registration, lookup and three-slot wait."""
import hashlib,importlib,json,struct
from pathlib import Path
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(16);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(0x70000000,0x40000);manager,enemy,stack=0x70001000,0x70004000,0x7003e000
 put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
 get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
 put(0x4a6dc0,manager);nodes=[0x70002000+j*32 for j in range(3)];peers=[0x70010000+j*0x6000 for j in range(3)]
 for j,p in enumerate(peers):put(p+0x5740,(j+1)*11);put(nodes[j],p);put(nodes[j]+4,nodes[j+1] if j<2 else 0)
 selected=[0]
 def arg(machine,address,size,user):machine.reg_write(UC_X86_REG_EAX,selected[0]&0xffffffff)
 m.mem_write(0x4251d0,b'\xc2\x04\x00');m.hook_add(UC_HOOK_CODE,arg,begin=0x4251d0,end=0x4251d0)
 m.hook_add(UC_HOOK_CODE,lambda machine,address,size,user:machine.emu_stop(),begin=0x422a9d,end=0x422a9d)
 registrations=[]
 for flags in (0,0x800000,0xffffffff):
  for mf in (0,1,0xffffffff):
   for prior in (0,3):
    for slot in range(-1,4):
     for j in range(16):put(manager+0x48+j*4,100+j)
     put(manager+0x88,mf);put(enemy+0x4060,flags);put(enemy+0x4070,prior);put(enemy+0x44b8,peers[1]);selected[0]=slot
     m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,enemy)
     m.emu_start(0x42065a,0x422a9b,count=10000);assert m.reg_read(UC_X86_REG_EIP)==0x422a9b
     registrations.append([flags,mf,prior,slot,get(enemy+0x4060),get(enemy+0x4070),get(manager+0x88),*[get(manager+0x48+j*4) for j in range(4)]])
 lookups=[];waits=[]
 for length in range(4):
  put(manager+0x180,nodes[0] if length else 0)
  for j in range(3):put(nodes[j]+4,nodes[j+1] if j+1<length else 0)
  for slot in range(4):
   for id in (0,11,22,33,999,0xffffffff):
    put(manager+0x48+slot*4,id);put(stack,0x70000000);put(stack+4,slot);m.reg_write(UC_X86_REG_ESP,stack)
    m.emu_start(0x417580,0x70000000,count=10000);p=m.reg_read(UC_X86_REG_EAX);assert p==0 or p in peers
    lookups.append([length,slot,id,0 if not p else peers.index(p)+1])
  for mask in range(16):
   for j in range(16):put(manager+0x48+j*4,11 if mask&(1<<j) else 0)
   m.reg_write(UC_X86_REG_ESP,stack);m.emu_start(0x421708,0x422a9b,count=10000)
   waits.append([length,mask,0 if m.reg_read(UC_X86_REG_EIP)==0x422a9b else 0xffffffff])
 ids=[]
 for counter in (0,1,2,0x7fffffff,0xfffffffe,0xffffffff):
  put(manager+0x90,counter);m.reg_write(UC_X86_REG_ECX,manager);m.reg_write(UC_X86_REG_EDI,enemy);m.reg_write(UC_X86_REG_EDX,1)
  m.emu_start(0x41b85f,0x41b883,count=1000);ids.append([counter,get(enemy+0x5740),get(manager+0x90),get(manager+0x94)])
 flag_rows=[];visible=[]
 def visibility(machine,address,size,user):visible.append([get(m.reg_read(UC_X86_REG_ECX)),int(address==0x46f300)])
 for addr in (0x46f300,0x46f340):
  m.mem_write(addr,b'\xc3');m.hook_add(UC_HOOK_CODE,visibility,begin=addr,end=addr)
 for op in (502,503):
  for flags in (0,0x20,0xffffffff):
   for bits in (0,0x20,0xc,0x40000000,0x800000,0xffffffff):
    put(enemy+0x4060,flags);selected[0]=bits;visible.clear()
    for j in range(16):put(enemy+0x124+j*4,100+j)
    m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,enemy)
    m.emu_start(0x420493 if op==502 else 0x4204cb,0x422a9b,count=10000)
    flag_rows.append(dict(op=op,flags=flags,bits=bits,after=get(enemy+0x4060),visibility=visible.copy()))
 spell_rows=[]
 m.mem_write(0x7003f000,b'\xd9\x1d'+struct.pack('<I',0x7003d000))
 for value in (-1,0,1,17,2147483647,-2147483648,16777217,1234):
  put(0x4a57c8,value)
  for floating in (0,1):
   put(stack,0x7003f000 if floating else 0x70000000);put(stack+4,-9907);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,enemy)
   m.emu_start(0x424110 if floating else 0x423810,0x7003f006 if floating else 0x70000000,count=10000)
   spell_rows.append([value,floating,get(0x7003d000) if floating else m.reg_read(UC_X86_REG_EAX)])
 out=ROOT/'artifacts/th16/boss-wait-native.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),registrations=registrations,lookups=lookups,waits=waits,constructorIds=ids,flagRows=flag_rows,spellPracticeReads=spell_rows,scope='Retail512 registration handler42065a through tail422a9b, actual41a950/41a910 helpers, controlled argument resolver4251d0. Complete417580 lookup and421708 three-slot wait over0..3 synthetic peers, matching/missing/zero IDs and four boss slots. Indices4+ are deliberately unsupported, outside the identified ID table. Constructor ID allocation fragment41b85f..41b883 with zero-wrap replacement EDX=1. Retail502/503 execute flag stores and sixteen visibility requests; 46f300/46f340 are controlled recorders, not family visibility proofs. Full423810/424110 getter dispatch for -9907 reads actual4a57c8 as i32 or x87 float32. No whole constructor/first frame, death, damage, ECL518 cancels, GPU or complete gameplay claim.'),separators=(',',':'))+'\n')
 print(len(registrations),'registrations,',len(lookups),'lookups,',len(waits),'waits')
if __name__=='__main__':main()
