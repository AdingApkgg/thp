"""Execute the entire retail text wrapper and raster, using literal formatter delivery."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'tools/th14-font-device-raster-native.py').read_text(encoding='utf8')
source=source.replace("output=ROOT/'artifacts/th14/font-device-raster-native'","output=ROOT/'artifacts/th14/font-alignment-native'")
source=source.replace("  elif name=='color':", "  elif name=='format':m.mem_write(get(sp+4),plain+b'\\0');result=len(plain)\n  elif name=='color':")
source=source.replace(" calls={a:(name,pop) for a,name,pop in shims.values()};", " calls={a:(name,pop) for a,name,pop in shims.values()};calls[0x4859cd]=('format',0);")
setup=""" vm=arena+0x6000;sprite=arena+0x7000;deliveries=[]
 holder=arena+0x8000;put(holder,texture);put(vm+0x2c,sprite);put(sprite+8,holder)
 for i,v in enumerate((0.,0.,512.,32.)):m.mem_write(sprite+0xc+i*4,struct.pack('<f',v))
 m.mem_write(sprite+0x38,struct.pack('<f',512.))
 def observe_delivery(uc,address,size,user):
  sp=uc.reg_read(UC_X86_REG_ESP);args=[get(sp+i*4) for i in range(1,9)]
  deliveries.append(dict(height=args[0],color=args[1],outline=args[2],font=sint(args[5]),spacing=args[6],shadow=args[7],offset=sint(uc.reg_read(UC_X86_REG_EDX))))
 m.hook_add(UC_HOOK_CODE,observe_delivery,begin=0x467ba0,end=0x467ba0)
"""
source=source.replace(' try:\n',setup+' try:\n',1)
start=source.index('  for font in');end=source.index(' finally:',start)
loop="""  for font,profile,alignment in __import__('itertools').product((*range(8),-1,8),range(8),range(3)):
   height=(16,17,20,17,23,17,32,17)[profile];offset=(-3,0,4,2,3,0,-1,17)[profile];foreground=(0x123456,0xffffff,0x817364,0x334455,0xfa3721,0,0x63e581,0x182944)[profile];outline=0;spacing=(0,0,0,12,20,0,0,12)[profile];shadow=profile not in (2,7);plain=(b'Text012: iWj',bytes.fromhex('938c95fb'),b'Text012: iWj',bytes.fromhex('938c95fb'),b'Odd',b'',bytes.fromhex('b1b2b3dedf'),bytes.fromhex('926e97ec9361817596b2917a8176'))[profile]
   m.mem_write(pixels,bytes(1024*128*2));m.mem_write(text,plain+b'\\0');m.mem_write(rect,struct.pack('<iiii',0,0,512,32));put(stack,arena)
   m.mem_write(vm+0x528,bytes([height]));put(vm+0x1c,0 if shadow else 0x800);put(vm+0x18,0xa4)
   args=(0,vm,foreground,outline,font,offset,spacing//2,arena+0x5000) if alignment==0 else (0,vm,foreground,outline,font,spacing//2,arena+0x5000)
   for i,v in enumerate(args,1):put(stack+i*4,v)
   m.reg_write(UC_X86_REG_ESP,stack);uploads.clear();deliveries.clear();m.emu_start((0x47db50,0x47dc40,0x47dd70)[alignment],arena,count=50000000)
   assert m.reg_read(UC_X86_REG_EIP)==arena and len(uploads)==1 and len(deliveries)==1,(font,profile,alignment,uploads,deliveries)
   d=deliveries[0];assert (d['height'],d['color'],d['outline'],d['font'],d['spacing'],d['shadow'])==(height,foreground,0,font,spacing,int(shadow));assert get(vm+0x18)==0xa5
   raw=bytes(m.mem_read(pixels,1024*128*2));name=f'font{font}-profile{profile}-alignment{alignment}.bin';(output/name).write_bytes(raw)
   rows.append(dict(font=font,height=height,offset=offset,color=foreground,outline=outline,spacing=spacing,plain=not shadow,text=plain.hex(),alignment=alignment,delivery=d,finalFlags=get(vm+0x18),file='artifacts/th14/font-alignment-native/'+name,sha256=hashlib.sha256(raw).hexdigest(),upload=uploads[0]))
"""
source=source[:start]+loop+source[end:]
source=source.replace("ROOT/'artifacts/th14/font-device-raster-native.json'","ROOT/'artifacts/th14/font-alignment-native.json'")
source=source.replace('Actual retail467ba0 and 467020/466eb0/466b10 scratch processing','Actual complete retail47db50/47dc40/47dd70 wrappers into467ba0 and467020/466eb0/466b10 scratch processing; CRT formatter returns controlled literal bytes')
(ROOT/'tools/th14-font-alignment-native.py').write_text(source,encoding='utf8')
print('Prepared240 complete retail alignment-wrapper/raster inputs')
