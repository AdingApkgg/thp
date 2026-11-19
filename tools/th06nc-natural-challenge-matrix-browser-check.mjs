import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,existsSync,readdirSync,openSync,closeSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

// One browser at a time: both children own the same CDP port.
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=[...readdirSync('shared/th06nc').filter(n=>n.endsWith('.mjs')).map(n=>'shared/th06nc/'+n),...['game.mjs','game-assets.mjs','game-renderer.mjs','game-audio.mjs','game-save.mjs'].map(n=>'runtimes/th06nc/'+n)];
const snapshot=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))]));
const sourceSha256=snapshot(),rows=[];
const path='docs/porting/th06nc-natural-challenge-matrix-browser-verified.json';
const load=p=>existsSync(p)?JSON.parse(readFileSync(p,'utf8')):null;
const current=r=>r?.passed===true&&JSON.stringify(r.sourceSha256)===JSON.stringify(sourceSha256);
const save=(passed,active=null)=>writeFileSync(path,JSON.stringify({scope:'Sixteen actual natural Challenge title-to-clear/save/reload runs and their saved replays. Replay checks compare all seven raw actor pools and gameplay counters/RNG at captured draw-aligned checkpoints, then natural replay-menu return, final score, unchanged replay bytes and no score writes. Does not establish every-frame/native task/GPU/audio equivalence or Standard/Extra/spell-practice completion.',sourceSha256,rows,active,passed,completeGame:false,nativeEquivalent:false},null,2)+'\n');
mkdirSync('tools/tmp',{recursive:true});
save(false);
for(let profile=0;profile<4;profile++)for(let difficulty=0;difficulty<4;difficulty++){
 const name=['reimu-a','reimu-b','marisa-a','marisa-b'][profile],level=['easy','normal','hard','lunatic'][difficulty];
 const runPath=`docs/porting/th06nc-natural-run-${name}-difficulty${difficulty}-challenge-browser-verified.json`,playPath=`docs/porting/th06nc-natural-playback-${name}-${level}-browser-verified.json`,input=`artifacts/th06nc/natural-run-${name}-difficulty${difficulty}-challenge-browser/natural-th6_01.rpy`;
 let run=load(runPath),play=load(playPath);
 for(const kind of ['run','playback']){
  assert.deepEqual(snapshot(),sourceSha256,'Source changed during matrix');
  const accepted=kind==='run'?current(run)&&run.checkpoints?.length>0&&run.drawSchedule?.length>0:current(play)&&play.checked===run.checkpoints.length&&play.inputSha256===sha(readFileSync(input));
  if(accepted)continue;
  const log=`tools/tmp/th06nc-matrix-${name}-${level}-${kind}.log`,fd=openSync(log,'w');
  save(false,{profile,difficulty,kind,log});console.log(JSON.stringify({profile,difficulty,kind,log}));
  let child;try{child=spawnSync(process.execPath,[`tools/th06nc-natural-${kind==='run'?'run':'playback'}-browser-check.mjs`,`--profile=${profile}`,`--difficulty=${difficulty}`],{stdio:['ignore',fd,fd]});}finally{closeSync(fd);}
  assert.equal(child.status,0,`${kind} ${name} ${level}: ${child.error??log}`);
  run=load(runPath);play=load(playPath);
 }
 assert.ok(current(run)&&current(play));assert.equal(play.checked,run.checkpoints.length);assert.ok(play.checked>0);assert.equal(play.inputSha256,sha(readFileSync(input)));
 rows.push({profile,difficulty,stages:run.stages,stageFrames:run.stageFrames,checkpoints:play.checked,score:play.expectedScore,runReport:runPath,runReportSha256:sha(readFileSync(runPath)),playbackReport:playPath,playbackReportSha256:sha(readFileSync(playPath)),inputSha256:play.inputSha256});
 save(false);console.log(JSON.stringify({completed:rows.length,profile,difficulty,checkpoints:play.checked}));
}
assert.equal(rows.length,16);save(true);console.log(JSON.stringify({passed:true,combinations:rows.length,checkpoints:rows.reduce((n,r)=>n+r.checkpoints,0)}));
