// Text startup 7a817; HUD portrait/frame setup 3d500..3db35.
export function messageAssetPlan(stage,character=0){
 if(!Number.isInteger(stage)||stage<1||stage>7||![0,1].includes(character))throw Error('TH06nc message: invalid stage/character');
 const enemy=[null,[['03a',0x4c6],['03b',0x4c8]],[['05a',0x4c6]],[['06a',0x4c6],['06b',0x4c8]],[['08a',0x4c6],['08b',0x4c8]],[['09a',0x4c6],['09b',0x4c8]],[['09b',0x4c6],['10a',0x4c8],['10b',0x4c9]],[['08a',0x4c6],['12a',0x4c8],['12b',0x4c9]]][stage];
 return [{archive:'th06IN.dat',file:'text.anm',slot:0,base:0x72f},{archive:'th06ST.dat',file:'msgframe.anm',slot:64,base:0x785},...['a','b','c'].map((suffix,i)=>({archive:'th06CM.dat',file:`face0${character}${suffix}.anm`,slot:15+i,base:0x4c0+i*2})),...enemy.map(([name,base],i)=>({archive:'th06ST.dat',file:`face${name}.anm`,slot:18+i,base}))];
}
