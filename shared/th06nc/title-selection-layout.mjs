// State-8 base selection resource sequence, native 0x14004aab0..0x14004ad10.
export const selectionResources=Object.freeze([
 ['slpl00a.anm',30,0x17d],['slpl00b.anm',31,0x17e],
 ['slpl01a.anm',32,0x17f],['slpl01b.anm',33,0x180],
 ['select01.anm',34,0x181],['select02.anm',35,0x184],
 ['select05.anm',38,0x186],['select03.anm',36,0x187],
 ['select04.anm',37,0x189],['select06.anm',39,0x18d],
 ['select07.anm',40,0x191],
].map(([file,slot,base])=>Object.freeze({file,slot,base})));
export function selectionLoadPlan({frame,practice,spell,difficulty}){
 if(frame<50)return null;
 return {backgroundEnabled:false,unload:[21,22,23,24,25,26,27,28,29,65,66,67],
  background:spell?'data/title/select00e.png':practice?'data/title/select00c.png':difficulty===4?'data/title/select00b.png':'data/title/select00.png',
  resources:selectionResources};
}
export function initializeSelectionAnimations(group,resources,{disabled=new Uint8Array(173),spell=false}={}){
 if(spell)throw Error('TH06nc: Spell selection owner not yet implemented');
 for(const ref of selectionResources)if(!resources.has(ref.file))throw Error(`TH06nc: missing selection resource ${ref.file}`);
 for(const slot of [21,22,23,24,25,26,27,28,29,65,66,67])group.bank.unload(slot);
 for(const ref of selectionResources){const resource=resources.get(ref.file);if(!resource)throw Error(`TH06nc: missing selection resource ${ref.file}`);group.bank.load(resource,ref.base,{slot:ref.slot});}
 for(let i=0;i<22;i++){
  const offset=0x122e0+i*288;
  if(disabled[125+i]){const previous=group.slots.get(offset);if(previous)previous.v.setUint32(0xc4,previous.v.getUint32(0xc4,true)&~1,true);continue;}
  const vm=group.bank.createVm(0x17d+i,{allowMissing:true});vm.tick();
  vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|8|0x2000,true);
  vm.v.setUint32(0xec,0xffffffff,true);
  for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);
  vm.v.setUint16(0x36,vm.v.getUint16(0x34,true),true);group.slots.set(offset,vm);
 }
}
export function finishSelectionEntry(group,initial){
 if(initial.spell)throw Error('TH06nc: Spell selection owner tail not yet implemented');
 const state={...initial,state:9,frame:0,totalFrame:0,pulse:0,backgroundEnabled:false,
  menuFadePreviousDuration:initial.menuFadeDuration??0,menuFadeDuration:0,menuFadeTicks:0,menuFadeStartColor:0,
  selection:initial.difficulty<4?initial.configuredDifficulty:0};
 const interrupt=initial.difficulty<4?6:18;
 for(const [offset,vm]of group.slots)if(offset>=0x9640&&offset<0x15900)vm.interrupt(interrupt);
 for(let i=0;i<4;i++)group.slots.get(0x122e0+i*288)?.interrupt(0);
 return {state,effects:initial.fastEntry?[]:[{kind:'entryFade',frames:30,alpha:255,mode:3}]};
}
