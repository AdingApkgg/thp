const F=Math.fround;
// ECL 67..75/201, 25371..25d78. Emission is supplied by the bullet manager.
export function configureEclShot(enemy,instruction,{operands,fireBullets=null}={}){
 if(!operands)throw Error('TH06nc ECL: shot configuration requires operands');
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),base=0x26c,rank=operands.environment.rank|0;
 v.setUint16(base+0x2c,a.getUint16(0,true),true);v.setUint16(base+0x30,instruction.opcode-67,true);
 for(const [arg,field,low,high]of [[4,0x18,0xbdc,0xbde],[8,0x1a,0x1080,0x1082]]){
  const raw=operands.integer(a.getUint32(arg,true))&65535,start=v.getInt16(low,true),end=v.getInt16(high,true),adjust=(Math.trunc(Math.imul(end-start,rank)/32)+start)|0;
  v.setInt16(base+field,raw+adjust,true);if(v.getInt16(base+field,true)<=0)v.setInt16(base+field,1,true);
 }
 for(let k=0;k<3;k++)v.setFloat32(base+12+k*4,F(v.getFloat32(0xc5c+k*4,true)+v.getFloat32(0xb0+k*4,true)),true);
 let angle=operands.float(a.getFloat32(20,true));
 if(instruction.opcode===201)v.setUint16(base+0x30,8,true);
 else{
  angle=F(angle+0);let count=0;
  while(angle>F(Math.PI)){angle=F(angle+F(-2*Math.PI));if(count++>16)break;}
  while(F(-Math.PI)>angle){angle=F(angle+F(2*Math.PI));if(count++>16)break;}
 }
 v.setFloat32(base+0x34,angle,true);
 const adjustment=()=>F(F(F(F(v.getFloat32(0xac,true)-v.getFloat32(0xa8,true))*F(rank))*F(1/32))+v.getFloat32(0xa8,true));
 let speed=operands.float(a.getFloat32(12,true));
 if(speed!==0){speed=F(adjustment()+speed);if(speed<F(0.3))speed=F(0.3);}v.setFloat32(base+4,speed,true);
 v.setFloat32(base+0x38,operands.float(a.getFloat32(24,true)),true);
 speed=operands.float(a.getFloat32(16,true));speed=F(F(adjustment()*F(0.5))+speed);if(speed<F(0.3))speed=F(0.3);v.setFloat32(base+8,speed,true);
 v.setUint32(base,a.getUint32(28,true),true);v.setUint16(base+0x2e,operands.integer(a.getInt16(2,true)),true);
 if(!(v.getUint8(0xbc)&0x20)){if(!fireBullets)throw Error('TH06nc ECL: shot configuration requires the bullet service');fireBullets(enemy,enemy.subarray(base,base+108));}
}
