const F=Math.fround;
// Table entry 12, original 351b0: one ordinary shot per active saved laser in
// the first eight slots. Keep its sequential (nonstandard) rotation arithmetic.
export function fireFromSavedLasers(enemy,{laserBindings,fireBullets,sin=Math.sin,cos=Math.cos}={}){
 if(!fireBullets)throw Error('TH06nc ECL: custom laser shot service missing');const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);
 for(let i=0;i<8;i++){const pointer=v.getBigUint64(0xf80+i*8,true);if(!pointer)continue;const laser=laserBindings?.get(pointer);if(!laser)throw Error('TH06nc ECL: custom saved laser state missing');if(!laser.v.getUint8(0x274))continue;v.setBigUint64(0x278,0x42800000n,true);v.setUint32(0x280,0,true);const angle=laser.v.getFloat32(0x260,true),s=F(sin(angle)),c=F(cos(angle)),y=v.getFloat32(0x27c,true),x=F(F(y*s)+F(c*v.getFloat32(0x278,true))),rotatedY=F(F(y*c)-F(x*s));v.setFloat32(0x278,F(x+v.getFloat32(0xb0,true)),true);v.setFloat32(0x27c,F(rotatedY+v.getFloat32(0xb4,true)),true);v.setFloat32(0x280,F(v.getFloat32(0xb8,true)+v.getFloat32(0x280,true)),true);fireBullets(enemy,enemy.subarray(0x26c,0x2d8));}
}
