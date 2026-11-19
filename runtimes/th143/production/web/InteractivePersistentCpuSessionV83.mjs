import{InteractivePersistentCpuSessionV82}from'./InteractivePersistentCpuSessionV82.mjs';
export class InteractivePersistentCpuSessionV83 extends InteractivePersistentCpuSessionV82 {
 keyboardBytes(){const bytes=super.keyboardBytes(),keys={F10:0x79,KeyR:0x52,KeyD:0x44,Home:0x24,KeyP:0x50,KeyS:0x53,KeyQ:0x51,KeyC:0x43};for(let i=0;i<10;++i)keys['Numpad'+i]=0x60+i;for(const key of this.keys)if(key in keys)bytes[keys[key]]=0x80;return bytes;}
 stateSnapshot(){const state=super.stateSnapshot();state.input=Array.from({length:8},(_,i)=>this.runtime.campaign_input_diagnostic(i)>>>0);return state;}
}
