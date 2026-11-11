"""Execute original type-0 transition initialization/update/interrupt/draw.

File/texture/allocation services are controlled; embedded ANM scripts execute
from the original resource loader. D3D calls and embedded draws are recorded.
"""
from pathlib import Path
import hashlib, importlib, json, struct, sys, traceback
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *

R=Path(__file__).resolve().parents[1]; H=R/'artifacts/th14/first-present-alpha-localization-nov12/batch-state/native-v2'
assert not H.exists();H.mkdir(parents=True);sys.path.insert(0,str(R/'tools'))
sha=lambda b:hashlib.sha256(b).hexdigest()
image,*_=importlib.import_module('th-anm-handlers').handlers(14)
assert sha(image.data)=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,base,size,raw,n in image.sections:
    first=base&~4095;m.mem_map(first,((base+size+4095)&~4095)-first);m.mem_write(base,image.data[raw:raw+n])
loader=importlib.import_module('th14-native-transition-resource-loader-nov09').install(m)
B=0x78000000;STACK=B+0xff000;STOP=B+0xfe000;ROOT=B+0x2000;OWNER=B+0x1000
m.mem_map(B,0x100000)
put=lambda p,v:m.mem_write(p,struct.pack('<I',v&0xffffffff))
get=lambda p:struct.unpack('<I',m.mem_read(p,4))[0]
events=[];cases=[];phase='';error='';device_states={}
def ret(value=0,argc=0):
    sp=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EIP,get(sp));m.reg_write(UC_X86_REG_ESP,sp+4+argc*4);m.reg_write(UC_X86_REG_EAX,value)
def run(entry,owner=ROOT,args=(),label=0):
    m.mem_write(STACK,struct.pack('<'+'I'*(len(args)+1),STOP,*args))
    for reg,value in [(UC_X86_REG_ESP,STACK),(UC_X86_REG_ECX,owner),(UC_X86_REG_EDX,label),(UC_X86_REG_MXCSR,0x1f80),(UC_X86_REG_FPCW,0x37f),(UC_X86_REG_FPSW,0),(UC_X86_REG_FPTAG,0xffff)]:m.reg_write(reg,value)
    try:m.emu_start(entry,STOP,count=5000000)
    except Exception as exc:raise RuntimeError(f'entry={entry:x} pc={m.reg_read(UC_X86_REG_EIP):x} phase={phase}')from exc
    assert m.reg_read(UC_X86_REG_EIP)==STOP,hex(m.reg_read(UC_X86_REG_EIP))
    return m.reg_read(UC_X86_REG_EAX)
def snapshot():
    geom=get(ROOT+0x5b4);assert geom
    return dict(state=get(geom+0x1cfc),counter=get(geom+0x1d00),layer=get(ROOT+0x24),
        rngHex=bytes(m.mem_read(0x4db508,16)).hex(),rootHex=bytes(m.mem_read(ROOT,0x5cc)).hex(),
        embeddedHex=[bytes(m.mem_read(geom+i*0x5cc,0x5cc)).hex()for i in range(5)])
