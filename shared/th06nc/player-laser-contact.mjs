const F=Math.fround;
function queue(slots,sound,disabled){if(disabled)return;for(let i=0;i<3;i++){if(slots[i]<0){slots[i]=sound;break;}if(slots[i]===sound)break;}}
// Player collision helper 6aba0..6af60: rotate the player into laser space,
// test the hit circle, then the expanded grazing rectangle and update reactions.
export function collidePlayerWithLaser({center,size,origin,angle,graze},{player,environment={},spawnEffect=null,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos}={}){
 if(!player)throw Error('TH06nc: laser collision needs player state');
 const p=player.position.map(F),ox=F(origin[0]),oy=F(origin[1]),dx=F(p[0]-ox),dy=F(p[1]-oy),s=F(sin(F(angle))),c=F(cos(F(angle)));
 const x=F(F(F(s*dy)+F(c*dx))+ox),y=F(F(F(c*dy)-F(s*dx))+oy),hx=F(F(size[0])*F(0.5)),hy=F(F(size[1])*F(0.5));
 let left=F(F(center[0])-hx),right=F(F(center[0])+hx),top=F(F(center[1])-hy),bottom=F(F(center[1])+hy);
 const radius=F(player.hitRadius),radiusSquared=F(radius*radius),distance=()=>{const px=left>x?left:Math.min(right,x),py=top>y?top:Math.min(bottom,y),vx=F(x-px),vy=F(y-py);return F(F(vy*vy)+F(vx*vx));};
 const effect=(type,count,color,position)=>{if(!spawnEffect)throw Error('TH06nc: player reaction effect service missing');spawnEffect({type,count,color,position});};
 if(radiusSquared>distance()){
  if((player.state&255)!==0)return 0;
  environment.spellActive=false;effect(12,1,0xff4040ff,p);effect(6,16,0xffffffff,p);player.state=2;player.deathBombFrames=8;player.hitTimer={previous:-999,frame:0};queue(soundSlots,4,soundDisabled);player.hitAnimationTimers=[{previous:-999,frame:2},{previous:-999,frame:2}];return 1;
 }
 if(!graze)return 0;left=F(left-F(48));right=F(right+F(48));top=F(top-F(48));bottom=F(bottom+F(48));
 if(!(radiusSquared>distance())||[1,2].includes(player.state&255))return 0;
 if(!environment.grazeCountersDisabled){if((environment.stageGraze|0)<99999)environment.stageGraze=((environment.stageGraze|0)+1)|0;if((environment.totalGraze|0)<999999)environment.totalGraze=((environment.totalGraze|0)+1)|0;}
 const position=p.map(x=>F(F(x+x)*F(0.5)));effect(8,1,0xffffffff,position);environment.score=(BigInt(environment.score??0)+500n)&0xffffffffffffffffn;environment.inputFlags=((environment.inputFlags??0)&~64)|128;queue(soundSlots,30,soundDisabled);return 2;
}
