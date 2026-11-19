import {queueSound} from './sound-queue.mjs';
const F=Math.fround;
export function readCreditPages(bytes){const root=JSON.parse(new TextDecoder().decode(bytes));if(!Array.isArray(root))throw Error('TH06nc credits: page array required');const pages=root.filter(Array.isArray).map(page=>page.filter(row=>typeof row==='string'));if(!pages.length)throw Error('TH06nc credits: empty page array');return pages;}
export function publishCreditsPages(state,pages,publishText,{initialize=false}={}){
 const {v}=state,first=v.getInt32(0x2c,true);
 for(let column=0;column<2;column++)for(let row=0;row<22;row++){
  const offset=0x48+(column*22+row)*288,vm=initialize?state.sprite(offset,0x737+column*22+row):state.vm(offset),text=pages[first+column]?.[row]??'';
  if(text.length){vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|2,true);publishText(vm,{offset,text,colors:[0xfffffe,0,0x10101,0x40202]});}else vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)&~2,true);
  vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x300)|0x400,true);vm.v.setFloat32(0xc8,column===0?64:471,true);vm.v.setFloat32(0xcc,F(F(F(row)*F(17))+F(35)),true);vm.v.setFloat32(0xd0,0,true);
 }
}
// Initialization tail14ac1..14c8e follows JSON admission/resource allocation.
export function initializeCredits(state,{pages,publishText,fade}={}){
 const {v}=state;v.setInt32(0x30,pages.length,true);v.setBigUint64(0x28,0n,true);v.setBigUint64(0x10,0n,true);v.setBigUint64(0x18,71n,true);v.setBigUint64(0x20,5n,true);publishCreditsPages(state,pages,publishText,{initialize:true});if(fade?.mode===2)fade.requestIn(0,30);
}
// Update13790..13bee, including warm-up, edge-only two-page navigation,
// actual44 text-VM refresh and unsigned30-tick exit independent of fade.
export function advanceCredits(state,{pages,publishText,held=0,previous=0,fade,soundSlots=[-1,-1,-1],soundDisabled=false,returnTitle=()=>{}}={}){
 const {v}=state;let slide=v.getInt32(0x20,true);if(slide<5)v.setInt32(0x20,++slide,true);
 if(v.getUint8(0x34)){const exit=(v.getInt32(0x38,true)+1)|0;v.setInt32(0x38,exit,true);if((exit>>>0)>=30){returnTitle();return 0;}return 1;}
 const old=v.getInt32(0x14,true),edge=bit=>Boolean(held&bit)&&((held&bit)!==(previous&bit)),sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled});
 if(old===1){
  const delta=edge(64)?-2:edge(128)?2:0;
  if(slide>=5&&delta){let page=v.getInt32(0x2c,true);v.setInt32(0x28,page,true);page=(page+delta)|0;if(page<0)page=Math.trunc((v.getInt32(0x30,true)-1)/2)*2;else if(page>=v.getInt32(0x30,true))page=0;v.setInt32(0x2c,page,true);sound(12);v.setInt32(0x24,delta/2,true);v.setBigUint64(0x1c,44n,true);publishCreditsPages(state,pages,publishText);}
  if(edge(512)){sound(11);v.setUint8(0x34,1);v.setInt32(0x38,0,true);fade?.requestOut(0,30);}
 }else if(old===0&&v.getInt32(0x10,true)>=8)v.setInt32(0x14,1,true);
 v.setInt32(0x10,old===v.getInt32(0x14,true)?(v.getInt32(0x10,true)+1)|0:0,true);
 if(!v.getUint8(0x34)){if(v.getInt32(0x1c,true)<44)v.setInt32(0x1c,(v.getInt32(0x1c,true)+1)|0,true);const pulse=(v.getInt32(0x18,true)+1)|0;v.setInt32(0x18,pulse-Math.trunc(pulse/72)*72,true);}
 return 1;
}

