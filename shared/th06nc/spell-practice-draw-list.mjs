const F=Math.fround;

// 4e880: transient XY translation and alpha, restored after the draw request.
export function drawSpellFade(vm,draw,{offsetX=0,offsetY=0,alpha=1}={}){
 alpha=F(alpha);if(alpha<=0)return;
 const {v}=vm,position=vm.state.slice(0xc8,0xd4),color=v.getUint32(0xec,true);
 try{
  v.setFloat32(0xc8,F(F(offsetX)+v.getFloat32(0xc8,true)),true);v.setFloat32(0xcc,F(F(offsetY)+v.getFloat32(0xcc,true)),true);
  if(!(alpha>=1)){const a=Math.trunc(F(F(F(color>>>24)*alpha)+F(.5)));v.setUint32(0xec,((a<<24)|(color&0xffffff))>>>0,true);}
  draw(vm,{snap:true});
 }finally{vm.state.set(position,0xc8);v.setUint32(0xec,color,true);}
}

// 532e0: one selected sprite and one reused ordinary sprite. The row placement
// is persistent; the lower-level draw helper restores only its own translation.
export function drawSpellList(group,draw,{offset,count,selection,x,y,step,selectedOffsetX=0,selectedOffsetY=0,color=0xffffffff,progress=null,slide=0}){
 const selected=group.slots.get(offset),ordinary=group.slots.get(offset+288);if(!selected||!ordinary)throw Error('TH06nc: spell-list VM pair missing');
 const request=(vm,index,isSelected)=>{
  const alpha=F(progress?progress[index]:1),{v}=vm;
  v.setFloat32(0xc8,isSelected?F(F(x)+F(selectedOffsetX)):F(F(x)+F(0)),true);
  const rowY=F(F(F(index)*F(step))+F(y));v.setFloat32(0xcc,isSelected?F(rowY+F(selectedOffsetY)):F(rowY+F(0)),true);v.setFloat32(0xd0,0,true);v.setUint32(0xec,isSelected?color>>>0:0xffffffff,true);
  drawSpellFade(vm,draw,{offsetX:F(F(F(1)-alpha)*F(slide)),offsetY:0,alpha});
 };
 for(let i=0;i<(count|0);i++)if(i!==(selection|0))request(ordinary,i,false);
 if((selection|0)>=0&&(selection|0)<(count|0))request(selected,selection|0,true);
}
