"""Observe the current Application's live completion-to-save handoff."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];P=R/'artifacts/th14/native-viewer-application-nov13/component-v4'
H=R/'artifacts/th14/ordinary-completion-flow-nov13';H.mkdir(exist_ok=True);O=H/'component-v2';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
j=load(P/'build.json')
for n,h in {**j['sourceBindingsByMode']['candidate'],**j['objectBindings']}.items():assert sha(R/n)==h,n
s=(P/'fixture.cpp').read_text()+'''
// Boundary fixture only: invoke the same completion method as MSG21, without
// changing stage/score/clear flags, RNG, lives, invulnerability or replay mode.
bool fixture_completion_ready(){
 auto& s=current->session;auto* b=s.battle.get();
 return s.state.phase==GameSessionPhase::stage&&!s.state.replay&&b&&b->player&&
  b->stage_active&&!b->pending_stage&&b->resources.stage_number==i32(s.state.stage)&&
  b->completion.mode.stage==i32(s.state.stage)&&b->completion.state.exit==StageExit::None;
}
API(completion_boundary_ready) u32 completion_boundary_ready(){return fixture_completion_ready();}
API(finish_live_boundary) u32 finish_live_boundary(){
 auto& s=current->session;
 if(!fixture_completion_ready())return 0;
 return s.battle->dialogue_stage_complete();
}
API(completion_flow_state) const u32* completion_flow_state(){
 static u32 w[24];auto& s=current->session;
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=u32(s.state.replay);
 w[3]=s.ending?u32(s.ending->index):~0u;w[4]=s.ending?s.ending->seen:0;
 w[5]=s.title?u32(s.title->screen):~0u;w[6]=u32(s.completed_run);
 w[7]=u32(s.clear_records.clears[1][1]);w[8]=u32(s.clear_records.no_continue_clears[1][1]);
 w[9]=s.scores.settings[0x16];w[10]=s.scores.settings[0x18];
 w[11]=s.title?u32(s.title->unlocked()):0;
 for(i32 n=0;n<6;++n)w[12+n]=s.title?u32(s.title->available(n/2,n%2)):0;
 w[18]=callbacks;w[19]=s.battle?u32(s.battle->completion.state.exit):0;
 w[20]=s.battle?u32(s.battle->completion.state.ending_frames):0;
 w[21]=s.battle?u32(bool(s.battle->pending_stage)):0;
 w[22]=s.state.frame;w[23]=s.title?u32(s.title->substate):~0u;
 return w;
}
'''
(O/'fixture.cpp').write_text(s,encoding='utf8',newline='\n');(O/'Th14WarmAttractCase.hpp').write_bytes((P/'Th14WarmAttractCase.hpp').read_bytes())
cmd=[x.replace(str(P),str(O))for x in load(P/'command.json')];(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
bindings={n:sha(R/n)for n in j['sourceBindingsByMode']['candidate']if not n.startswith(P.relative_to(R).as_posix()+'/')}
for p in [O/'fixture.cpp',O/'Th14WarmAttractCase.hpp']:bindings[p.relative_to(R).as_posix()]=sha(p)
j.update(sourceBindingsByMode={'candidate':bindings},fixtureSha256=sha(O/'fixture.cpp'),outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},
 completionBoundaryMethodInvokedDirectly=True,naturalFullCampaignAccepted=False,onlyAddedTestEntryAndReadOnlyObservation=True)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(dict(compiled=True,wasmSha256=sha(O/'candidate.wasm'),productionGameCodeChanged=False)))
