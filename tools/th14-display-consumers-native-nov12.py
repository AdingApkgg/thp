"""Bounded original-code display consumers, without starting the retail game/GPU."""
from pathlib import Path
import hashlib, importlib, itertools, json, struct, sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
H=R/'artifacts/th14/display-consumers-nov12';sha=lambda b:hashlib.sha256(b).hexdigest()
# Retain and bind the existing original rectangle/COM recorder; only broaden inputs.
parent=R/'tools/th14-stage-fade-render-native.py';source=parent.read_text(encoding='utf8')
source=source.replace("OUT=ROOT/'artifacts/th14/stage-fade-render'","OUT=ROOT/'artifacts/th14/display-consumers-nov12/fade-native'")
old='for kind,alpha,color,depth,fog in itertools.product((2,3),(0,1,127,128,254,255),(0,0x123456),range(2),range(2)):'
new='for kind,alpha,color,depth,fog,width in itertools.product((0,2,3,5),(0,127,255),(0,0x123456),range(2),range(2),(640,960,1280)):'
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace('submissions.clear();pending.clear();run(0x46ca40,(),fade)',
    'submissions.clear();pending.clear();put(0x4f7a64,width);put(0x4f7a68,width*3//4);floats(0x4d904c,[0.,1.]);run(0x46c8d0 if kind in (0,5) else 0x46ca40,(),fade)')
source=source.replace('input=[kind,alpha,color,depth,fog]','input=[kind,alpha,color,depth,fog,width,width*3//4]')
source=source.replace("scope='Complete original Stage-created", "scope='Expanded dynamic-size original fade callbacks46c8d0/46ca40; inherited scope: Complete original Stage-created")
derived=H/'fade-native-derived.py';derived.write_text(source,encoding='utf8',newline='')
namespace={'__file__':str(parent),'__name__':'display_consumer_fade'};exec(compile(source,str(derived),'exec'),namespace);namespace['main']()
fade_report_path=H/'fade-native/native.json';fade_report=json.loads(fade_report_path.read_bytes())
fade_report.update(scope='Original callbacks46c8d0 and46ca40 plus actual rectangle46c4b0: 288 inputs, widths640/960/1280, types0/2/3/5, alpha0/127/255, two colors, depth/fog combinations. Full-window callback starts with initialized global viewport depth0..1; type2/3 retain the active viewport. COM/flush/cookie services controlled; no GPU pixels or registration/lifetime proof.',
    globalViewportDepthSynthetic=[0,1],derivedToolSha256=sha(derived.read_bytes()))
