"""Capture actual 4fdd0 spell-menu information refresh for a later JS comparison.

Controlled services: localization map/strings/printf, memory
primitives, cookie and lazy catalog load. Native control flow, record queries,
sprite setters and post-publication layout execute. Publication is a no-op by
default; --native-font executes actual 7530 with independently evaluated glyph
metadata at the GPU font service boundary. This is reference capture,
not a claim that the browser information owner is implemented or verified.
"""
import hashlib,json,re,struct,subprocess,sys
import msgpack
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 resource=ROOT/'runtimes/th06nc/artifacts/scripts/th06IN.dat/localization.msgpack';localization=msgpack.unpackb(resource.read_bytes(),raw=False)
 table=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{readFileSync}from'node:fs';import{readSpellPracticeTable}from'./shared/th06nc/spell-practice-table.mjs';console.log(JSON.stringify(readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack'))));"],cwd=ROOT))
 refs=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{selectionResources}from'./shared/th06nc/title-selection-layout.mjs';import{spellMenuAsset}from'./shared/th06nc/spell-practice-layout.mjs';console.log(JSON.stringify([...selectionResources,spellMenuAsset,{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f}]));"],cwd=ROOT));n=Native();n.load_title(refs);m=n.m;catalog=n.assets+0x100000;heap=0x75000000;m.mem_map(heap,0x800000);cursor=heap;events=[];lookups=[];language='zh-CN';native_font='--native-font'in sys.argv;glyph_cache={};font_files={};available={f['stem']for f in json.loads((ROOT/'artifacts/th06nc/fonts.json').read_text(encoding='utf-8'))['fonts']if f['bitmapAvailable']}
 for i,r in enumerate(table):
  b=bytearray(40);struct.pack_into('<BBHBBB',b,0,r['id'],r['stageIndex'],r['subroutine'],r['difficulty'],r['order'],r['midboss']);text=r['name'].encode();b[7:7+len(text)]=text;m.mem_write(catalog+i*40,bytes(b))
 m.mem_write(0x140c221c0,struct.pack('<Q',catalog));m.mem_write(0x140c2208c,struct.pack('<I',len(table)));map_pointer=n.vm+0x1000;sentinel=n.vm+0x1100;m.mem_write(0x140a6ec28,struct.pack('<Q',map_pointer));m.mem_write(map_pointer+8,struct.pack('<Q',sentinel))
 def alloc(data):
  nonlocal cursor
  p=cursor;cursor+=(len(data)+15)&~15;assert cursor<heap+0x800000;m.mem_write(p,data);return p
 def cstring(p):return bytes(m.mem_read(p,1024)).split(b'\0')[0].decode('utf-8')
 def string(p):
  length,capacity=struct.unpack('<2Q',m.mem_read(p+16,16));pointer=struct.unpack('<Q',m.mem_read(p,8))[0]if capacity>15 else p;return bytes(m.mem_read(pointer,length)).decode('utf-8')
 def set_string(p,data):
  m.mem_write(p,bytes(32));m.mem_write(p,struct.pack('<Q',alloc(data+b'\0')));m.mem_write(p+16,struct.pack('<2Q',len(data),max(16,len(data))))
 def hook(m,a,size,u):
  sp=m.reg_read(UC_X86_REG_RSP);rcx=m.reg_read(UC_X86_REG_RCX);rdx=m.reg_read(UC_X86_REG_RDX);r8=m.reg_read(UC_X86_REG_R8);r9=m.reg_read(UC_X86_REG_R9)
  if a==0x140008350:set_string(rcx,bytes(m.mem_read(rdx,r8)));m.reg_write(UC_X86_REG_RAX,rcx)
  elif a==0x14000d0d0:
   key=string(r8);lookups.append(key);value=localization.get(key,{}).get(language);node=0
   if value is not None:node=alloc(bytes(0x50));set_string(node+0x30,value.encode())
   m.mem_write(rdx,struct.pack('<2Q',0,node));m.reg_write(UC_X86_REG_RAX,rdx)
  elif a==0x140013020:
   fmt=cstring(r8);tokens=list(re.finditer(r'%(?:[-+0 #]*\d*(?:\.\d+)?)(?:I64|ll|l)?[sudi%xX]',fmt));args=[];i=0
   for token in tokens:
    spec=token.group()
    if spec=='%%':continue
    value=r9 if i==0 else struct.unpack('<Q',m.mem_read(sp+0x28+(i-1)*8,8))[0];i+=1
    if spec.endswith('s'):value=cstring(value)
    elif spec.endswith(('d','i')):value=value&0xffffffff;value=value-(1<<32)if value>=1<<31 else value
    elif not any(x in spec for x in ['ll','I64']):value&=0xffffffff
    args.append(value)
   normalized=re.sub(r'%([-+0 #]*\d*(?:\.\d+)?)(?:I64|ll|l)([udi%xX])',r'%\1\2',fmt);text=normalized%tuple(args);data=text.encode();assert len(data)<rdx,(fmt,text,rdx);m.mem_write(rcx,data+b'\0');m.reg_write(UC_X86_REG_RAX,len(data))
  elif a==0x14007d2c0:
   font_size=struct.unpack('<I',m.mem_read(sp+0x28,4))[0];colors=[struct.unpack('<I',m.mem_read(sp+p,4))[0]for p in [0x38,0x40,0x60,0x68]];key=str(font_size)+'_'+('_'.join(f'0x{x:08X}'for x in colors))+'_'+language
   if key in available:
    if key not in glyph_cache:
     directory=ROOT/'runtimes/th06nc/artifacts/fonts';meta_path=directory/(key+'.json');advance_path=directory/('advance_'+key+'.txt');glyphs={}
     font_files[key]=dict(metadataSha256=hashlib.sha256(meta_path.read_bytes()).hexdigest(),advanceSha256=hashlib.sha256(advance_path.read_bytes()).hexdigest())
     for line in advance_path.read_text(encoding='utf-8').splitlines():
      if line:cp,advance=line.split('\t');glyphs[int(cp,16)]=dict(advance=float(advance),source=[0,0,0,0])
     for frame in json.loads(meta_path.read_text(encoding='utf-8'))['frames']:
      cp=int(frame['filename'],16);r=frame['frame'];glyphs.setdefault(cp,dict(advance=0))['source']=[r['x'],r['y'],r['w'],r['h']]
     glyph_cache[key]=glyphs
    glyphs=glyph_cache[key];pointer=struct.unpack('<Q',m.mem_read(sp+0x48,8))[0];text=cstring(pointer);x=rcx&0xffffffff;y=rdx&0xffffffff;current_x=x;fraction=0;width=0;height=0
    for ch in text:
     g=glyphs.get(ord(ch));advance=18
     if g:
      width=g['source'][2]-x+current_x;height=max(height,g['source'][3]);integer=int(g['advance']);fraction+=g['advance']-integer;advance=integer
      if fraction>=1:advance+=1;fraction-=1
     current_x=int(current_x+advance)
    destination=struct.unpack('<Q',m.mem_read(sp+0x58,8))[0];m.mem_write(destination,struct.pack('<4i',x,y,width,height))
  elif a==0x140007530:
   pointer=struct.unpack('<Q',m.mem_read(sp+0x38,8))[0];events.append(dict(offset=rdx-n.owner,sprite=struct.unpack('<H',m.mem_read(rdx+0x34,2))[0],text=cstring(pointer),colors=[r8&0xffffffff,r9&0xffffffff,*struct.unpack('<2I',m.mem_read(sp+0x28,4)+m.mem_read(sp+0x30,4))],size=list(m.mem_read(rdx+0x108,2))))
   if native_font:return
  elif a in [0x1402bdee2,0x1402bdee8]:
   m.mem_write(rcx,bytes([rdx&255])*r8 if a==0x1402bdee2 else bytes(m.mem_read(rdx,r8)));m.reg_write(UC_X86_REG_RAX,rcx)
  m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in [0x14007d2c0,0x140008350,0x140008410,0x14000d0d0,0x140013020,0x140007530,0x1402bdee2,0x1402bdee8,0x1402bcf20,0x140076b90]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 cases=[]
 for language in ['zh-CN','en']:
  for owner in [28,29,30]:
   for stage in range(7):
    for profile in range(4):
     for record_mode in range(5):
      unlocked=record_mode!=0
      cursor=heap;events.clear();lookups.clear();m.mem_write(n.owner,bytes(0x20000));m.mem_write(0x1404f27c8,bytes(134*384));m.mem_write(0x140c22138,bytes(8));m.mem_write(0x1404f1e80,bytes([profile>>1,profile&1]));rows=[r for r in table if r['stageIndex']==stage];order=max(r['order']for r in rows)if profile&1 else 0;row=next(r for r in rows if r['order']==order)
      for offset,value in [(0x168b0,owner),(0x168dc,stage),(0x168e0,order),(0x168e4,max(0,order-7)),(0x168e8,0 if stage==6 else row['difficulty'])]:m.mem_write(n.owner+offset,struct.pack('<i',value))
      m.mem_write(n.owner+0x168d3,b'\1')
      for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RDI,8),(UC_X86_REG_R14,0x17d)]:m.reg_write(reg,value)
      m.emu_start(0x14004c781,0x14004ca1a,count=1000000)
      if unlocked:
       for r in table:
        attempted=record_mode in [1,4] or(record_mode==2 and r['midboss']!=0)or(record_mode==3 and r['id']%3!=0);captured=attempted and record_mode!=4 and(record_mode!=3 or r['id']%2!=0);base=0x1404f27c8+r['id']*384;m.mem_write(base+0x3c,struct.pack('<2H',17 if attempted else 0,5 if attempted else 0));m.mem_write(base+0x40+(r['difficulty']*4+profile)*8,struct.pack('<Q',0x123456789abc+r['id']*100));m.mem_write(base+0xe0+(r['difficulty']*4+profile)*4,struct.pack('<I',11));m.mem_write(base+0x130+(r['difficulty']*4+profile)*4,struct.pack('<I',3 if captured else 0))
      sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner)
      try:m.emu_start(0x14004fdd0,n.stack+0xf000,count=1000000)
      except Exception:print('native failure',owner,stage,profile,unlocked,hex(m.reg_read(UC_X86_REG_RIP)),bytes(m.mem_read(m.reg_read(UC_X86_REG_RSP),16)).hex());raise
      assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
      vms=[]
      for offset in sorted({e['offset']for e in events}):
       b=bytearray(m.mem_read(n.owner+offset,288));p=struct.unpack_from('<Q',b,0x100)[0]
       if p:struct.pack_into('<Q',b,0x100,(p-n.manager-0x608)//64+1)
       vms.append(dict(offset=offset,bytes=b.hex()))
      cases.append(dict(language=language,owner=owner,stage=stage,profile=profile,unlocked=unlocked,recordMode=record_mode,completeFlags=list(m.mem_read(n.owner+0x16928,7)),order=order,scroll=max(0,order-7),difficulty=0 if stage==6 else row['difficulty'],lookups=list(lookups),requests=list(events),vms=vms))
 report=dict(scope=__doc__,publicationMode='native-font'if native_font else'no-op',fontFiles=font_files,executableSha256=n.target['sha256'],localizationSha256=hashlib.sha256(resource.read_bytes()).hexdigest(),cases=cases)
 out=ROOT/('artifacts/th06nc/spell-info-native-font-cases.json'if native_font else'artifacts/th06nc/spell-info-native-cases.json');out.write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf-8');print(json.dumps({'capturedCases':len(cases),'textRequests':sum(len(c['requests'])for c in cases),'artifact':out.relative_to(ROOT).as_posix()}))

if __name__=='__main__':main()
