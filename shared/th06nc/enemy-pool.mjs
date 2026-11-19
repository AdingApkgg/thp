import {executeEclCustomCallback} from './ecl-custom.mjs';
import {EclOperands} from './ecl-operands.mjs';
import {EclDispatch} from './ecl-dispatch.mjs';
import {tickEclEnemy} from './ecl-tick.mjs';
export const enemyBytes=0x10b0;
// Template constructor 35f50 and ordinary spawn helper 360d0.
export function createEnemyTemplate(){
 const bytes=new Uint8Array(enemyBytes),v=new DataView(bytes.buffer);
 for(const [p,value]of [[0,-999],[0xa0,-1],[0xa8,0xbf000000],[0xac,0x3f000000],[0xbc,0x1380],[0x234,1],[0x23c,1],[0x2c0,0x41400000],[0x2c4,0x41400000],[0x2c8,0x41400000],[0xbe0,-1],[0xc50,100],[0xc54,-1],[0xf6c,-1],[0xf70,-1],[0x109c,65535],[0x10a0,-999]])v.setUint32(p,value,true);
 for(let i=0;i<8;i++)v.setUint16(0x310+i*288,65535,true);return bytes;
}
export class EnemyPool {
 constructor(program,{anmBank,environment={},...services}={}){
  this.program=program;this.anmBank=anmBank;this.environment=environment;this.services=services;this.template=createEnemyTemplate();this.storage=new Uint8Array(256*enemyBytes);this.entries=new Array(256);
 }
 spawn({sub,position,life=-1,item=-1,score=-1,context=null}){
  let slot=0;while(slot<256&&(this.storage[slot*enemyBytes+0xbc]&128))slot++;
  if(slot===256)throw Error('TH06nc: enemy pool capacity exceeded');
  const enemy=this.storage.subarray(slot*enemyBytes,(slot+1)*enemyBytes);enemy.set(this.template);const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength);
  life=(life<<16)>>16;if(life>=0)v.setInt32(0x234,life,true);
  for(let i=0;i<3;i++)v.setFloat32(0xb0+i*4,position[i],true);
  if(context){if(context.byteLength<64)throw Error('TH06nc: truncated spawn context');enemy.set(context.subarray(8,64),0x48);}
  const operands=new EclOperands(enemy,this.environment),enemyAnms=new Map(),linkedEffects=new Map(),laserBindings=new Map(),services={...this.services,operands,anmBank:this.anmBank,enemyAnms,linkedEffects,laserBindings,gameEnvironment:this.environment},dispatch=new EclDispatch(this.program,enemy,services);
  services.enemyCallback??=enemy=>executeEclCustomCallback(enemy,{...services,environment:this.environment});
  dispatch.start((sub<<16)>>16,{integer:v.getInt32(0x48,true),floatBits:v.getUint32(0x58,true)});
  const initialUpdate=tickEclEnemy(dispatch);
  v.setUint32(0xf74,v.getUint32(0x1f4,true),true);v.setUint8(0x10a8,item&255);if(life>=0)v.setInt32(0x234,life,true);if((score|0)>=0)v.setInt32(0xc50,score|0,true);
  v.setInt32(0x238,v.getInt32(0x234,true),true);v.setInt32(0x23c,v.getInt32(0x234,true),true);
  const entry={slot,enemy,v,operands,enemyAnms,linkedEffects,laserBindings,dispatch,initialUpdate,pool:this};this.entries[slot]=entry;return entry;
 }
}
