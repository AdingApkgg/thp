import {setEclCustomCallback,executeEclCustom} from './ecl-custom.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {configureEclShot} from './ecl-shot-config.mjs';
import {attachEnemyEffect} from './enemy-linked-effects.mjs';
import {configureEclLaser} from './ecl-laser-config.mjs';
import {controlEclLaser} from './ecl-laser-control.mjs';
// Single-command layer. Dispatch timing, call stack and enemy updates are separate.
export const supportedEclCommands=Object.freeze([0,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,84,87,98,100,103,104,105,106,107,108,109,111,112,113,114,115,116,117,120,122,123,127,128,129,130,131,132,133,134,135,200,201]);
export const serviceEclCommands=Object.freeze([83,85,86,88,89,90,91,92,93,94,95,96,97,99,101,102,118,119,121,124,125,126]);
export function applyEclCommand(enemy,instruction,{operands,soundSlots=[-1,-1,-1],soundDisabled=false,bossLifeDirty=false,anmBank=null,enemyAnms=null,sin=null,cos=null,atan2=null,fireBullets=null,registerBoss=null,bossState=null,advanceStageChapter=null,spawnEffect=null,linkedEffects=null,beginSpell=null,endSpell=null,dropItem=null,spawnPointItem=null,gameEnvironment=null,spawnLaser=null,laserBindings=null,signalBackground=null,writePlayerPosition=null,spawnEnemy=null,clearEnemies=null,cancelBullets=null,bulletPool=null,player=null}={}){
 const v=new DataView(enemy.buffer,enemy.byteOffset,enemy.byteLength),a=new DataView(instruction.args.buffer,instruction.args.byteOffset,instruction.args.byteLength),op=instruction.opcode;
 const u=p=>a.getUint32(p,true),i=p=>a.getInt32(p,true),f=p=>a.getFloat32(p,true),put=(p,x)=>v.setUint32(p,x,true);
 const byte=(p,mask,bits)=>v.setUint8(p,(v.getUint8(p)&mask)|bits);
 const need=()=>{if(!operands)throw Error('TH06nc ECL: command requires operand resolver');return operands;};
 const resolved=p=>need().float(f(p));
 switch(op){
  case 0:case 127:break;
  case 4:case 5:need().assign(i(0),u(4));break;
  case 6:case 7:{
   const operands=need(),span=operands.integer(u(4))>>>0,base=op===7?operands.integer(u(8)):0,rng=operands.environment.rng;
   if(span&&!rng)throw Error('TH06nc ECL: random command needs the shared RNG');
   operands.assign(i(0),((span?rng.next32()%span:0)+base)>>>0);break;
  }
  case 8:case 9:{
   const operands=need(),span=resolved(4),base=op===9?resolved(8):0,rng=operands.environment.rng;
   if(!rng)throw Error('TH06nc ECL: random command needs the shared RNG');
   const value=Math.fround(Math.fround(rng.float01()*span)+base),word=new DataView(new ArrayBuffer(4));word.setFloat32(0,value,true);operands.assign(i(0),word.getUint32(0,true));break;
  }
  case 10:case 11:case 12:need().assign(i(0),v.getUint32(0xb0+(op-10)*4,true));break;
  case 13:case 14:case 15:case 16:case 17:case 20:case 21:case 22:case 23:case 24:need().arithmetic(i(0),u(4),u(8),['add','sub','mul','div','mod'][op>=20?op-20:op-13]);break;
  case 18:case 19:{const destination=i(0),delta=op===18?1:-1,operands=need();if(!operands.increment(destination,delta,gameEnvironment??operands.environment))a.setInt32(0,(destination+delta)|0,true);else if(destination<=-10018&&destination>=-10020)writePlayerPosition?.(-10018-destination,operands.environment.playerPosition[-10018-destination]);break;}
  case 25:need().angleBetween(i(0),[u(4),u(8),u(12),u(16)],atan2??need().environment.atan2);break;
  case 26:need().normalizeAngle(i(0));break;
  case 28:{const x=resolved(0),y=resolved(4);put(0x90,x===y?0:x<y?-1:1);break;}
  case 27:{const x=need().integer(u(0)),y=need().integer(u(4));put(0x90,x===y?0:x<y?-1:1);break;}
  case 43:case 44:{
   const base=op===43?0xb0:0x1084;for(let k=0;k<3;k++)put(base+k*4,u(k*4));
   for(let k=0;k<3;k++)v.setFloat32(base+k*4,need().float(v.getFloat32(base+k*4,true)),true);
   if(op===44)byte(0xbc,0xfc,0);
   else if(v.getUint8(0xbe)&1)for(let k=0;k<2;k++){
    const p=base+k*4,x=v.getFloat32(p,true),low=v.getFloat32(0x28+k*4,true),high=v.getFloat32(0x30+k*4,true);
    if(low>x)v.setFloat32(p,low,true);else if(x>high)v.setFloat32(p,high,true);
   }
   break;
  }
  case 45:v.setFloat32(0x22c,resolved(0),true);v.setFloat32(0x3c,resolved(4),true);byte(0xbc,0xfd,1);break;
  case 46:case 47:case 48:v.setFloat32(op===46?0xc48:op===47?0x3c:0xf78,resolved(0),true);byte(0xbc,0xfd,1);break;
  case 49:case 50:{
   const F=Math.fround,rng=need().environment.rng;if(!rng)throw Error('TH06nc ECL: random direction needs RNG');let angle=F(F(rng.float01()*F(f(4)-f(0)))+f(0));
   if(op===50){
    const x=v.getFloat32(0xb0,true),y=v.getFloat32(0xb4,true),pi=F(Math.PI),half=F(Math.PI/2);
    if(F(v.getFloat32(0x28,true)+F(96))>x){if(angle>half)angle=F(pi-angle);else if(-half>angle)angle=F(-pi-angle);}
    if(x>F(v.getFloat32(0x30,true)-F(96))){if(half>angle&&angle>=0)angle=F(pi-angle);else if(angle>-half&&0>=angle)angle=F(-pi-angle);}
    if(F(v.getFloat32(0x2c,true)+F(48))>y&&0>angle)angle=F(-angle);
    if(y>F(v.getFloat32(0x34,true)-F(48))&&angle>0)angle=F(-angle);
   }
   v.setFloat32(0x22c,angle,true);break;
  }
  case 51:{
   const env=need().environment,F=Math.fround,dx=F(Math.fround(env.playerPosition[0])-v.getFloat32(0xb0,true)),dy=F(Math.fround(env.playerPosition[1])-v.getFloat32(0xb4,true));
   if((dx!==0||dy!==0)&&!atan2)throw Error('TH06nc ECL: aimed movement requires atan2 service');
   v.setFloat32(0x22c,F((dx===0&&dy===0?F(Math.PI/2):F(atan2(dy,dx)))+f(0)),true);v.setFloat32(0x3c,resolved(4),true);byte(0xbc,0xfd,1);break;
  }
  case 52:case 53:case 54:case 55:case 56:case 57:case 58:case 59:case 60:case 61:case 62:case 63:case 64:{
   const F=Math.fround,duration=i(0);let delta;
   if(op>=56&&op<=60){const target=[resolved(4),resolved(8),resolved(12)];delta=target.map((x,k)=>F(x-v.getFloat32(0xb0+k*4,true)));}
   else{
    if(!sin||!cos)throw Error('TH06nc ECL: movement tween requires sine/cosine services');
    const angle=op<=55?resolved(4):need().float(v.getFloat32(0x22c,true)),speed=op<=55?f(8):v.getFloat32(0x3c,true);
    delta=[F(F(F(F(cos(angle))*speed)*F(duration))*F(0.5)),F(F(F(F(sin(angle))*speed)*F(duration))*F(0.5)),0];
   }
   for(let k=0;k<3;k++){v.setFloat32(0x244+k*4,delta[k],true);put(0x250+k*4,v.getUint32(0xb0+k*4,true));}
   const ease=op<=55?op-51:op<=60?op-56:op-60;byte(0xbc,0xe0,2|(ease<<2));
   put(0x264,duration);put(0x260,duration);put(0x25c,-999);
   if(op>=56&&op<=60)for(const p of [0x1084,0x1088,0x108c])put(p,0);
   break;
  }
  case 65:for(let k=0;k<4;k++)put(0x28+k*4,u(k*4));byte(0xbe,255,1);break;
  case 66:byte(0xbe,254,0);break;
  case 67:case 68:case 69:case 70:case 71:case 72:case 73:case 74:case 75:case 201:configureEclShot(enemy,instruction,{operands,fireBullets});break;
  case 76:case 77:{
   const operands=need(),quotient=Math.trunc(i(0)/5),product=(Math.imul(quotient,operands.environment.rank|0)*2)|0,interval=(i(0)-Math.trunc(product/32)+quotient)|0;put(0xf68,interval);
   if(op===76){put(0x10a4,0);put(0x10a0,-999);}
   else if(interval!==0){const rng=operands.environment.rng;if(!rng)throw Error('TH06nc ECL: random fire interval requires RNG');put(0x10a4,rng.next32()%(interval>>>0));put(0x10a0,-999);}
   break;
  }
  case 78:byte(0xbc,255,0x20);break;
  case 79:byte(0xbc,0xdf,0);break;
  case 82:for(let k=0;k<4;k++)put(0x288+k*4,need().bits(u(k*4)));for(let k=0;k<4;k++)v.setFloat32(0x2ac+k*4,resolved(16+k*4),true);break;
  case 84:if(i(0)>=0){put(0x2a8,u(0));put(0x26c,v.getUint32(0x26c,true)|0x200);}else put(0x26c,v.getUint32(0x26c,true)&~0x200);break;
  case 87:put(0xbd8,need().bits(u(0)));break;
  case 83:if(!cancelBullets)throw Error('TH06nc ECL: projectile clear service missing');cancelBullets({items:true});break;
  case 85:case 86:configureEclLaser(enemy,instruction,{operands,spawnLaser,laserBindings});break;
  case 88:case 89:case 90:case 91:case 92:controlEclLaser(enemy,instruction,{operands,laserBindings,atan2:atan2??Math.atan2,gameEnvironment});break;
  case 98:for(const [k,p]of [0x109c,0x2bc,0x2be,0xf6c,0xf6e].entries())v.setUint16(p,a.getUint16(k*2,true),true);v.setUint8(0xf7c,255);break;
  case 130:byte(0xbe,0xfb,i(0)!==0?4:0);break;
  case 134:enemy.fill(0,0xf80,0x1080);break;
  case 200:{
   const F=Math.fround,radius=resolved(4),angle=resolved(0);if(!sin||!cos)throw Error('TH06nc ECL: polar origin needs sine/cosine services');
   v.setFloat32(0xc5c,F(F(cos(angle))*radius),true);v.setFloat32(0xc60,F(F(sin(angle))*radius),true);put(0xc64,0);break;
  }
  case 80:for(let k=0;k<3;k++)v.setFloat32(0x278+k*4,Math.fround(v.getFloat32(0xc5c+k*4,true)+v.getFloat32(0xb0+k*4,true)),true);if(!fireBullets)throw Error('TH06nc ECL: shot requires bullet service');fireBullets(enemy,enemy.subarray(0x26c,0x2d8));break;
  case 81:for(let k=0;k<3;k++)v.setFloat32(0xc5c+k*4,resolved(k*4),true);break;
  case 93:if(!beginSpell)throw Error('TH06nc ECL: spell start service missing');beginSpell(enemy,instruction.args);break;
  case 94:if(!endSpell)throw Error('TH06nc ECL: spell completion service missing');endSpell();break;
  case 95:if(!spawnEnemy)throw Error('TH06nc ECL: enemy spawn service missing');spawnEnemy({sub:i(0),position:[resolved(4),resolved(8),resolved(12)],life:a.getUint16(16,true),item:a.getUint16(18,true),score:i(20),context:enemy.subarray(0x40,0xa0)});break;
  case 96:if(!clearEnemies)throw Error('TH06nc ECL: enemy clear service missing');clearEnemies();break;
  case 97:case 99:{
   if(!anmBank||!enemyAnms)throw Error('TH06nc ECL: animation command requires an enemy ANM bank and bindings');
   const offset=op===97?0x108:0x2d8+i(0)*288,id=0x100+i(op===97?0:4);
   enemyAnms.set(offset,rebindAnm(anmBank,id,enemy.subarray(offset,offset+288),{randomU16:operands?.environment.rng?()=>operands.environment.rng.next16():null}));break;
  }
  case 100:for(let k=0;k<3;k++)v.setUint8(0x38+k,a.getUint8(k));break;
  case 101:if(!registerBoss)throw Error('TH06nc ECL: boss registration service missing');registerBoss(enemy,i(0));bossLifeDirty=true;break;
  case 102:attachEnemyEffect(enemy,instruction.args,{spawnEffect,linkedEffects});break;
  case 103:for(let k=0;k<3;k++)put(0x2c0+k*4,u(k*4));break;
  case 104:byte(0xbd,0xfd,u(0)!==0?2:0);break;
  case 105:byte(0xbd,0xef,u(0)!==0?16:0);break;
  case 106:if(!soundDisabled)for(let k=0;k<3;k++){if(soundSlots[k]<0){soundSlots[k]=i(0);break;}if(soundSlots[k]===i(0))break;}break;
  case 107:byte(0xbd,0x1f,(a.getUint8(0)<<5)&255);break;
  case 108:put(0xbe0,u(0));break;
  case 109:put(8+i(4)*4,u(0));break;
  case 111:for(const p of [0x234,0x238,0x23c])put(p,u(0));if(v.getUint8(0xbd)&8){bossLifeDirty=true;if(bossState)bossState.dirty=true;}break;
  case 112:put(4,u(0));put(0,-999);break;
  case 113:put(0xa0,u(0));break;
  case 114:put(0xa4,u(0));break;
  case 115:put(0xc54,u(0));put(4,0);put(0,-999);break;
  case 116:put(0xc58,u(0));break;
  case 117:byte(0xbd,254,u(0)!==0?1:0);break;
  case 118:if(!spawnEffect)throw Error('TH06nc ECL: effect service missing');spawnEffect({type:i(0),position:Array.from({length:3},(_,k)=>v.getFloat32(0xb0+k*4,true)),count:i(4),color:u(8)});break;
  case 119:{
   const count=i(0),env=gameEnvironment??need().environment,rng=need().environment.rng,F=Math.fround;
   if(count>0&&!rng)throw Error('TH06nc ECL: item scattering requires shared RNG');
   for(let k=0;k<count;k++){
    const position=Array.from({length:3},(_,j)=>v.getFloat32(0xb0+j*4,true));
    for(let j=0;j<2;j++)position[j]=F(position[j]+F(F(rng.float01()*F(144))-F(72)));
    if(((env.playerPower??0)&65535)<128){if(!dropItem)throw Error('TH06nc ECL: item service missing');dropItem({type:k===0?2:0,position,critical:false});}
    else if(!env.spellPractice){if(!spawnPointItem)throw Error('TH06nc ECL: point-item service missing');spawnPointItem({position});}
   }
   break;
  }
  case 120:byte(0xbe,253,u(0)!==0?2:0);break;
  case 121:executeEclCustom(enemy,instruction,{anmBank,enemyAnms,player,spawnLaser,linkedEffects,soundSlots,soundDisabled,bulletPool,laserBindings,spawnEffect,fireBullets,environment:gameEnvironment??need().environment,sin:sin??Math.sin,cos:cos??Math.cos,atan2:atan2??Math.atan2});break;
  case 122:setEclCustomCallback(enemy,i(0));break;
  case 123:put(0x44,(v.getInt32(0x44,true)+need().integer(u(0)))|0);break;
  case 124:if(!dropItem)throw Error('TH06nc ECL: item service missing');dropItem({type:a.getUint16(0,true),position:Array.from({length:3},(_,k)=>v.getFloat32(0xb0+k*4,true)),critical:false});break;
  case 125:if(!signalBackground)throw Error('TH06nc ECL: background signal service missing');signalBackground();break;
  case 126:if(!advanceStageChapter)throw Error('TH06nc ECL: stage chapter service missing');advanceStageChapter(i(0));break;
  case 128:v.setUint16(0x192,a.getUint16(0,true),true);break;
  case 129:v.setUint16(0x362+i(0)*288,a.getUint16(4,true),true);break;
  case 131:put(0xa8,u(0));put(0xac,u(4));for(const [p,q]of [[0xbdc,8],[0xbde,12],[0x1080,16],[0x1082,20]])v.setUint16(p,a.getUint16(q,true),true);break;
  case 132:byte(0xbe,247,u(0)!==0?8:0);break;
  case 133:put(0xc58,v.getUint32(0xbe0,true));put(4,0);put(0,-999);break;
  case 135:byte(0xbe,239,u(0)!==0?16:0);break;
  default:throw Error(`TH06nc ECL: opcode ${op} not implemented`);
 }
 return {soundSlots,bossLifeDirty};
}
