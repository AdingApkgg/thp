"""Feed only recorded key masks into an ordinary current Application."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/native-viewer-application-nov13/component-v4'
H=R/'artifacts/th14/ordinary-keyscript-nov13';H.mkdir(exist_ok=False);O=H/'component';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
j=load(P/'build.json')
for n,h in {**j['sourceBindingsByMode']['candidate'],**j['objectBindings']}.items():assert sha(R/n)==h,n
s=(P/'fixture.cpp').read_text()
marker='API(frame) u32 frame(double seconds){';assert s.count(marker)==1
helper='''
namespace {
Replay fixture_keys;
bool fixture_keys_enabled=false;
u32 fixture_key_reads=0,fixture_key_tail_reads=0,fixture_last_key_stage=0,fixture_last_key_frame=0,fixture_last_key=0;
u32 fixture_physical_held(){
 if(!fixture_keys_enabled||!current)return menu_input_held;
 const auto& session=current->session;
 if(session.state.phase!=GameSessionPhase::stage||session.state.replay||session.state.demo)return menu_input_held;
 // Read the ordinary recorder's own input position. No replay header is
 // restored into the game: this separate decoder supplies key masks only.
 const auto stage=session.recording.selected;
 const auto* entry=fixture_keys.stage(stage);
 if(!entry||stage>=session.recording.stages.size())return menu_input_held;
 const u32 frame=session.recording.stages[stage].frames;
 fixture_last_key_stage=stage;fixture_last_key_frame=frame;++fixture_key_reads;
 u32 held=1; // after the supplied segment, keep shooting rather than all-FF keys
 if(frame<entry->frames){
  const auto* p=fixture_keys.decoded().data()+entry->offset+kReplayStageHeader+frame*6;
  const bool terminal=p[0]==255&&p[1]==255&&p[2]==255&&p[3]==255&&p[4]==255&&p[5]==255;
  if(!terminal)held=u32(p[0])|u32(p[1])<<8;else ++fixture_key_tail_reads;
 }else ++fixture_key_tail_reads;
 fixture_last_key=held;return held;
}
}
API(load_keys) u32 load_keys(const u8* data,u32 size){
 if(!fixture_keys.open(data,size)||fixture_keys.character()!=0||fixture_keys.subtype()!=1||fixture_keys.difficulty()!=1||fixture_keys.stage_count()!=6||fixture_keys.uses_touch())return 0;
 if(fixture_keys.decoded()[10]&3)return 0;
 fixture_keys_enabled=true;return 1;
}
API(keyscript_state) const u32* keyscript_state(){
 static u32 w[12];const auto& s=current->session;
 w[0]=fixture_keys_enabled;w[1]=fixture_last_key_stage;w[2]=fixture_last_key_frame;w[3]=fixture_last_key;
 w[4]=fixture_key_reads;w[5]=fixture_key_tail_reads;w[6]=s.state.replay;w[7]=s.recording_active;
 w[8]=s.completed_run;w[9]=s.recording.selected;w[10]=w[9]<s.recording.stages.size()?s.recording.stages[w[9]].frames:0;w[11]=s.state.stage;
 return w;
}
API(ordinary_flow_state) const u32* ordinary_flow_state(){
 static u32 w[24];auto& s=current->session;
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=s.state.replay;w[3]=s.ending?u32(s.ending->index):~0u;
 w[4]=s.ending?s.ending->seen:0;w[5]=s.title?u32(s.title->screen):~0u;w[6]=s.completed_run;
 w[7]=u32(s.clear_records.clears[1][1]);w[8]=u32(s.clear_records.no_continue_clears[1][1]);
 w[9]=s.scores.settings[0x16];w[10]=s.scores.settings[0x18];w[11]=s.title?u32(s.title->unlocked()):0;
 for(i32 n=0;n<6;++n)w[12+n]=s.title?u32(s.title->available(n/2,n%2)):0;
 w[18]=callbacks;w[19]=s.battle?u32(s.battle->completion.state.exit):0;
 w[20]=s.battle?u32(s.battle->completion.state.ending_frames):0;w[21]=s.battle?u32(bool(s.battle->pending_stage)):0;
 w[22]=s.state.frame;w[23]=s.title?u32(s.title->substate):~0u;return w;
}
'''
s=s.replace(marker,helper+'\n'+marker,1)
needle='ok=current->tick_once(menu_input_held,pause);';assert s.count(needle)==1
s=s.replace(needle,'ok=current->tick_once(fixture_physical_held(),pause);',1)
(O/'fixture.cpp').write_text(s,encoding='utf8',newline='\n');(O/'Th14WarmAttractCase.hpp').write_bytes((P/'Th14WarmAttractCase.hpp').read_bytes())
cmd=[x.replace(str(P),str(O))for x in load(P/'command.json')];(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
bindings={n:sha(R/n)for n in j['sourceBindingsByMode']['candidate']if not n.startswith(P.relative_to(R).as_posix()+'/')}
for p in [O/'fixture.cpp',O/'Th14WarmAttractCase.hpp']:bindings[p.relative_to(R).as_posix()]=sha(p)
j.update(sourceBindingsByMode={'candidate':bindings},fixtureSha256=sha(O/'fixture.cpp'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},
 onlyAddedInputProviderAndReadOnlyObservation=True,recordedGameStateNotRestored=True,completionMethodsNotExposed=True,productionGameCodeChanged=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=sha(O/'candidate.wasm'),productionGameCodeChanged=False)))
