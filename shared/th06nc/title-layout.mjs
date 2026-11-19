// Title startup resource table, native 0x140047b88..0x140047de3.
export const titleResources=Object.freeze([
 ['title01.anm',0x15,0x100],['title02.anm',0x1b,0x133],
 ['title03.anm',0x1c,0x13c],['title04.anm',0x1d,0x146],
 ['title01s.anm',0x16,0x1ad],['title04s.anm',0x17,0x1e0],
 ['title05.anm',0x18,0x217],['title00.anm',0x19,0x218],
 ['title06.anm',0x1a,0x21a],
].map(([file,slot,base])=>Object.freeze({file,slot,base})));
// Native title owner offsets, not draw order. Disabled-menu bytes at 0x158e0
// gate creation of the 0x100..0x17c slots in the original initializer.
export function titleVmSlots(disabled=new Uint8Array(0x7d)){
 if(disabled.length!==0x7d)throw Error('TH06nc: invalid title disabled vector');
 return [{offset:0x15990,id:0x217},
  ...Array.from({length:0x7d},(_,i)=>({offset:0x9640+i*0x120,id:0x100+i})).filter((_,i)=>!disabled[i]),
  {offset:0x16170,id:0x218},{offset:0x16290,id:0x219},
  ...Array.from({length:4},(_,i)=>({offset:0x163b0+i*0x120,id:0x21a+i}))];
}
