"""Explain retained UV phase with retail updates; never pad the live game."""
from pathlib import Path
import hashlib,importlib,json,struct,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/compositor-filter-nov13'
O=H/'background-uv-phase-qualified.json';assert not O.exists()
sys.path.insert(0,str(R/'tools'))
ui=importlib.import_module('th14-ui-oracle');vm=importlib.import_module('th14-anm-vm-oracle')
image=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
assert hashlib.sha256(image.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
native_path=R/'artifacts/th14/current-startup-prefix-nov10/native/transition-before-readback.json'
geometry=bytes.fromhex(load(native_path)['geometryHex']);assert len(geometry)==5*0x5cc+8
bg=geometry[4*0x5cc:5*0x5cc];word=lambda n:struct.unpack_from('<I',bg,n)[0]
native_counter=struct.unpack_from('<I',geometry,5*0x5cc+4)[0]
retail=ui.Retail(image);rows=[];bindings={native_path.relative_to(R).as_posix():sha(native_path)}
for name,relative in [('baseline','current-vorbis-no1-startup-nov13/current'),('filterCandidate','compositor-filter-nov13/candidate-no1')]:
 path=R/'artifacts/th14'/relative/'transition-after-draw.json';data=load(path)['words']
 assert data[0]==884712 and data[5:7]==[6,303]
 state=data[7+5*303:7+6*303];steps=word(0x560)-state[7]
 assert steps==native_counter-data[3] and steps in [4,5]
 # Future no-op keeps the interpreter active without executing setup commands.
 # Opcode2 stops progression and was rejected in an earlier control.
 code=vm.instruction(0,time=256)+vm.instruction(-1,time=32767)
 args=[vm.f(1),word(0x1c),vm.f(1),vm.f(1),0,0,0,0,0,0,0,0,
       state[35],state[36],word(0x3d8),word(0x3dc),0,steps,0xffffffff]
 actual=vm.native_rows(retail,args,code)
 ix,iy=vm.FIELDS.index('uv.offsetX'),vm.FIELDS.index('uv.offsetY')
 assert actual[-1][ix:iy+1]==[word(0x88),word(0x8c)]
 rows.append(dict(name=name,nativeCounter=native_counter,cppCounter=data[3],nativeAge=word(0x560),cppAge=state[7],
   controlledNativeUpdateCount=steps,inputUvWords=state[35:37],nativeTargetUvWords=[word(0x88),word(0x8c)],
   outputUvWords=actual[-1][ix:iy+1],scrollWords=[word(0x3d8),word(0x3dc)],
   fullNativePerUpdateRows=actual,uvExactAfterObservedAgeGap=True))
 bindings[path.relative_to(R).as_posix()]=sha(path)
archive_path=R/'artifacts/archive-differential/th14.json';archive=load(archive_path)
effect_path=Path(archive['extraction'])/'effect.anm'
assert sha(effect_path)==next(x['sha256']for x in archive['decoded']if x['name']=='effect.anm')
texture=None
for _,chunk in importlib.import_module('th-anm-texture-table').chunks(effect_path.read_bytes()):
 at=struct.unpack_from('<I',chunk,16)[0];name=chunk[at:chunk.index(b'\0',at)].decode()
 if name=='effect/eff_switchbg.png':
  at=struct.unpack_from('<I',chunk,28)[0];fmt,width,height,size=struct.unpack_from('<HHHI',chunk,at+6)
  assert(fmt,width,height,size)==(5,256,256,131072)
  texture=dict(name=name,format=fmt,width=width,height=height,pixelBytes=size,
               rawPixelsSha256=hashlib.sha256(chunk[at+16:at+16+size]).hexdigest())
assert texture is not None
report=dict(rows=rows,texture=texture,originalExeSha256=hashlib.sha256(image.data).hexdigest(),
 actualRetail46fe50Executed=True,syntheticFutureHoldAndRate1=True,
 velocityEnableAndScrollAreMeasuredBackgroundInputs=True,
 earlierStopOpcodeAndMissingVelocityFlagControlsRejected=True,
 geometryShiftNotEstablishedByImageCorrelation=True,
 liveGameUpdatesOrRngOrUvValuesPadded=False,wholeFramePixelsOrTimingAccepted=False,
 productionChanged=False,completeGame=False,bindings=bindings,toolSha256=sha(Path(__file__)))
O.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),updates=[x['controlledNativeUpdateCount']for x in rows],bothUvPairsBitExact=True,
                     geometryShiftEstablished=False,completeGame=False)))
