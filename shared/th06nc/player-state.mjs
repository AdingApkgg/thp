import {initializePlayer} from './player-init.mjs';
import {movePlayer} from './player-movement.mjs';
import {advancePlayerLife} from './player-life.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {tickPlayer} from './player-update.mjs';
// Raw owner plus the plain player interface used by actual collision helpers.
export class PlayerState {
 constructor({anmBank,environment={},character,shot,skipIntro}={}){this.bytes=new Uint8Array(0xa2b8);this.v=new DataView(this.bytes.buffer);this.environment=environment;this.anmBank=anmBank;this.anms=initializePlayer(this.bytes,{anmBank,environment,character,shot,skipIntro});}
 get position(){return [0,1,2].map(k=>this.v.getFloat32(0x7730+k*4,true));}
 set position(position){position.forEach((x,k)=>this.v.setFloat32(0x7730+k*4,x,true));}
 get hitRadius(){return this.v.getFloat32(0x774c,true);}set hitRadius(x){this.v.setFloat32(0x774c,x,true);}
 get state(){return this.v.getUint8(0x7898);}set state(x){this.v.setUint8(0x7898,x);}
 get deathBombFrames(){return this.v.getInt32(0x773c,true);}set deathBombFrames(x){this.v.setInt32(0x773c,x,true);}
 timer(offset,value){if(value){this.v.setInt32(offset,value.previous,true);this.v.setInt32(offset+4,value.frame,true);}return {previous:this.v.getInt32(offset,true),frame:this.v.getInt32(offset+4,true)};}
 get hitTimer(){return this.timer(0x7854);}set hitTimer(x){this.timer(0x7854,x);}
 get hitAnimationTimers(){return [this.timer(0x79e8),this.timer(0x79f0)];}set hitAnimationTimers(x){this.timer(0x79e8,x[0]);this.timer(0x79f0,x[1]);}
 move(input,options={}){return movePlayer(this.bytes,input,{anmBank:this.anmBank,anms:this.anms,environment:this.environment,...options});}
 advanceLife(services={}){return advancePlayerLife(this.bytes,{environment:this.environment,resetMainAnimation:id=>this.anms.set(0x78c8,rebindAnm(this.anmBank,id,this.bytes.subarray(0x78c8,0x79e8),{randomU16:this.environment.rng?()=>this.environment.rng.next16():null})),...services});}
 tick(input,services={}){return tickPlayer(this,input,services);}
}
