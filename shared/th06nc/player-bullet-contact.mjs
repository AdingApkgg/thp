const F=Math.fround;
// Original 6a980: bomb-area cancellation first, then circle/rectangle hit test.
export function collidePlayerWithBullet({position,size,circle=true},{player,environment={},queryCancel=null,spawnEffect=null,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 if(!player)throw Error('TH06nc: bullet contact requires player state');
 const x=F(position[0]),y=F(position[1]),hx=F(F(size[0])*F(0.5)),hy=F(F(size[1])*F(0.5)),left=F(x-hx),right=F(x+hx),top=F(y-hy),bottom=F(y+hy);
 if(queryCancel?.({left,top,right,bottom}))return 2;
 const px=F(player.position[0]),py=F(player.position[1]);let distance,radius;
 if(circle){const dx=F(px-x),dy=F(py-y);distance=F(F(dy*dy)+F(dx*dx));radius=F(F(F(Math.min(F(size[1]),F(size[0])))*F(0.5))+F(player.hitRadius));}
 else{const cx=left>px?left:Math.min(right,px),cy=top>py?top:Math.min(bottom,py),dx=F(px-cx),dy=F(py-cy);distance=F(F(dy*dy)+F(dx*dx));radius=F(player.hitRadius);}
 if(!(F(radius*radius)>distance))return 0;
 if((player.state&255)===0){
  if(!spawnEffect)throw Error('TH06nc: player hit effect service missing');environment.spellActive=false;const p=player.position.map(F);spawnEffect({type:12,count:1,color:0xff4040ff,position:p});spawnEffect({type:6,count:16,color:0xffffffff,position:p});player.state=2;player.deathBombFrames=8;player.hitTimer={previous:-999,frame:0};
  if(!soundDisabled&&!soundSlots.includes(4)){const i=soundSlots.findIndex(x=>x<0);if(i>=0)soundSlots[i]=4;}player.hitAnimationTimers=[{previous:-999,frame:2},{previous:-999,frame:2}];
 }
 return 1;
}
