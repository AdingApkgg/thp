const F=Math.fround,STEP=F(.7853981852531433),TAU=F(2*Math.PI);
// Entry 7, original 34350: two eight-point rings, three successive layers.
// Point and angle updates are sequential float32 operations, including the
// accumulated full turns between layers; reducing angles changes the result.
export function fireLayeredRings(enemy,instruction,{environment,spawnLaser,fireBullets,sin=Math.sin,cos=Math.cos}={}){
 if(!environment?.rng)throw Error('TH06nc ECL: ring RNG missing');
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),mode=a.getInt32(4,true),hard=environment.difficulty>1,random=F(environment.rng.float01()*TAU),starts=[F(random-F(Math.PI)),F(random-F(2.7488937377929688))],position=Array.from({length:3},(_,i)=>v.getFloat32(0xb0+i*4,true));
 if(mode===0&&!spawnLaser||mode!==0&&!fireBullets)throw Error('TH06nc ECL: ring projectile service missing');
 for(let group=0;group<2;group++){
  let angle=starts[group];const points=[];
  for(let i=0;i<8;i++){points.push([F(position[0]+F(F(cos(angle))*F(32))),F(position[1]+F(F(sin(angle))*F(32))),position[2]]);if(i<7)angle=F(angle+STEP);}
  angle=starts[group];const turn=F((group===0?STEP:-STEP)-TAU);
  for(let layer=0;layer<3;layer++){
   const distance=F(layer<2?112:480);
   for(const point of points){
    if(mode===0){
     const descriptor=new Uint8Array(0x44),d=new DataView(descriptor.buffer);d.setInt32(0,50,true);d.setInt32(4,16,true);d.setInt16(0xc,1,true);d.setInt16(0xe,hard?8:2,true);d.setFloat32(0x10,hard?20:28,true);d.setInt16(0x14,2,true);d.setFloat32(0x1c,hard?440:distance,true);point.forEach((n,i)=>d.setFloat32(0x20+i*4,n,true));d.setUint8(0x2c,1);d.setInt32(0x30,60+layer*16,true);d.setInt32(0x34,90-layer*16,true);d.setInt32(0x38,16,true);d.setFloat32(0x3c,angle,true);d.setFloat32(0x40,hard?440:distance,true);spawnLaser(descriptor);
    }else{point.forEach((n,i)=>v.setFloat32(0x278+i*4,n,true));fireBullets(enemy,enemy.subarray(0x26c,0x2d8));}
    point[0]=F(point[0]+F(F(cos(angle))*distance));point[1]=F(point[1]+F(F(sin(angle))*distance));angle=F(angle+STEP);
   }
   angle=F(angle+turn);
  }
 }
}
