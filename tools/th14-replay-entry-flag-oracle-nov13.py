"""Retail entry-bit producers and real GameSession recording regression."""
from pathlib import Path
import hashlib, importlib, json, os, struct, subprocess, sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESI, UC_X86_REG_EDX, UC_X86_REG_EIP
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/replay-entry-flag-nov13'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_bytes())
sys.path.insert(0,str(R/'tools'))
im=importlib.import_module('th12-pe').Image('H:/Games/th/14/th14.exe')
assert hashlib.sha256(im.data).hexdigest()=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
m=Uc(UC_ARCH_X86,UC_MODE_32)
for _,va,size,raw,n in im.sections:
 p=va&~4095;m.mem_map(p,((va+size+4095)&~4095)-p);m.mem_write(va,im.data[raw:raw+n])
B=0x70000000;m.mem_map(B,0x10000);rows=[]
for initial,pc in [(True,0x446a4c),(False,0x446a99)]:
 for old in [0,1,2,3,0x80000000,0xffffffff]:
  m.reg_write(UC_X86_REG_ESI,0x4d8f60)
  m.emu_start(pc,pc+10,count=1);assert m.reg_read(UC_X86_REG_EIP)==pc+10
  flag=struct.unpack('<I',m.mem_read(0x4d9658,4))[0]
  m.mem_write(B+0xd8,struct.pack('<I',old));m.reg_write(UC_X86_REG_EDX,B)
  m.emu_start(0x4547b7,0x4547cc,count=10);assert m.reg_read(UC_X86_REG_EIP)==0x4547cc
  actual=struct.unpack('<I',m.mem_read(B+0xd8,4))[0]
  assert actual==(old&~1)|int(initial)
  rows.append(dict(initial=initial,old=old,producerFlag=flag,headerD8=actual))
(O/'native.json').write_text(json.dumps(dict(rows=rows,originalCodePatched=False,
 executableSha256=hashlib.sha256(im.data).hexdigest(),fullReplayRecordingAccepted=False),indent=2)+'\n')
provider=load(R/'artifacts/th14/option-refresh-oracle-nov13/candidate-providers/build.json')
for n,h in provider['sourceBindings'].items():assert sha(R/n)==h,n
for x in provider['currentProviders']:assert sha(R/x['object'])==x['objectSha256']
source=R/'runtimes/th12/th12_web/cpp/game/GameSession.cpp'
old=source.read_text()
anchor='// Native D8 carries 4d9658 bit 0; the ordinary port session uses 0.\n    s.th14_stage_flags=0;'
assert old.count(anchor)==1
candidate=old.replace(anchor,'// 446a4c sets new-entry=1; 446a99 clears it for the next stage.\n    // Replay4547b7 copies that bit to stage-header D8.\n    s.th14_stage_flags=initial?1u:0u;')
(O/'GameSession.candidate.cpp').write_text(candidate,encoding='utf8',newline='\n')
fixture=O/'fixture.cpp'
fixture.write_text(r'''
#include "GameSession.hpp"
#include <cstdlib>
using namespace th11;
extern "C" __attribute__((export_name("run"))) u32 run(i32 selection,i32 difficulty,i32 practice,i32 initial){
 auto s=std::make_unique<GameSession>(0);
 s->state.character=selection/2;s->state.subtype=selection%2;s->state.difficulty=difficulty;
 s->state.practice=practice;s->state.stage=initial?(practice?5u:1u):2u;
 if(!s->recording.begin(selection/2,selection%2,difficulty,practice,0))std::abort();
 s->battle=std::make_unique<GameBattle>(s->resources,s->animations,s->economy,s->spell_records,s->compositor,s->clear_records,true);
 auto& b=*s->battle;ShtResource sht;AnmResource anm;
 b.player=std::make_unique<PlayerFrame>(sht,anm,anm,s->animations,s->economy,b,9,7);
 if(!s->record_stage_entry(initial))std::abort();
 const auto& h=s->recording.stages[s->state.stage].header;
 u32 v=0;std::memcpy(&v,h.data()+0xd8,4);
 // Player's borrowed empty resources must outlive its destructor.
 b.player.reset();return v;
}
''',encoding='utf8')
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
assert sha(cc)==provider['compilerSha256'];flags=provider['flags']
def command(args,name):
 with (O/(name+'.log')).open('wb')as f:
  p=subprocess.run([str(cc),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
 assert p.returncode==0,(O/(name+'.log')).read_text(errors='replace')[-3000:]
command([*flags,'-c',str(O/'GameSession.candidate.cpp'),'-o',str(O/'GameSession.candidate.o')],'candidate-object')
objects=[str(R/x['object']) for x in provider['currentProviders']]
for mode in ['baseline','candidate']:
 selected=[str(O/'GameSession.candidate.o') if mode=='candidate' and Path(p).name=='GameSession.cpp.o' else p for p in objects]
 command([*flags,'-fno-access-control','-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined',
 '-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',str(fixture),*selected,'-o',str(O/(mode+'.wasm'))],mode)
(O/'build.json').write_text(json.dumps(dict(normalAccessProductionCandidate=True,fixtureRelaxedAccess=True,
 baselineSourceSha256=sha(source),candidateSourceSha256=sha(O/'GameSession.candidate.cpp'),
 objects={x['object']:x['objectSha256']for x in provider['currentProviders']},
 wasm={k:sha(O/(k+'.wasm'))for k in ['baseline','candidate']},toolSha256=sha(Path(__file__)),
 productionChanged=False,completeGame=False),indent=2)+'\n')
print('Built baseline and candidate recording paths; actual original bit producers: 12 cases.')
