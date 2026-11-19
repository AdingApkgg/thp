const F=Math.fround;
// Saved laser operations 88..92, native 26f52..270e9.
export function controlEclLaser(enemy,instruction,{operands,laserBindings,atan2=Math.atan2,gameEnvironment=null}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),index=a.getInt32(0,true),op=instruction.opcode;
 if(index<0||index>=32)throw Error('TH06nc: invalid saved laser index');const pointer=v.getBigUint64(0xf80+index*8,true);let laser=null;
 if(pointer){laser=laserBindings?.get(pointer);if(!laser)throw Error('TH06nc: saved laser state missing');}
 if(op===91){v.setInt32(0x90,laser?.v.getUint8(0x274)?0:1,true);return;}
 if(!laser)return;const l=laser.v;
 if(op===88){if(!operands)throw Error('TH06nc: laser control operand service missing');l.setFloat32(0x260,F(l.getFloat32(0x260,true)+operands.float(a.getFloat32(4,true))),true);}
 else if(op===89){
  if(!operands)throw Error('TH06nc: laser aiming operand service missing');const player=(gameEnvironment??operands.environment).playerPosition,dx=F(F(player[0])-l.getFloat32(0x278,true)),dy=F(F(player[1])-l.getFloat32(0x27c,true)),angle=dx===0&&dy===0?F(Math.PI/2):F(atan2(dy,dx));
  l.setFloat32(0x260,F(angle+operands.float(a.getFloat32(4,true))),true);
 }else if(op===90){for(let i=0;i<3;i++)l.setFloat32(0x278+i*4,F(a.getFloat32(4+i*4,true)+v.getFloat32(0xb0+i*4,true)),true);}
 else if(op===92&&l.getUint8(0x274)&&l.getUint8(0x290)<2){l.setUint8(0x290,2);l.setInt32(0xc,0,true);l.setInt32(8,-999,true);}
 else if(op!==92)throw Error('TH06nc: unknown laser control operation');
}
