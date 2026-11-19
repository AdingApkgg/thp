// Browser acceptance driver: observes live hazards and sends ordinary controls.
// A short beam search may turn every two ticks instead of committing to a long
// straight movement. It never writes game owners, timers, stocks or score.
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const directions=[[0,0,0],[16,0,-1],[32,0,1],[64,-1,0],[128,1,0],[80,-Math.SQRT1_2,-Math.SQRT1_2],[144,Math.SQRT1_2,-Math.SQRT1_2],[96,-Math.SQRT1_2,Math.SQRT1_2],[160,Math.SQRT1_2,Math.SQRT1_2]];
const cell=32,depth=6,width=24,safe=16;
const key=(x,y)=>Math.floor(x/cell)+Math.floor(y/cell)*256;
function obstacleGrids(hazards){
 const grids=[];
 for(let t=1;t<=depth*2;t++){
  const grid=new Map();
  for(const bullet of hazards.bullets){
   const x=bullet.position[0]+bullet.velocity[0]*t,y=bullet.position[1]+bullet.velocity[1]*t,r=Math.max(...bullet.size)*.5+1.25;
   if(x+r+safe<8||x-r-safe>376||y+r+safe<16||y-r-safe>432)continue;
   const obstacle={x,y,r},reach=r+safe;
   for(let row=Math.floor((y-reach)/cell);row<=Math.floor((y+reach)/cell);row++)for(let col=Math.floor((x-reach)/cell);col<=Math.floor((x+reach)/cell);col++){
    const k=col+row*256;if(!grid.has(k))grid.set(k,[]);grid.get(k).push(obstacle);
   }
  }
  grids.push(grid);
 }
 return grids;
}
function clearance(x,y,grid,hazards){
 let margin=safe;
 for(const b of grid.get(key(x,y))??[]){margin=Math.min(margin,Math.hypot(x-b.x,y-b.y)-b.r);if(margin<0)return margin;}
 if(hazards.boss)margin=Math.min(margin,Math.hypot(x-hazards.boss[0],y-hazards.boss[1])-36);
 for(const laser of hazards.lasers){
  if(laser.mode===2)continue;
  const rx=x-laser.origin[0],ry=y-laser.origin[1],c=Math.cos(laser.angle),s=Math.sin(laser.angle),along=c*rx+s*ry,across=-s*rx+c*ry;
  const outside=Math.max(laser.tail-along,0,along-laser.head),side=Math.max(Math.abs(across)-laser.width*.25,0);
  margin=Math.min(margin,Math.hypot(outside,side)-1.25);
 }
 return margin;
}
export function planInput(hazards,state){
 const speed=hazards.focusSpeed||2,actions=directions.flatMap(([mask,x,y])=>[true,false].map(focus=>({mask:(focus?13:9)|mask,vx:x*speed*(focus?1:2),vy:y*speed*(focus?1:2),focus})));
 const item=hazards.items.filter(item=>item.type!==1&&item.type!==6&&(state.playerPower<128||![0,2,4].includes(item.type))&&item.position[1]>150&&item.position[1]<420).sort((a,b)=>Math.hypot(a.position[0]-hazards.position[0],a.position[1]-hazards.position[1])-Math.hypot(b.position[0]-hazards.position[0],b.position[1]-hazards.position[1]))[0];
 const target=hazards.boss&&state.playerPower>=64&&![3,5].includes(item?.type)?[hazards.boss[0],400]:item?.position??[192,380];
 const grids=obstacleGrids(hazards);let beam=[{x:hazards.position[0],y:hazards.position[1],cost:0,first:13,last:13,rank:0}],best=13;
 for(let d=0;d<depth;d++){
  const candidates=new Map();
  for(const node of beam)for(const action of actions){
   let x=node.x,y=node.y,margin=safe;
   for(let tick=0;tick<2;tick++){x=clamp(x+action.vx,8,376);y=clamp(y+action.vy,16,432);margin=Math.min(margin,clearance(x,y,grids[d*2+tick],hazards));}
   if(margin<0)continue;
   const cost=node.cost+(safe-margin)*.2+(action.focus?0:.1)+(action.mask===node.last?0:.15),rank=cost/(d+1)+Math.abs(x-target[0])*.06+Math.abs(y-target[1])*.035;
   const candidate={x,y,cost,rank,first:d?node.first:action.mask,last:action.mask},k=Math.round(x/4)+Math.round(y/4)*256;
   if(!candidates.has(k)||candidates.get(k).rank>rank)candidates.set(k,candidate);
  }
  if(!candidates.size)break;
  beam=[...candidates.values()].sort((a,b)=>a.rank-b.rank).slice(0,width);best=beam[0].first;
 }
 return best;
}
export async function advanceStandardBot(){
 const game=globalThis.th06ncGame;let state=game.report(),advanced=0;
 for(let step=0;step<60&&state.phase==='game';step++){
  if(state.playerState===2&&state.bombs>0){await game.advance(1,13);state=await game.advance(1,15);advanced+=2;continue;}
  const hazards=game.hazards();let mask=hazards&&state.dialog<0?planInput(hazards,state):9;
  if(hazards&&state.dialog<0&&state.playerPower<64&&state.bombs===3&&!state.bombActive&&hazards.bullets.length>=30)mask|=2;
  state=await game.advance(2,mask);advanced+=2;
 }
 return {...state,botTicks:advanced};
}
