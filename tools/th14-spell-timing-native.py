"""Full retail41c800 sampler; only its external monotonic clock is controlled."""
import hashlib,importlib,json,struct,itertools,random
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,SPELL,GAME,REPLAY,HEADER,CLOCK,STACK,RETURN=(0x70000000+x for x in (0,0x1000,0x3000,0x4000,0x5000,0x6000,0x1f000,0x20000))
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  start=base&~4095;m.mem_map(start,((base+size+4095)&~4095)-start);m.mem_write(base,img.data[raw:raw+n])
 m.mem_map(BASE,0x30000)
 def invalid(uc,access,address,size,value,user):
  print('unmapped',hex(uc.reg_read(UC_X86_REG_EIP)),hex(address));return False
 m.hook_add(UC_HOOK_MEM_INVALID,invalid)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 # movsd xmm0,[CLOCK]; ret. CRT fmod, floor, encode/checksum stay original.
 m.mem_write(0x46ac20,b'\xf2\x0f\x10\x05'+struct.pack('<I',CLOCK)+b'\xc3')
 constants=[struct.unpack('<d',m.mem_read(p,8))[0] for p in (0x4c1a00,0x4c1a20,0x4c1ab0)]
 assert constants==[.00835,.0167,100.0],constants
 def call(now):
  m.mem_write(CLOCK,struct.pack('<d',now));put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK)
  m.emu_start(0x41c800,RETURN,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
 def state():return dict(flags=get(SPELL+0x7c),frames=get(SPELL+0x94),encoded=get(SPELL+0xa8),index=get(SPELL+0x8c),startWords=list(struct.unpack('<2I',m.mem_read(SPELL+0x98,8))),records=list(struct.unpack('<20I',m.mem_read(HEADER+0x88,80))))
 def encode(s,h):return ((s+h+22)*1000+(s+66)%1000)*100+(h+33)%100
 deltas=[0,.008349999,.00835,.008350001,.0167,.999,1,59.999,60,99.99,100,120,933,934,999,1000,1234.5,-.1,-1,-100,.1,.2,.3,.4,.5,.6]
 rng=random.Random(411800);cases=[]
 for i in range(600):
  delta=deltas[i] if i<len(deltas) else rng.randrange(10000000)/10000
  start=0 if i<len(deltas) or i%3==0 else rng.randrange(10000000)/1000
  encoded=[0,0x6ad1584,0x6ae9c24,encode(120,99),encode(934,0),encode(999,99),rng.randrange(0x100000000)][i%7]
  cases.append(dict(start=start,now=start+delta,frames=rng.randrange(60000),flags=(i%8)<<8,replay=i>=400,index=i%20,record=encoded))
 rows=[]
 for c in cases:
  m.mem_write(BASE,bytes(0x21000));put(0x4db534,SPELL);put(0x4db558,GAME);put(0x4db688,REPLAY);put(0x4f58a4,1)
  put(GAME+0x94,int(c['replay']));put(REPLAY+0x24,HEADER);put(REPLAY+0x100,HEADER);put(SPELL+0x90,c['frames']);put(SPELL+0x8c,c['index']);put(SPELL+0x7c,c['flags']|1)
  for n in range(20):put(HEADER+0x88+n*4,c['record'] if n==c['index'] else n*0xdeaddead)
  m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  call(c['start']);first=state();put(SPELL+0x7c,first['flags']&~1);call(c['now']);rows.append(dict(**c,first=first,last=state()))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),rows=rows,constants=constants,scope='Full41c800 start/end sampler, original CRT fmod/floor, rounding threshold, three-digit wrapped encoding, actual41bf60 replay checksum and invalid sentinel;20-entry recording/replay headers controlled. Only external46ac20 clock is replaced with a controlled double. Negative/zero/long and boundary times, varied flags/index/record values. Does not prove browser clock resolution, callback order, physical audio/GPU or natural card captures.')
 (ROOT/'artifacts/th14/spell-timing-native.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} full retail spell clock samples')
if __name__=='__main__':main()
