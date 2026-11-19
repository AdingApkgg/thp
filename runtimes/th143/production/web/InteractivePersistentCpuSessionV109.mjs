import{InteractivePersistentCpuSessionV107}from'./InteractivePersistentCpuSessionV107.mjs';
export class InteractivePersistentCpuSessionV109 extends InteractivePersistentCpuSessionV107{
 retireConsumedStorage(){if(this.cpuReadyForClose&&this.runtime.campaign_storage_fence()!==1)throw Error('Retired resource still referenced; fence '+this.runtime.campaign_storage_diagnostic(11));}
 async step(){const result=await super.step();this.retireConsumedStorage();return result;}
 closeForPage(){try{return super.closeForPage();}finally{this.retireConsumedStorage();}}
 stateSnapshot(){const s=super.stateSnapshot();s.storage=Array.from({length:13},(_,i)=>this.runtime.campaign_storage_diagnostic(i)>>>0);return s;}
}