def record(machine,address,size,user):
    sp=m.reg_read(UC_X86_REG_ESP)
    if address==0x475eb0:events.append(dict(kind='flush'));ret();return
    if address==0x478f60:
        vm=get(sp+4);events.append(dict(kind='embeddedDraw',index=(vm-get(ROOT+0x5b4))//0x5cc,script=struct.unpack('<H',m.mem_read(vm+0x4aa,2))[0],flags=get(vm+0x18),flags2=get(vm+0x1c)));return
    if address==0x4756e0:
        vm=get(sp+4);events.append(dict(kind='quadSubmitEntry',script=struct.unpack('<H',m.mem_read(vm+0x4aa,2))[0],mode=get(sp+8),verticesHex=bytes(m.mem_read(0x4fd218,4*28)).hex()));return
    if address==0x475f80:
        pointer=get(sp+4);events.append(dict(kind='finalQuadSubmission',verticesHex=bytes(m.mem_read(pointer,4*28)).hex()));ret(0,1);return
    method,argc=services[address]
    args=list(struct.unpack('<'+'I'*argc,m.mem_read(sp+4,argc*4)))
    row=dict(kind=method,args=args[1:])
    if method=='DrawPrimitiveUP':
        primitive,count,pointer,stride=args[1:];vertices=count+2 if primitive in (5,6)else count*3
        assert 0<vertices<=128 and 0<stride<=128
        row['deviceStates']=dict(device_states)
        row['verticesHex']=bytes(m.mem_read(pointer,vertices*stride)).hex()
    if method=='SetRenderState':device_states[args[1]]=args[2]
    events.append(row);ret(0,argc)
services={}
for slot,name,argc in [(57,'SetRenderState',3),(67,'SetTextureStageState',4),(65,'SetTexture',3),(89,'SetFVF',2),(83,'DrawPrimitiveUP',5),(69,'SetSamplerState',4)]:
    addr=B+0x8000+slot*16;services[addr]=(name,argc);put(B+0x7000+slot*4,addr);m.hook_add(UC_HOOK_CODE,record,begin=addr,end=addr)
for addr in [0x478f60,0x4756e0]:m.hook_add(UC_HOOK_CODE,record,begin=addr,end=addr)
put(0x4d9640,B+0x4000);put(B+0x4000+0xe8,640);put(B+0x4000+0xec,480)
for i in range(4):put(0x4fd218+i*28+12,0x3f800000)
put(B+0x6000,B+0x7000);put(0x4d8f68,B+0x6000);put(0x4db53c,OWNER)
try:
    meta=json.loads((R/'artifacts/archive-differential/th14.json').read_bytes());path=Path(meta['extraction'])/'effect.anm';blob=path.read_bytes()
    assert sha(blob)=='bbd7205654c87677c4a582fc5e99c2884e724f501b3d281c75bf207a76095559'
    ascii_blob=(Path(meta['extraction'])/'ascii.anm').read_bytes()
    assert sha(ascii_blob)=='fc1c2295fda07140b475b2ddd45d221920534e4a011c529e76578609d69a9284'
    phase='load original ASCII fallback';ascii_resource=loader.load('ascii.anm',ascii_blob,2,1.)
    put(loader.manager+0x191e4,ascii_resource.resource)
    phase='load original effect resource';resource=loader.load('effect.anm',blob,8,1.)
    put(OWNER+0x10,resource.resource)
    def initialize():
        global phase
        phase='copy root';m.mem_write(ROOT,bytes(0x5cc));run(0x40af00,resource.resource,(ROOT,0));run(0x46fe50)
        phase='type0 initialize';loader.context['loading']=True
        try:assert run(0x40a530)==0
        finally:loader.context['loading']=False
        for i,callback in enumerate([0x40a680,0x40a6f0,0x40ace0,0x40acf0]):put(ROOT+0x5b8+i*4,callback)
    def interrupt(label):
        # Execute47f158..47f1a6 after a declared successful lookup of ROOT.
        # This includes the actual effect callback, pending-word store and
        # root child-list test. Lookup/pool ownership are outside this probe.
        m.reg_write(UC_X86_REG_ESP,STACK-0x200)
        m.reg_write(UC_X86_REG_EBP,STACK-0x100)
        m.reg_write(UC_X86_REG_ESI,ROOT)
        put(STACK-0x100+12,label)
        m.emu_start(0x47f158,0x47f1a6,count=5000000)
        assert m.reg_read(UC_X86_REG_EIP)==0x47f1a6
    draw_cases=[]
    for state in range(4):
      for before in [0,79,84]:
       for frame in [0,1,10,20,40]:
        for fmt,warm in [(f,w)for f in [21,22]for w in [255,0,7]]:
         initialize();interrupt(7+state)
         for _ in range(before):assert run(0x46fe50)==0
         interrupt(1)
         for _ in range(frame):assert run(0x46fe50)==0
         put(0x4f7a64,640);put(0x4f7a68,480);m.mem_write(0x4f7a6c,struct.pack('<f',1.));put(0x4d905c,fmt)
         device_states.clear();device_states.update({19:5,20:6,171:1,206:0,207:2,208:1,209:1,15:1,14:0,27:1})
         start=loader.manager+0xbc81f4;put(loader.manager+0xf481f4,start);put(loader.manager+0xf481f8,start);put(loader.manager+0xbc81f0,0)
         m.mem_write(loader.manager+0xbc8188,bytes([255])*16)
         if warm!=255:
            warm_vm=B+0x10000;source=get(ROOT+0x5b4)+4*1484;m.mem_write(warm_vm,bytes(m.mem_read(source,1484)));put(warm_vm+0x18,(get(warm_vm+0x18)&~0x1e0)|(warm<<5)|3);put(warm_vm+0x534,0xffffffff)
            run(0x478f60,loader.manager,(warm_vm,));run(0x475eb0,loader.manager)
         events.clear();phase=f'embedded draw state={state} before={before} frame={frame} format={fmt} warm={warm}'
         status=run(0x40a6f0);assert status==0
         run(0x475eb0,loader.manager) # Declared final caller flush, as in C++ fixture.
         draw_cases.append(dict(state=state,before=before,frame=frame,format=fmt,warm=warm,result=status,snapshot=snapshot(),events=list(events)))
except Exception:
    error=traceback.format_exc();(H/'exception.txt').write_text(error)
out=dict(terminal=True,error=error,phase=phase,cases=cases,drawCases=locals().get('draw_cases',[]),
    originalInstructionsForConstructorUpdateInterruptAndDraw=True,
    interruptUsesActualPostLookupCallbackAndPendingStore=True,rootLookupDeclared=True,controlledRootStorageAndCallbackInstallation=True,
    actualEffectAnmResourceLoader=True,actualAsciiFallbackLoaded=True,resourceHeapRetainedAcrossLoads=True,embeddedDrawsAndGpuCallsRecorded=True,actual475eb0FlushAnd475f80QueueExecuted=True,drawTimeDeviceStatesRecorded=True,finalCallerFlushDeclaredAndExecuted=True,initialDeviceStateDeclared=True,noGpuPixels=True,
    noWholeReplayOrOrdinaryUiAcceptance=True,completeGame=False,sourceSha256=sha(Path(__file__).read_bytes()))
(H/'report.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(terminal=True,error=error[-1200:],phase=phase,updateCases=len(cases),drawCases=len(out['drawCases']))))
if error:sys.exit(1)
