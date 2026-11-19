const F=Math.fround;
// Native 6a8c0: 16 bomb cancellation rectangles, touching edges included.
// Width zero alone disables a slot; retain signed and unordered comparisons.
export function queryPlayerBombCancel(player,{left,top,right,bottom}){
 const {v}=player;left=F(left);top=F(top);right=F(right);bottom=F(bottom);
 for(let i=0;i<16;i++){
  const p=0x7754+i*16,width=v.getFloat32(p,true);if(width===0)continue;
  const halfWidth=F(width*F(.5)),x=v.getFloat32(p+8,true);if(F(x-halfWidth)>right||left>F(x+halfWidth))continue;
  const halfHeight=F(v.getFloat32(p+4,true)*F(.5)),y=v.getFloat32(p+12,true);if(F(y-halfHeight)>bottom||top>F(y+halfHeight))continue;
  return true;
 }
 return false;
}
