"""TH14 own replay header/stage construction and 455490 serialization.

Stop at the native compression entry. CRT memory, allocation, sprintf and
time are controlled boundaries. No native filesystem operation is executed.
"""
import hashlib,importlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]

def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,base,size,raw,n in img.sections:
  first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,img.data[raw:raw+n])
 base=0x70000000;m.mem_map(base,0x400000)
 manager,header,record,control,player,fps,name,stack= [base+v for v in (0x1000,0x2000,0x3000,0x4000,0x5000,0x30000,0x31000,0x3ff000)]
 heap=[base+0x100000];captured=[]
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def ret(v=0,cleanup=0):
  sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,v);m.reg_write(UC_X86_REG_ESP,sp+4+cleanup);m.reg_write(UC_X86_REG_EIP,get(sp))
 def boundary(machine,address,size,user):
  sp=m.reg_read(UC_X86_REG_ESP)
  if address==0x48f980:
   dst,val,n=get(sp+4),get(sp+8)&255,get(sp+12);m.mem_write(dst,bytes([val])*n);ret(dst)
  elif address==0x487620:
   dst,src,n=get(sp+4),get(sp+8),get(sp+12);m.mem_write(dst,bytes(m.mem_read(src,n)));ret(dst)
  elif address in (0x485540,0x4854af):
   n=get(sp+4);dst=heap[0];heap[0]+=(n+15)&~15;m.mem_write(dst,bytes(n));ret(dst)
  elif address==0x485ddf:
   m.mem_write(get(sp+4),b'test\0');ret(4)
  elif address==0x4654d0:
   p,n=m.reg_read(UC_X86_REG_ECX),m.reg_read(UC_X86_REG_EDX);captured.append(bytes(m.mem_read(p,n)));m.emu_stop()
 for a in (0x48f980,0x487620,0x485540,0x4854af,0x485ddf,0x4654d0):m.hook_add(UC_HOOK_CODE,boundary,begin=a,end=a)
 def run(start,end=base,ecx=0,args=()):
  m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,ecx);put(stack,base)
  for i,v in enumerate(args):put(stack+4+i*4,v)
  m.emu_start(start,end,count=1000000);assert m.reg_read(UC_X86_REG_EIP)==end,hex(m.reg_read(UC_X86_REG_EIP))
 # Default plus non-default controller tables, executing the whole initializer.
 configs=[];default_controller=img.read(0x4d6aac,20)
 for variant in range(17):
  table=default_controller if variant==0 else struct.pack('<10h',*[((variant*7+i*3)%31)-1 for i in range(10)])
  m.mem_write(0x4d6aac,table);m.mem_write(header,bytes([0xa5])*0x5c);run(0x4376e0,ecx=header)
  configs.append(dict(controller=table.hex(),config=bytes(m.mem_read(header,0x5c)).hex()))
 m.mem_write(0x4d6aac,default_controller)
 # Native difficulty tables and real start-power branch, without its player call.
 starts=[]
 for difficulty,stage in itertools.product(range(5),range(1,8)):
  put(0x4f5834,difficulty);put(0x4f58a4,stage);put(0x4f5860,100);put(0x4f585c,400)
  run(0x435caa,0x435cef);run(0x435da5,0x435e17)
  starts.append(dict(difficulty=difficulty,stage=stage,values=[get(p) for p in (0x4f584c,0x4f5850,0x4f5854,0x4f5858)]))
 cases=[]
 lengths=(0,1,29,30,31,899,900,901)
 specifications=[(selection,practice,[(1+((selection+length)%3)*3 if (selection+length)%3<2 else 7,length)]) for selection,practice,length in itertools.product(range(6),(False,True),lengths)]
 specifications += [(s,False,[(1,31),(3,901),(7,29)]) for s in range(6)]
 for case_id,(selection,practice,stage_specs) in enumerate(specifications):
  m.mem_write(manager,bytes(0x320));m.mem_write(header,bytes(0x94));m.mem_write(control,bytes(0x100));heap[0]=base+0x100000
  cfg=bytes.fromhex(configs[case_id%len(configs)]['config']);m.mem_write(control+0x24,cfg)
  put(0x4db688,manager);put(manager+0x1c,header);put(0x4db558,control);put(0x4db67c,player);put(0x4db54c,fps)
  m.mem_write(fps+0x24,struct.pack('<dd',58.5,60.0));flag=case_id%2;put(0x4d9658,flag)
  put(0x4f58b8,16 if practice else 0);stage_inputs=[]
  for stage_index,(stage,frames) in enumerate(stage_specs):
   h=record+stage_index*0x100;put(0x4f58a4,stage);seed=(0x9630+case_id*31+stage_index)&65535;put(0x4db510,seed)
   g=[(case_id*0x197731+i*0x10204081)&0xffffffff for i in range(28)]
   g[0]=selection//2;g[1]=selection%2;g[3]=case_id%5;g[4]=case_id%10;g[7]=0xffffffff
   m.mem_write(0x4f5828,struct.pack('<28I',*g));initial=stage_index==0
   if initial:
    m.mem_write(h,bytes(0xdc));put(manager+stage*4+0x20,h);m.reg_write(UC_X86_REG_EBX,manager);m.reg_write(UC_X86_REG_EDX,h)
    run(0x454714,0x45481d)
   else:
    run(0x456050);h=get(manager+stage*4+0x20)
    # Own stage-entry writer snapshots globals in ordinary (flag == 0) mode.
    # Provide that same snapshot when flag == 1, the explicit writer boundary.
    m.mem_write(h+0x14,struct.pack('<28I',*g))
   x,y=-4096+case_id*13,51200-case_id*7;weapon=case_id%2
   put(player+0x5ec,x);put(player+0x5f0,y);put(player+0x184b0,weapon)
   frame=stack-0x100;put(frame-4,h);m.reg_write(UC_X86_REG_EBP,frame);m.reg_write(UC_X86_REG_ESI,h);m.reg_write(UC_X86_REG_EBX,manager);run(0x455f3d,0x455f95)
   stage_header=bytes(m.mem_read(h,0xdc))
   inputs=b''.join(struct.pack('<HHH',(i*37+selection)&0xffff,(i*11)&0xffff,(i*13)&0xffff) for i in range(frames))
   terminal=case_id%3==0
   if terminal:inputs+=bytes([255])*6
   rates=bytes((55+i%6 for i in range((frames+29)//30)))
   stream_frames=frames+int(terminal)
   # Native linked blocks hold at most900 ticks; FPS bytes are concatenated
   # after all the input blocks. Use real linked-list traversal in455490.
   nodes=[]
   for block_index,first in enumerate(range(0,max(stream_frames,1),900)):
    block=base+0x40000+stage_index*0x20000+block_index*0x2000;node=block+0x1f00;nodes.append(node)
    part=inputs[first*6:(first+900)*6];ratepart=rates[first//30:(first+900)//30]
    m.mem_write(block,bytes(0x18b4));m.mem_write(block,part);m.mem_write(block+0x151c,ratepart)
    put(block+0x1518,block+len(part));put(block+0x18a0,block+0x151c+len(ratepart));put(node,block);put(node+4,0)
    if len(nodes)>1:put(nodes[-2]+4,node)
   put(manager+0x44+stage*16,nodes[0]);put(manager+0xc0,nodes[-1])
   stage_inputs.append(dict(number=stage,initial=initial,header=stage_header.hex(),inputs=inputs.hex(),fps=rates.hex(),terminal=terminal,liveFrames=frames))
  timestamp=0x12345678655ff991;m.mem_write(header+0xc,struct.pack('<Q',timestamp));reached=8 if case_id%2 else stage_specs[-1][0];put(header+0x88,reached)
  score=123456789+case_id;put(0x4f5830,score);name_text='QA' if case_id%2 else 'PORTTH14';m.mem_write(name,name_text.encode()+b'\0')
  captured.clear();m.reg_write(UC_X86_REG_ESP,stack)
  # args: save slot, name, unknown, terminal. The marker is already supplied
  # in the native input buffer, so terminal append is disabled for this run.
  put(stack,base)
  for i,v in enumerate((0,name,0,0)):put(stack+4+i*4,v)
  m.emu_start(0x455490,base,count=1000000);assert len(captured)==1
  cases.append(dict(selection=selection,difficulty=case_id%5,practice=practice,timestampLow=timestamp&0xffffffff,timestampHigh=timestamp>>32,config=cfg.hex(),name=name_text,score=score,reached=reached,continues=case_id%10,slowdown=2.5,stages=stage_inputs,decoded=captured[0].hex()))
 out=ROOT/'artifacts/th14/replay-writer-native.json';out.write_text(json.dumps(dict(executableSha256=hashlib.sha256(img.data).hexdigest(),configs=configs,starts=starts,cases=cases),separators=(',',':'))+'\n',encoding='utf8')
 print(f'{len(configs)} native configs / {len(starts)} starts / {len(cases)} native serialized replay bodies')
if __name__=='__main__':main()
