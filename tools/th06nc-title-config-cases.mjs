import {readFileSync} from 'node:fs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {TitleScene} from '../shared/th06nc/title-scene.mjs';
import {titleResources} from '../shared/th06nc/title-layout.mjs';
import {selectionResources,initializeSelectionAnimations} from '../shared/th06nc/title-selection-layout.mjs';
import {createGameConfig} from '../shared/th06nc/config-file.mjs';
const refs=[...titleResources,...selectionResources];
const resources=new Map(refs.map(ref=>[ref.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+ref.file))]));
const cases=[];
let baseline;
for(const state of [3,9,14])for(const difficulty of [1,4])
 for(const configuredDifficulty of [0,4])for(const mode of [0,1])for(const high of [0,1])
  for(const frame of [14,15,30])for(const held of [0,256,512,768])for(const selection of [0,1]){
   const config=createGameConfig();config[21]=configuredDifficulty;config[23]=mode;config[24]=high;
   const scene=new TitleScene(resources,{optionsServices:{config},extraAvailable:true,extraUnlockedShots:[[true,true],[true,true]]});
   initializeSelectionAnimations(scene.group,resources);
   Object.assign(scene.state,{state,difficulty,frame,selection,practice:0,spell:0,pulse:0,totalFrame:0});
   baseline??=[...scene.group.slots].map(([offset,vm])=>({offset,file:[...resources].find(([,resource])=>resource===vm.resource)?.[0],bytes:Buffer.from(vm.state).toString('hex')}));
   const before=[...config],initial={...scene.state};
   scene.tick(held);
   cases.push({initial,held,before,after:[...config]});
  }
console.log(JSON.stringify({refs,baseline,cases}));
