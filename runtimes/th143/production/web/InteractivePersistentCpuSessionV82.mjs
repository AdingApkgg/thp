import{InteractivePersistentCpuSessionV80}from'./InteractivePersistentCpuSessionV80.mjs';
export class InteractivePersistentCpuSessionV82 extends InteractivePersistentCpuSessionV80 {
 collectPersistence(){
  super.collectPersistence();const c=this.runtime,generation=c.campaign_config_generation();
  if(this.configurationGeneration!==undefined&&generation!==this.configurationGeneration){const n=c.campaign_config_written_bytes();if(n){const changes=new Map([['th143.cfg',this.bytes(c.campaign_config_written(),n).slice()]]),frame=this.frames;this.persistencePending=this.persistencePending.then(async()=>{const files=await this.fileStore.write(changes);this.persistenceLog.push({frame,files,configurationGeneration:generation});}).catch(error=>{this.persistenceError=error;});}}
  this.configurationGeneration=generation;
 }
 async step(){
  if(this.phase==='closed')return this.frames-1;const result=await super.step(),c=this.runtime,p=c.boot_region(0x4e47d0,0xa34),desired=new DataView(c.memory.buffer).getUint32(p+0x6ec,true);
  if(desired===3){if(c.campaign_quit_finish()!==1)throw Error('Main Quit failed at '+c.campaign_quit_diagnostic(0).toString(16));this.phase='closed';await this.flushPersistence();}return result;
 }
 stateSnapshot(){const state=super.stateSnapshot();state.quit=Array.from({length:11},(_,i)=>this.runtime.campaign_quit_diagnostic(i)>>>0);state.configurationGeneration=this.runtime.campaign_config_generation();return state;}
}
