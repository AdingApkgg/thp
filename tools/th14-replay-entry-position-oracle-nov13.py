"""Compare nonzero entry coordinates through real session recording providers."""
from pathlib import Path
import hashlib,importlib,json,os,struct,subprocess,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EDX,UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/replay-entry-position-nov13'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
parent=R/'artifacts/th14/replay-entry-flag-nov13';bindings=load(parent/'current-provider-bindings.json')
for p,h in {**bindings['sourceBindings'],**bindings['objectBindings']}.items():assert sha(R/p)==h,p
sys.path.insert(0,str(R/'tools'));im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert hashlib.sha256(im.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,raw,n in im.sections:
 p=va&~4095;m.mem_map(p,((va+size+4095)&~4095)-p);m.mem_write(va,im.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x10000);rows=[]
coords=[(-1234,51199),(0,51200),(-2147483648,2147483647),(2147483647,-2147483648)]
for initial in [0,1]:
 for x,y in coords:
  before=bytearray([0xa5]*0x100);struct.pack_into('<ii',before,0xc,x,y)
  m.mem_write(B,bytes(before));m.mem_write(0x4d9658,struct.pack('<I',initial));m.reg_write(UC_X86_REG_EDX,B)
  m.emu_start(0x4547cc,0x4547e3,count=10);assert m.reg_read(UC_X86_REG_EIP)==0x4547e3
  after=bytes(m.mem_read(B,0x100));expected=bytearray(before)
  if initial:expected[0xc:0x14]=bytes(8)
  assert after==expected
  rows.append(dict(initial=initial,input=[x,y],output=list(struct.unpack_from('<ii',after,0xc))))
(O/'native.json').write_text(json.dumps(dict(rows=rows,onlyCoordinateBytesMayChange=True,
 executableSha256=hashlib.sha256(im.data).hexdigest(),blockSha256=hashlib.sha256(im.read(0x4547cc,0x17)).hexdigest(),
 originalInstructionBytesPatched=0,noDeclaredServices=True),indent=2)+'\n')
source=R/'runtimes/th12/th12_web/cpp/game/GameSession.cpp';old=source.read_text()
anchor='    s.th14_stage_flags=initial?1u:0u;';assert old.count(anchor)==1
new=old.replace(anchor,anchor+'\n    // 4547d5/4547dc clear initial header coordinates; next-stage entries retain them.\n    if(initial)s.x=s.y=0;')
(O/'GameSession.baseline.cpp').write_bytes(source.read_bytes());(O/'GameSession.candidate.cpp').write_text(new,encoding='utf8',newline='\n')
fixture=(parent/'fixture.cpp').read_text().replace('i32 practice,i32 initial)', 'i32 practice,i32 initial,i32 x,i32 y)')
fixture=fixture.replace(' if(!s->record_stage_entry(initial))',' b.player->motion.state.x=x;b.player->motion.state.y=y;\n if(!s->record_stage_entry(initial))')
fixture=fixture.replace(' u32 v=0;std::memcpy(&v,h.data()+0xd8,4);',' static std::array<u8,kReplayStageHeader> output;output=h;')
fixture=fixture.replace('b.player.reset();return v;','b.player.reset();return u32(uintptr_t(output.data()));')
fixture+='\nextern "C" __attribute__((export_name("header_size"))) u32 header_size(){return kReplayStageHeader;}\n'
(O/'fixture.cpp').write_text(fixture,encoding='utf8')
provider=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(cc)==provider['compilerSha256'];flags=provider['flags']
def compile(args,name):
 with(O/(name+'.log')).open('wb')as f:q=subprocess.run([str(cc),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
 assert q.returncode==0,(O/(name+'.log')).read_text(errors='replace')[-3000:]
compile([*flags,'-c',str(O/'GameSession.candidate.cpp'),'-o',str(O/'GameSession.candidate.o')],'candidate-object')
objects=[str(R/p)for p in bindings['objectBindings']]
prior_object=str(parent/'GameSession.candidate.o');assert objects.count(prior_object)==1
for mode in ['baseline','candidate']:
 selected=[str(O/'GameSession.candidate.o')if mode=='candidate'and p==prior_object else p for p in objects]
 compile([*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(O/'fixture.cpp'),*selected,'-o',str(O/(mode+'.wasm'))],mode)
(O/'build.json').write_text(json.dumps(dict(sourceBindings=bindings['sourceBindings'],objects=bindings['objectBindings'],
 baselineSourceSha256=sha(source),candidateSourceSha256=sha(O/'GameSession.candidate.cpp'),
 fixtureSha256=sha(O/'fixture.cpp'),normalAccessCandidateGameSession=True,fixtureAccessRelaxed=True,
 wasm={mode:sha(O/(mode+'.wasm'))for mode in ['baseline','candidate']},coords=coords,completeGame=False),indent=2)+'\n')
print('Built original/candidate session position probes and executed 8 retail coordinate cases.')
