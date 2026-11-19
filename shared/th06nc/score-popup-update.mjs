const F=Math.fround;
// Common text task priority 1, popup block 9100..920e. Story/game-over UI
// replaces this block; caller supplies that suspension state.
export function advanceScorePopups(pool,{suspended=false}={}){
 if(suspended)return;
 const v=new DataView(pool.storage.buffer,pool.storage.byteOffset,pool.storage.byteLength);
 for(let slot=0;slot<515;slot++){
  const p=slot*40;if(!v.getUint8(p+0x1c))continue;v.setFloat32(p+0x14,F(v.getFloat32(p+0x14,true)-F(.5)),true);const frame=v.getInt32(p+4,true);v.setInt32(p,frame,true);v.setInt32(p+4,(frame+1)|0,true);if(((frame+1)|0)>60)v.setUint8(p+0x1c,0);
 }
}
