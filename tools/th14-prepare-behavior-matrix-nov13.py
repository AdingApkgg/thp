"""Current normal-menu matrix with external keys and read-only checkpoints."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/behavior-matrix-nov13';assert not H.exists();H.mkdir();O=H/'component';O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
P=R/'artifacts/th14/current-normal-full-nov13/component-v2';j=load(P/'build.json')
for n,h in {**j['sourceBindingsByMode']['candidate'],**j['objectBindings']}.items():assert sha(R/n)==h,n
s=(P/'fixture.cpp').read_text();a='std::unique_ptr<Application> current;GameSession* game=nullptr;';assert s.count(a)==1;s=s.replace(a,a+'\nu32 menu_input_held=0;bool menu_pause_pending=false;')
a='do{ok=current->tick_once(0);';assert s.count(a)==1;s=s.replace(a,'do{const bool pause=menu_pause_pending;menu_pause_pending=false;ok=current->tick_once(menu_input_held,pause);')
prior=(R/'artifacts/th14/promoted-ordinary-matrix-nov08/menu-application/fixture.cpp').read_text();a=prior.index('API(set_menu_input)');s+='\n'+prior[a:]
s+='''
API(press_pause) void press_pause(){menu_pause_pending=true;}
API(behavior_state) const u32* behavior_state(){
 auto& s=current->session;auto* b=s.battle.get();auto* p=b?b->player.get():nullptr;static u32 w[20];
 w[0]=u32(s.state.phase);w[1]=s.state.stage;w[2]=s.state.character;w[3]=s.state.subtype;w[4]=s.state.difficulty;
 w[5]=b?u32(b->control_frame()):0;w[6]=p?u32(p->motion.state.x):0;w[7]=p?u32(p->motion.state.y):0;
 w[8]=p?u32(p->state.life_state):0xffffffff;w[9]=b?u32(b->economy.th14_bombs):0xffffffff;
 w[10]=b&&b->bomb?u32(b->bomb->state.active):0;w[11]=0;
 if(p)for(u32 i=0;i<256;++i)if(p->shots.at(i).state)++w[11];
 w[12]=p?u32(p->motion.state.focused):0;w[13]=p?u32(p->input.movement.held):0;
 w[14]=s.pause_menu?u32(s.pause_menu->state):0xffffffff;w[15]=callbacks;
 w[16]=p?u32(p->motion.state.normal_speed):0;w[17]=p?u32(p->motion.state.focus_speed):0;
 w[18]=b?u32(b->economy.power):0;w[19]=b?u32(b->economy.lives):0;
 return w;
}
'''
(O/'fixture.cpp').write_text(s,encoding='utf8',newline='\n');(O/'Th14WarmAttractCase.hpp').write_bytes((P/'Th14WarmAttractCase.hpp').read_bytes())
cmd=[x.replace(str(P),str(O))for x in load(P/'command.json')];(O/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(O/'compile.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'compile.log').read_text(errors='replace')[-3000:]
bindings={n:h for n,h in j['sourceBindingsByMode']['candidate'].items()if not n.startswith('artifacts/th14/current-normal-full-nov13/component-v2/')}
for p in [O/'fixture.cpp',O/'Th14WarmAttractCase.hpp',Path(__file__)]:bindings[p.relative_to(R).as_posix()]=sha(p)
j.update(fixtureSha256=sha(O/'fixture.cpp'),sourceBindingsByMode={'candidate':bindings},outputs={'candidate':{'wasmSha256':sha(O/'candidate.wasm')}},heldKeysAndPauseEventOnly=True,noGameSelectionOrEconomyWrites=True)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps({'compiled':True,'normalProvidersReused':145,'wasmSha256':sha(O/'candidate.wasm')}))
