// Original stage tables 3de330/308500 and enemy resource setup 37170.
export function stageAssetPlan(stage){
 if(!Number.isInteger(stage)||stage<1||stage>7)throw Error('TH06nc: invalid stage');
 return {stage,ecl:`ecldata${stage}.ecl`,enemyAnimations:[{file:`stg${stage}enm.anm`,archive:'th06ST.dat',slot:8,base:0x100},
  ...([1,2,5,6,7].includes(stage)?[{file:`stg${stage}enm2.anm`,archive:'th06ST.dat',slot:9,base:0x100}]:[])]};
}
export function loadStageEnemyBank(bank,resources,stage){
 const plan=stageAssetPlan(stage);for(const ref of plan.enemyAnimations)if(!resources.has(ref.file))throw Error(`TH06nc: missing stage enemy ANM ${ref.file}`);
 bank.unload(8);bank.unload(9);for(const ref of plan.enemyAnimations)bank.load(resources.get(ref.file),ref.base,{slot:ref.slot});return plan;
}
