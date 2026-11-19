// Shared projectile/effect ANMs, loader 11f92..11fee.
export function commonProjectileAssetPlan(){return [
 {file:'etama3.anm',archive:'th06CM.dat',slot:6,base:0x200},
 {file:'etama3_2.anm',archive:'th06CM.dat',slot:0x34,base:0x29a},
 {file:'etama4.anm',archive:'th06CM.dat',slot:7,base:0x2ba}
];}
// Effect initializer 2b390..2b44a.
export function stageEffectAssetPlan(stage){
 if(!Number.isInteger(stage)||stage<1||stage>7)throw Error('TH06nc: invalid effect stage');
 return {file:`eff0${[1,2,3,4,5,5,4][stage-1]}.anm`,archive:'th06ST.dat',slot:11,base:0x2d3};
}
export function loadProjectileAndEffectBank(bank,resources,stage){
 const refs=[...commonProjectileAssetPlan(),stageEffectAssetPlan(stage)];
 for(const r of refs)if(!resources.has(r.file))throw Error(`TH06nc: missing common ANM ${r.file}`);
 for(const r of refs)bank.load(resources.get(r.file),r.base,{slot:r.slot});return refs;
}
