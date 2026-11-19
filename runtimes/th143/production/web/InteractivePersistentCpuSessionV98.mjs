import{InteractivePersistentCpuSessionV96}from'./InteractivePersistentCpuSessionV96.mjs';
import{BinaryGameFileStoreV2}from'./BinaryGameFileStoreV2.mjs';
import{writeExitJournalV1,clearExitJournalV1,recoverExitJournalV1}from'./WindowExitJournalV1.mjs';
export class InteractivePersistentCpuSessionV98 extends InteractivePersistentCpuSessionV96 {
 async initialize(progress=()=>{}){const store=await new BinaryGameFileStoreV2().open();try{this.exitJournalRecovery=await recoverExitJournalV1(store);}finally{store.close();}return super.initialize(progress);}
 closeForPage(){
  const c=this.runtime;if(!c||this.phase==='loading')return false;
  if(this.phase!=='closed'){this.keys.clear();if(c.campaign_window_close_request()!==1||c.campaign_window_close_finish()!==1)throw Error('Window close failed at '+c.campaign_window_close_diagnostic(0).toString(16));this.phase='closed';}
  const files=new Map,n=c.campaign_config_written_bytes(),score=c.campaign_score_file_bytes();if(n)files.set('th143.cfg',this.bytes(c.campaign_config_written(),n).slice());if(score)files.set('scoreth143.dat',this.bytes(c.campaign_score_file_data(),score).slice());let journal;try{journal=writeExitJournalV1(files);this.exitJournalWritten=true;}finally{this.exitFlush=this.flushPersistence().then(()=>{if(journal)clearExitJournalV1(journal);}).catch(error=>{this.persistenceError=error;});}return true;
 }
 stateSnapshot(){const s=super.stateSnapshot(),c=this.runtime;s.windowClose=Array.from({length:10},(_,i)=>c.campaign_window_close_diagnostic(i)>>>0);s.exitJournalRecovery=this.exitJournalRecovery;s.exitJournalWritten=!!this.exitJournalWritten;return s;}
}
