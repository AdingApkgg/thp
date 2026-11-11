"""Execute original HUD producers, queue40b9b0 and text40bf20 at six sizes.

CRT formatting, atlas binding, geometry and GPU remain declared services.
"""
import hashlib,importlib,itertools,json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
BASE,SUP,HUD,RESULT,TIME,SPELL,RESOURCE,ATLAS,REQUEST,STACK,RETURN=(0x70000000+n for n in (0,0x10000,0x40000,0x44000,0x45000,0x46000,0x47000,0x48000,0x50000,0x70000,0x80000))
def main():
 img,_,_=importlib.import_module('th-anm-handlers').handlers(14);m=Uc(UC_ARCH_X86,UC_MODE_32)
 for _,b,size,raw,n in img.sections:
  start=b&~4095;m.mem_map(start,((b+size+4095)&~4095)-start);m.mem_write(b,img.data[raw:raw+n])
 m.mem_map(BASE,0x90000)
 def put(p,v):m.mem_write(p,struct.pack('<I',v&0xffffffff))
 def get(p):return struct.unpack('<I',m.mem_read(p,4))[0]
 def signed(p):return struct.unpack('<i',m.mem_read(p,4))[0]
 def flt(p):return struct.unpack('<f',m.mem_read(p,4))[0]
 def string(p):return bytes(m.mem_read(p,256)).split(b'\0')[0].decode('ascii')
 def formatted(fmt,args):
  n=len(re.findall(r'%(?:\d+)?(?:\.\d+)?d',fmt));return fmt%tuple(signed(args+4*i) for i in range(n)) if n else fmt
 queued=[];glyphs=[];phase='producer'
 def record(text,p):queued.append(dict(text=text,position=[flt(p+i*4) for i in range(3)],color=get(SUP+0x191b0),scale=[flt(SUP+0x191b4),flt(SUP+0x191b8)],font=get(SUP+0x191c8),shadow=get(SUP+0x191c4),passIndex=get(SUP+0x191cc),horizontal=get(SUP+0x191d4),vertical=get(SUP+0x191d8)))
 def hook(uc,a,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP)
  if a==0x485ddf:
   text=formatted(string(get(sp+8)),sp+12);uc.mem_write(get(sp+4),text.encode()+b'\0');uc.reg_write(UC_X86_REG_EAX,len(text))
  elif a==0x40bb10:record(formatted(string(get(sp+12)),sp+16),get(sp+8))
  elif a==0x40b9b0 and phase=='producer':record(string(get(sp+8)),get(sp+4))
  elif a==0x40caf0:put(SUP+0x40,get(sp+4))
  elif a==0x4756e0:glyphs.append(dict(sprite=(get(SUP+0x40)-ATLAS)//72,x=flt(SUP+0x50),y=flt(SUP+0x54),color=get(SUP+0x548),filtered=bool(get(SUP+0x30)&0x400)))
  elif a==0x47f0a0:uc.reg_write(UC_X86_REG_EAX,RESULT if get(sp+4)==1 else TIME if get(sp+4)==2 else 0)
 for a,cleanup in ((0x485ddf,0),(0x40bb10,0),(0x40b9b0,8),(0x4854a0,0),(0x40caf0,4),(0x476100,20),(0x4756e0,8),(0x47f0a0,4),(0x47f6e0,0)):
  m.mem_write(a,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3');m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 m.hook_add(UC_HOOK_CODE,lambda *args:m.emu_stop(),begin=0x43144a,end=0x43144a)
 def encode(seconds,hund):return ((seconds+hund+22)*1000+(seconds+66)%1000)*100+(hund+33)%100
 cases=[dict(width=width,bonus=bonus,alpha=80,result=result,time=2,show=1,manager=1,frames=frames,encoded=encode(120,99))for width,bonus,result,frames in itertools.product([480,640,800,801,960,1280],[0,99,1000,3000000,1000000000,-1],[0,1],[59,60])]
 rows=[]
 for c in cases:
  width=c['width']
  m.mem_write(BASE,bytes(0x90000));queued.clear();glyphs.clear();phase='producer';m.mem_write(0x40b9b0,b'\xc2\x08\x00');m.ctl_remove_cache(0x40b9b0,0x40bb10)
  for p,v in ((0x4db520,SUP),(0x4f56cc,BASE+0x60000),(0x4db534,SPELL if c['manager'] else 0),(HUD+0x110,c['result']),(HUD+0x118,c['time']),(HUD+0x11c,c['show']),(HUD+0x2a8,c['bonus']),(SPELL+0x94,c['frames']),(SPELL+0xa8,c['encoded']),(RESULT+0x534,0x00ffffff|(c['alpha']<<24)),(TIME+0x534,0x00ffffff|(c['alpha']<<24)),(SUP+0x191b0,0xffffffff),(SUP+0x191b4,0x3f800000),(SUP+0x191b8,0x3f800000),(SUP+0x191d4,1),(SUP+0x191d8,1)):put(p,v)
  put(STACK,RETURN);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,HUD);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
  m.emu_start(0x431140,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==0x43144a
  phase='draw';m.mem_write(0x40b9b0,img.read(0x40b9b0,0x160));m.ctl_remove_cache(0x40b9b0,0x40bb10)
  for q in queued[:]:
   m.mem_write(REQUEST,bytes(0x138));m.mem_write(REQUEST,q['text'].encode()+b'\0');m.mem_write(REQUEST+0x100,struct.pack('<3fI2f',*q['position'],q['color'],*q['scale']))
   for off,v in ((0x120,q['font']),(0x124,q['shadow']),(0x128,q['passIndex']),(0x130,q['horizontal']),(0x134,q['vertical'])):put(REQUEST+off,v)
   put(SUP+0x191e4,RESOURCE);put(RESOURCE+0x11c,ATLAS);put(SUP+0x191dc,9);m.mem_write(0x4f7a6c,struct.pack('<f',width/640.))
   for off,v in [(0x191b0,q['color']),(0x191c8,q['font']),(0x191c4,q['shadow']),(0x191cc,q['passIndex']),(0x191d4,q['horizontal']),(0x191d8,q['vertical']),(0x191ac,0)]:put(SUP+off,v)
   m.mem_write(SUP+0x191b4,struct.pack('<2f',*q['scale']));put(0x4f7a80,width//2);put(0x4f7a84,int(width/640.*16))
   put(STACK,RETURN);put(STACK+4,REQUEST+0x100);put(STACK+8,REQUEST);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP)
   m.emu_start(0x40b9b0,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN and get(SUP+0x191ac)==1
   put(STACK,RETURN);put(STACK+4,SUP+0xbac);m.reg_write(UC_X86_REG_ESP,STACK);m.reg_write(UC_X86_REG_ECX,SUP);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   m.emu_start(0x40bf20,RETURN,count=100000);assert m.reg_read(UC_X86_REG_EIP)==RETURN
  rows.append(dict(**c,requests=queued[:],glyphs=glyphs[:]))
 report=dict(executableSha256=hashlib.sha256(img.data).hexdigest(),originalQueue40b9b0Executed=True,originalTextTraversal40bf20Executed=True,stableDeviceSizeWithinQueueDrawDeclared=True,crtAtlasAndGpuDeclaredServices=True,newGameRuns=0,newGpuRuns=0,rows=rows,scope='144 declared bonus/time cases across six display sizes; original431140..43144a, grouping, encoded-time helpers, queue40b9b0 and traversal40bf20 execute. CRT, lookup/retirement, atlas, geometry and GPU are declared services; no VM-retirement or pixel acceptance.')
 (ROOT/'artifacts/th14/ascii-queue-layout-nov12/hud-awards-native-v2.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(f'PASS {len(rows)} original awards/time layouts; {sum(len(r["glyphs"]) for r in rows)} glyphs')
if __name__=='__main__':main()
