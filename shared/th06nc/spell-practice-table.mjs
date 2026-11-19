import {readMessagePack} from './messagepack.mjs';

// Resource projection in 76b90..77540. Stage indices stay zero based.
// The native allocation has 40-byte records; trailing allocation padding is
// deliberately not exposed as meaningful state.
export function readSpellPracticeTable(input){
 const root=readMessagePack(input);
 if(root?.version!==6||!Array.isArray(root.entries))throw Error('TH06nc: invalid spell-practice table version or entries');
 const encoder=new TextEncoder();
 return root.entries.flatMap(row=>{
  // Native skips array entries whose length is not seven.
  if(!Array.isArray(row)||row.length!==7)return [];
  if(row.slice(0,6).some(n=>!Number.isInteger(n)||n<0||n>0xffffffff))throw Error('TH06nc: invalid spell-practice integer');
  const name=row[6];if(typeof name!=='string'||name.includes('\0')||encoder.encode(name).length>31)throw Error('TH06nc: invalid spell-practice name');
  return [{id:row[0]&255,stageIndex:row[1]&255,subroutine:row[2]&65535,difficulty:row[3]&255,order:row[4]&255,midboss:row[5]&255,name}];
 });
}

// Native 466d0: an ID lookup, not an index into the table.
export function findSpellPractice(table,id){return table.find(row=>row.id===(id&255))??null;}

// Native 46850: any attempted difficulty unlocks this stage/card row.
export function spellPracticeOrderUnlocked(table,records,stageIndex,order){
 return table.some(row=>row.stageIndex===(stageIndex|0)&&row.order===(order|0)&&row.id<134&&Boolean(records.get(row.id)?.attempts));
}

// Native 46740: every catalog entry must have an ordinary attempt and a
// practice capture for the currently configured character/shot.
export function spellPracticeStageComplete(table,records,stageIndex,character,shot){
 const rows=table.filter(row=>row.stageIndex===(stageIndex|0)),profile=(character&255)*2+(shot&255);
 return rows.length>0&&rows.every(row=>row.id<134&&Boolean(records.get(row.id)?.attempts)&&row.difficulty<5&&profile<4&&Boolean(records.get(row.id)?.practiceCaptures[row.difficulty*4+profile]));
}

// Native 46900: count grouped card rows and keep the selection in an eight-row
// viewport. This helper does not change the caller's selected card.
export function spellPracticeViewport(table,stageIndex,selection,scroll){
 const count=table.reduce((n,row)=>row.stageIndex===(stageIndex&255)?Math.max(n,row.order+1):n,0),visible=Math.min(count,8),maxScroll=Math.max(0,count-visible);
 selection|=0;let start=Math.max(0,Math.min(scroll|0,maxScroll));
 if(visible>0&&selection<start)start=Math.max(0,selection);
 else if(visible>0&&selection>=start+visible)start=Math.min(maxScroll,selection-visible+1);
 return {count,start,visible,end:start+visible};
}
