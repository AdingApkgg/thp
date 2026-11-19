const F=Math.fround;
// World manager position integration, before ECL update: 374b1..3757c.
export function integrateEnemyPosition(enemy){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),mirror=Boolean(v.getUint8(0xbc)&0x40);
 for(let i=0;i<3;i++){const p=0xb0+i*4,x=v.getFloat32(p,true),delta=v.getFloat32(0x1084+i*4,true);v.setFloat32(p,F(i===0&&mirror?x-delta:x+delta),true);}
 if(v.getUint8(0xbe)&1)for(let i=0;i<2;i++){
  const p=0xb0+i*4,x=v.getFloat32(p,true),low=v.getFloat32(0x28+i*4,true),high=v.getFloat32(0x30+i*4,true);
  if(low>x)v.setFloat32(p,low,true);else if(x>high)v.setFloat32(p,high,true);
 }
}
