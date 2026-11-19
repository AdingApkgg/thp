import{InteractivePersistentCpuSessionV83}from'./InteractivePersistentCpuSessionV83.mjs';
export class InteractivePersistentCpuSessionV84 extends InteractivePersistentCpuSessionV83 {
 keyboardBytes(){const bytes=super.keyboardBytes();for(const key of this.keys)if(/^Key[A-Z]$/.test(key))bytes[key.charCodeAt(3)]=0x80;return bytes;}
 stateSnapshot(){const state=super.stateSnapshot(),c=this.runtime;state.nickname=Array.from({length:19},(_,i)=>c.campaign_nickname_diagnostic(i)>>>0);state.nicknameUnlocked=Array.from(new Uint8Array(c.memory.buffer,c.campaign_nickname_unlocked(),70));state.nicknameTexts=Array.from({length:c.campaign_nickname_text_count()},(_,i)=>{const p=c.campaign_nickname_text_data(i),bytes=new Uint8Array(c.memory.buffer,p,256),n=bytes.indexOf(0);return new TextDecoder('shift-jis').decode(bytes.subarray(0,n));}).slice(-8);return state;}
}