fade_report_path.write_text(json.dumps(fade_report,separators=(',',':'))+'\n')
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll')
assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
assert sha(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for img in (image,dll):
    for _,b,size,raw,n in img.sections:
        first=b&~4095;m.mem_map(first,((b+size+4095)&~4095)-first);m.mem_write(b,img.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x50000)
enemy,effect,vertices,positions,stack=[B+n for n in (0x1000,0x7000,0x10000,0x18000,0x4f000)]
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
words=lambda p,n:list(struct.unpack('<'+'I'*n,m.mem_read(p,n*4)))
floats=lambda p,*v:m.mem_write(p,struct.pack('<'+'f'*len(v),*v))
def run(entry,args=(),ecx=0):
    m.mem_write(stack,struct.pack('<'+'I'*(len(args)+1),B,*args));m.reg_write(UC_X86_REG_ESP,stack)
    m.reg_write(UC_X86_REG_ECX,ecx);m.reg_write(UC_X86_REG_MXCSR,0x1f80)
    m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
    m.emu_start(entry,B,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==B
m.mem_write(0x101ca068,dll.read(0x101ca190,0x4a*4));run(0x101bc521,(0x101ca068,))
pe=struct.unpack_from('<I',dll.data,0x3c)[0];export=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
functions,names,ordinals=[dll.image_base+dll.u32(export+x) for x in (28,32,36)]
for i in range(dll.u32(export+24)):
    name=dll.cstring(dll.image_base+dll.u32(names+i*4),128)
    if name=='D3DXVec3Normalize':
        ordinal=struct.unpack('<H',dll.read(ordinals+i*2,2))[0];normalize=dll.image_base+dll.u32(functions+ordinal*4)
put(0x4b12b8,normalize)
# Security-cookie check is a declared service, not a floating-point implementation.
def cookie(uc,a,n,u):
    sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EIP,words(sp,1)[0]);uc.reg_write(UC_X86_REG_ESP,sp+4)
m.hook_add(UC_HOOK_CODE,cookie,begin=0x4854a0,end=0x4854a0)
def setup(width):
    m.mem_write(enemy,bytes(0x8000));put(enemy+0x40f0,effect);put(effect,17);put(effect+4,17)
    put(effect+0x10,vertices);put(effect+0x14,positions);put(effect+0xc,B+0x8000)
    for j in range(16):
        p=B+0x20000+j*0x1000;put(B+0x8000+j*4,p);put(p+0x5b4,p+0x800)
    height=width*3//4
    for p,v in ((0x4f7a64,width),(0x4f7a68,height),(0x4f7a70,(width-384)//2),
                (0x4f7a88,width//2),(0x4f7a8c,(height-448)//2)):put(p,v)
    floats(0x4f7a6c,width/640)
def snapshot():
    return [v for j in range(289) for v in words(positions+j*12,3)+words(vertices+j*28,7)]
rectangles=[];updates=[]
for width,rectangle in itertools.product((640,960,1280),((-250.5,-30.25,153.75,215.5),(0,0,384,448),(24.25,230.5,296,296),(185,440,72,72))):
    setup(width);x,y,w,h=rectangle
    for reg,value in ((UC_X86_REG_XMM1,x),(UC_X86_REG_XMM2,y),(UC_X86_REG_XMM3,w)):
        m.reg_write(reg,struct.unpack('<I',struct.pack('<f',value))[0])
    run(0x41f360,(struct.unpack('<I',struct.pack('<f',h))[0],),effect)
    rectangles.append(dict(width=width,rectangle=rectangle,words=snapshot()))
for width,position,radius,rate in itertools.product((640,960,1280),((0,100,0),(-190,0,0),(185,440,0),(24.25,230.5,9)),(16,128),(.5,1.25)):
    setup(width);floats(0x4d8f58,rate);floats(enemy+0x44,*position)
    floats(enemy+0x40f4,128,radius);put(enemy+0x40fc,0x008f8fff);floats(enemy+0x4100,.25,-.5)
    frames=[]
    for _ in range(2):
        run(0x424100,ecx=enemy);frames.append(dict(state=words(enemy+0x40f8,1)+words(enemy+0x4100,2),words=snapshot()))
    updates.append(dict(width=width,position=position,radius=radius,rate=rate,frames=frames))
report=dict(rectangles=rectangles,updates=updates,executableSha256=sha(image.data),dllSha256=sha(dll.data),
    realD3dxNormalizeExecuted=True,floatingPointControlSynthetic={'x87':0x37f,'mxcsr':0x1f80},nativeGameStarted=False,gpuStarted=False,
    syntheticInputs=True,originalDeformationInstructionsUnmodified=True,completeGame=False,
    toolSha256=sha(Path(__file__).read_bytes()),fadeParentSha256=sha(parent.read_bytes()),fadeDerivedSha256=sha(derived.read_bytes()),
    instructionBindings={hex(a):sha(image.read(a,b-a)) for a,b in ((0x41f360,0x41f4b7),(0x424100,0x42468d),(0x46c8d0,0x46c968),(0x46ca40,0x46ca8e))})
(H/'deformation-native.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
print(json.dumps(dict(rectangleCases=len(rectangles),updateTimelines=len(updates),framesPerTimeline=2,realD3dxNormalizeExecuted=True)))
