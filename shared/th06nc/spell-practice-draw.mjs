import {drawSpellFade,drawSpellList} from './spell-practice-draw-list.mjs';
import {drawSpellTransition,drawSpellListEdge,spellPulseAlpha,spellDifficultyColor} from './spell-practice-draw-effects.mjs';
import {drawSpellHighlight} from './spell-practice-highlight.mjs';
import {spellPracticeViewport,spellPracticeOrderUnlocked} from './spell-practice-table.mjs';
const F=Math.fround;
const ease=(frame,start,duration)=>{
 if(frame<=start)return F(0);if(frame>=start+duration)return F(1);
 const t=F(F(1)-F(F((frame-start)|0)/F(duration)));return F(F(1)-F(F(t*t)*t));
};

// Actual Spell Practice owner draw 53500..54869. The caller supplies the
// initialized text, selection and scratch VMs and owns texture submission.
export function drawSpellPractice(group,state,draw,{table,records,character,shot,hasTexture=()=>true}={}){
 if(![28,29,30,31].includes(state.state))return;
 const vm=offset=>{const value=group.slots.get(offset);if(!value)throw Error('TH06nc: spell draw VM missing '+offset.toString(16));return value;};
 const tint=(offset,color)=>{const value=vm(offset);value.v.setUint32(0xec,color>>>0,true);return value;};
 const place=(value,x,y,{z=0,color=0xffffffff,visible=false}={})=>{const v=value.v;v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,y,true);if(z!==null)v.setFloat32(0xd0,z,true);v.setUint32(0xec,color>>>0,true);if(visible)v.setUint32(0xc4,v.getUint32(0xc4,true)|1,true);};
 const fade=(offset,options)=>drawSpellFade(vm(offset),draw,options),direct=offset=>draw(vm(offset),{snap:true});
 const pulseColor=((spellPulseAlpha(state.pulse??0,128)<<24)|0xffffff)>>>0,profile=(character&255)*2+(shot&255),stage=state.spellStage|0;
 const highlighted=state.state===30||state.state===31,icon=vm(0x1a298);icon.bindSprite(0x7cc+profile);
 const entryFrame=state.fastEntry&&state.state===28?state.frame|0:54;
 const first=ease(entryFrame,0,30),second=ease(entryFrame,4,26);
 fade(0x19998,{offsetX:F(26.66666603088379),offsetY:F(F(-6.222222328186035)-F(F(F(1)-first)*F(120))),alpha:first});
 const headingY=F(F(F(F(1)-second)*F(-36))-F(6.222222328186035));
 tint(0x16930,0xffe8c890);fade(0x16930,{offsetX:F(26.66666603088379),offsetY:headingY,alpha:second});
 tint(0x19870,0xc0ffffff);fade(0x19870,{offsetX:F(26.66666603088379),offsetY:headingY,alpha:second});
 const panel=(x,offsetX=0,alpha=1)=>{
  const value=vm(0x1a3b8);if(!value.pointer(0x100)||value.boundBinding?.active===false||!hasTexture(value))return;
  place(value,F(x),F(96.44444274902344),{z:null,visible:true});fade(0x1a3b8,{offsetX,alpha});
 };
 if(state.state===28){
  const progress=Array.from({length:7},(_,i)=>ease(entryFrame,8+i*3,26));
  drawSpellList(group,draw,{offset:0x19bd8,count:7,selection:stage,x:F(50.11111068725586),y:F(119.11111450195312),step:F(45),selectedOffsetX:F(-11.555553436279297),selectedOffsetY:F(-9.777777671813965),progress,slide:F(-560)});
  const sx=F(F(F(F(icon.v.getFloat32(0xe8,true)*F(.5))*F(480))/F(1080))*F(119));
  const sy=F(F(F(F(icon.v.getFloat32(0xe4,true)*F(.5))*F(480))/F(1080))*F(169));
  for(let i=0;i<7;i++){
   const alpha=progress[i],shift=F(F(-27.11111068725586)-F(F(F(1)-alpha)*F(560)));
   const unlocked=table.some(r=>r.stageIndex===i&&r.id<134&&Boolean(records.get(r.id)?.attempts));
   const color=i===stage?pulseColor:unlocked?0xc0ffffff:0x60909090;
   for(const offset of [0x16ed0,0x17e90,0x176b0]){tint(offset+i*288,color);fade(offset+i*288,{offsetX:shift,alpha});}
   const matching=(state.completePending||state.completeClock>0)&&i===state.completeStage&&profile===state.completeProfile;
   if(state.completeFlags?.[i]&&!(matching&&state.completePending)){
    const stats=vm(0x18670+i*288).v;
    let x=F(stats.getFloat32(0xc8,true)-F(3.555555582046509));x=F(x-sx);x=F(x+shift);x=F(x+F(.8888888955116272));
    let y=F(F(stats.getInt32(0x118,true))*stats.getFloat32(0xe4,true));y=F(y*F(480));y=F(y/F(1080));y=F(y-sy);y=F(y*F(.5));y=F(y+stats.getFloat32(0xcc,true));y=F(y+F(.8888888955116272));
    const gray=i===stage||matching&&state.completeClock>0?spellPulseAlpha(state.pulse??0,208):128;
    let markColor=(0xff000000|gray*0x10101)>>>0;
    if(alpha<=0)markColor&=0xffffff;else if(alpha<1)markColor=((Math.trunc(F(F(F(markColor>>>24)*alpha)+F(.5)))<<24)|(markColor&0xffffff))>>>0;
    drawSpellHighlight(icon,draw,{x,y,color:markColor,ticks:state.profileTransition,direction:state.orderDirection,noticeClock:matching?state.completeClock:0,hasTexture:hasTexture(icon)});
   }
   drawSpellTransition(vm(0x18670+i*288),draw,{color,ticks:state.difficultyTransition,direction:state.orderDirection,offsetX:shift,alpha});
  }
  const alpha=ease(entryFrame,6,24),shift=F(F(-27.11111068725586)-F(F(F(1)-alpha)*F(64)));
  for(const x of [77.33333587646484,271.3333435058594,466.3333435058594])panel(x,shift,alpha);
  for(const offset of [0x16a50,0x16b70,0x16c90]){tint(offset,0xffe8c890);fade(offset,{offsetX:shift,alpha});}
  return;
 }
 panel(50.66667175292969);tint(0x16a50,0xffe8c890);direct(0x16a50);
 const viewport=spellPracticeViewport(table,stage,state.spellOrder,state.spellScroll);
 drawSpellList(group,draw,{offset:0x19e18,count:viewport.visible,selection:state.spellOrder-viewport.start,x:F(50.55555725097656),y:F(119.11111450195312),step:F(32),selectedOffsetX:F(-8.44444465637207),selectedOffsetY:F(-6.888888835906982),color:state.state===29?0xffffffff:0xc0ffffff});
 const preview=viewport.end<viewport.count;
 if(preview){place(vm(0x19f38),F(50.55555725097656),F(375.1111145019531),{color:0x3fffffff});drawSpellListEdge(vm(0x19f38),draw);}
 const user=vm(0x16db0);
 for(let i=0;i<viewport.visible;i++){
  const order=viewport.start+i,unlocked=spellPracticeOrderUnlocked(table,records,stage,order);
  const color=order===state.spellOrder?(state.state===29?(pulseColor&0xffffc0c0)>>>0:0xc0ffc0c0):unlocked?0xc0ffffff:0x60909090;
  tint(0x16ed0+i*288,color);direct(0x16ed0+i*288);
  const boss=vm(0x177d0+i*288);
  if(boss.v.getInt32(0x114,true)>0){place(user,F(74.55555725097656),boss.v.getFloat32(0xcc,true),{z:null,color:((((color>>>24)*3)<<22)|0xe8c890)>>>0});draw(user,{snap:true});}
  tint(0x177d0+i*288,color);direct(0x177d0+i*288);
 }
 if(preview){const unlocked=spellPracticeOrderUnlocked(table,records,stage,viewport.end);tint(0x180d0,unlocked?0x54ffffff:0x2a909090);drawSpellListEdge(vm(0x180d0),draw);}
 panel(243.11111450195312);tint(0x16c90,0xffe8c890);direct(0x16c90);
 const count=stage===6?1:4;
 drawSpellList(group,draw,{offset:0x1a058,count,selection:highlighted?state.spellDifficulty:-1,x:F(243.11111450195312),y:F(119.11111450195312),step:F(76.66666412353516),selectedOffsetX:F(-17.111114501953125),selectedOffsetY:F(-16.66666603088379)});
 const scratch=vm(0x16050);scratch.v.setFloat32(0xe8,1,true);scratch.v.setFloat32(0xe4,1,true);
 for(let i=0;i<count;i++){
  const difficulty=stage===6?4:i,row=table.find(r=>r.stageIndex===stage&&r.order===state.spellOrder&&r.difficulty===difficulty)??null;
  const selected=highlighted&&i===state.spellDifficulty,attempted=row&&row.id<134&&Boolean(records.get(row.id)?.attempts);
  const color=selected?pulseColor:attempted?0xc0ffffff:0x60909090,baseY=F(F(F(i)*F(76.66666412353516))+F(117.77777862548828));
  scratch.bindSprite(0x792+difficulty);place(scratch,F(253.55555725097656),F(baseY+F(3.1111111640930176)),{color});draw(scratch,{snap:true});
  if(row){tint(0x18f70+i*288,color);direct(0x18f70+i*288);}
  tint(0x18670+i*288,color);direct(0x18670+i*288);
  if(!row)continue;
  const statsColor=selected?pulseColor:0xa0ffffff,matching=row===state.noticeRecord&&profile===state.noticeProfile;
  const captured=row.id<134&&row.difficulty<5&&profile<4&&Boolean(records.get(row.id)?.practiceCaptures[row.difficulty*4+profile]);
  if(captured&&!(matching&&state.noticePending)){
   const markColor=spellDifficultyColor(selected||matching&&state.noticeClock>0,state.pulse??0);
   drawSpellHighlight(icon,draw,{x:F(255.11111450195312),y:F(baseY+F(25.33333396911621)),color:markColor,ticks:state.profileTransition,direction:state.orderDirection,noticeClock:matching?state.noticeClock:0,hasTexture:hasTexture(icon)});
  }
  for(const offset of [0x18af0,0x181f0])drawSpellTransition(vm(offset+i*288),draw,{color:statsColor,ticks:state.difficultyTransition,direction:state.orderDirection});
  tint(0x193f0+i*288,((((color>>>24)*3)<<22)|0xe8c890)>>>0);direct(0x193f0+i*288);
 }
}
