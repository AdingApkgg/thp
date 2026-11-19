import{InteractivePersistentCpuSessionV79}from'./InteractivePersistentCpuSessionV79.mjs';
export class InteractivePersistentCpuSessionV80 extends InteractivePersistentCpuSessionV79 {
 async initialize(progress=()=>{}){await super.initialize(progress);this.padBuffer=this.runtime.allocate(128);}
 capturePad(){
  const c=this.runtime,bytes=new Uint8Array(128),pad=Array.from(navigator.getGamepads?.()||[]).find(p=>p?.connected);
  if(pad)for(let i=0;i<Math.min(128,pad.buttons.length);++i)if(pad.buttons[i]?.pressed||pad.buttons[i]?.value>.5)bytes[i]=0x80;
  this.bytes(this.padBuffer,128).set(bytes);const axis=i=>Math.round((Math.max(-1,Math.min(1,pad?.axes[i]||0))+1)*32767.5);let pov=65535;
  if(pad?.mapping==='standard'){const up=bytes[12]!==0,down=bytes[13]!==0,left=bytes[14]!==0,right=bytes[15]!==0;if(up||down||left||right){const angle=Math.atan2((right?1:0)-(left?1:0),(up?1:0)-(down?1:0));pov=Math.round((angle<0?angle+2*Math.PI:angle)*18000/Math.PI)%36000;}}
  if(c.campaign_pad_input(this.padBuffer,128,pad?1:0,axis(0),axis(1),pov)!==1)throw Error('Gamepad input packet rejected');
 }
 async step(){this.capturePad();return super.step();}
 stateSnapshot(){const state=super.stateSnapshot();state.pad=Array.from({length:26},(_,i)=>this.runtime.campaign_pad_diagnostic(i)>>>0);return state;}
}
