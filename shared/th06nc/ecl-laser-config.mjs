// ECL laser configuration 26aa4..26bd5, followed by helper 105e0.
export function configureEclLaser(enemy,instruction,{operands,spawnLaser,laserBindings}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),F=Math.fround;
 if(!operands||!spawnLaser||!laserBindings)throw Error('TH06nc: laser command services missing');
 for(let i=0;i<3;i++)v.setFloat32(0xe0+i*4,F(v.getFloat32(0xc5c+i*4,true)+v.getFloat32(0xb0+i*4,true)),true);
 v.setUint16(0xcc,a.getUint16(0,true),true);v.setUint16(0xce,a.getUint16(2,true),true);
 for(const [target,source]of [[0xfc,4],[0xc8,8],[0xd8,12],[0xdc,16],[0x100,20]])v.setFloat32(target,operands.float(a.getFloat32(source,true)),true);
 for(const [target,source]of [[0xd0,24],[0xf0,28],[0xf4,32],[0xf8,36],[0xc0,40],[0xc4,44],[0xd4,48]])v.setUint32(target,a.getUint32(source,true),true);
 v.setUint8(0xec,instruction.opcode===86?0:1);const laser=spawnLaser(enemy.subarray(0xc0,0x104)),index=v.getInt32(0xbd8,true);
 if(index<0||index>=32)throw Error('TH06nc: invalid saved laser index');
 v.setBigUint64(0xf80+index*8,laser?.pointer??0n,true);if(laser)laserBindings.set(laser.pointer,laser);return laser;
}
