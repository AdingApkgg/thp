// Menu helper 0x14004d1f0 and sampled-key repeat phase 0x140079d37..79d7a.
export class TitleInput {
 constructor(){this.held=0;this.clock=0;}
 sample(held){
  held>>>=0;const previous=this.held;let repeat=0;
  if(held===previous){
   if(this.clock>=30&&(this.clock&7)===0)repeat=1;
   if(this.clock>=38)this.clock=30;
   this.clock=(this.clock+1)>>>0;
  }else this.clock=0;
  this.held=held;return {held,previous,repeat};
 }
}
export function navigateTitle(selection,count,{held,previous,repeat},{disabled=false,slots=[-1,-1,-1]}={}){
 let direction=0;
 if((held&0x10)&&((previous&0x10)!==(held&0x10)||repeat!==0))direction=-1;
 else if((held&0x20)&&((previous&0x20)!==(held&0x20)||repeat!==0))direction=1;
 if(!direction)return {selection,direction,soundSlots:[...slots]};
 selection=(selection+direction)|0;
 const soundSlots=[...slots];
 if(!disabled)for(let i=0;i<3;i++){
  if(soundSlots[i]<0){soundSlots[i]=12;break;}
  if(soundSlots[i]===12)break;
 }
 if(selection<0)selection=(count-1)|0;
 if(selection>=count)selection=0;
 return {selection,direction,soundSlots};
}
