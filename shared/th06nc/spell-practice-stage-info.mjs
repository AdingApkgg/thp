import {createSpellInfoPublisher,publishSpellInfoHeading,spellBossKeys as bossKeys} from './spell-practice-info-text.mjs';
export {spellInfoTextAsset} from './spell-practice-info-text.mjs';
const F=Math.fround;

// Stage-selection branch of information refresh 4fdd0..50ab2. The caller owns
// localized resources and the verified text publisher; later card/difficulty
// branches use different layouts and are not represented by this function.
export function refreshSpellPracticeStageInfo(group,state,{table,records,character,shot,localization={},publishText}={}){
 if(state.state!==28||typeof publishText!=='function')throw Error('TH06nc: stage-info owner and publisher required');
 const localize=key=>localization[key]??key,profile=(character&255)*2+(shot&255);
 if(profile>=4)throw Error('TH06nc: invalid spell-menu profile');
 const format=(text,value)=>text.replace(/%[ds]/,()=>String(value));
 const publish=createSpellInfoPublisher(group,publishText);publishSpellInfoHeading(publish,state,profile,localization);let key;
 for(const [i,suffix,x]of [[0,'STAGE_COLUMN',83.55555725097656],[1,'BOSS_COLUMN',277.5555725097656],[2,'RECORD_COLUMN',472.5555725097656]]){
  key='EXE_SPELL_PRACTICE_'+suffix;publish(0x16a50+i*288,0x738+i,localize(key),{key,x,y:102.55555725097656});
 }
 state.completeFlags??=Array(7).fill(false);
 for(let stage=0;stage<7;stage++){
  const rows=table.filter(r=>r.stageIndex===stage),attempted=r=>r.id<134&&Boolean(records.get(r.id)?.attempts),unlocked=rows.some(attempted),mainUnlocked=rows.some(r=>!r.midboss&&attempted(r));
  const baseY=F(F(F(stage)*F(45))+F(120.77777862548828)),y=F(baseY+F(3.8888888359069824)),subtitleY=F(baseY+F(27));
  key='EXE_SPELL_PRACTICE_STAGE_ITEM_'+(stage===6?'EX':'FMT');publish(0x16ed0+stage*288,0x73c+stage,format(localize(key),stage+1),{key,x:92.44444274902344,y});
  key=unlocked?'ST_STAGE'+(stage+1)+'_STAGE_NAME':'EXE_UNKNOWN_SPELLCARD_NAME';publish(0x17e90+stage*288,0x74a+stage,localize(key),{key,x:106.22222137451172,y:subtitleY,scale:.8,color:0xe0ffff});
  key=mainUnlocked?bossKeys[stage]:'EXE_UNKNOWN_SPELLCARD_NAME';publish(0x176b0+stage*288,0x743+stage,localize(key),{key,x:286.4444580078125,y});
  const attempts=unlocked?rows.filter(attempted).length:0,captures=unlocked?rows.filter(r=>attempted(r)&&r.difficulty<5&&Boolean(records.get(r.id)?.practiceCaptures[r.difficulty*4+profile])).length:0;
  state.completeFlags[stage]=rows.length>0&&captures===rows.length&&attempts===rows.length;
  const pad=x=>String(x).padStart(2,' '),text=pad(captures)+' / '+pad(attempts)+' / '+pad(mainUnlocked?rows.length:'?');
  publish(0x18670+stage*288,0x751+stage,text,{x:487.22222900390625,y});
 }
}
