import{InteractivePersistentCpuSessionV99}from'./InteractivePersistentCpuSessionV99.mjs';
import{BinaryGameFileStoreV2}from'./BinaryGameFileStoreV2.mjs';
import{recoverExitJournalV1}from'./WindowExitJournalV1.mjs';
import{writeExitJournalV2,clearExitJournalV2,recoverExitJournalV2,sameExitBytesV2}from'./WindowExitJournalV2.mjs';
export class InteractivePersistentCpuSessionV101 extends InteractivePersistentCpuSessionV99 {
 async initialize(progress=()=>{}){
  const store=await new BinaryGameFileStoreV2().open();let legacy,current;try{legacy=await recoverExitJournalV1(store);current=await recoverExitJournalV2(store);}finally{store.close();}
  await super.initialize(progress);this.exitJournalRecovery=current.recovered?current:legacy;this.durableExitFiles=new Map(Array.from(await this.fileStore.readAll(),([name,file])=>[name,file.bytes]));const write=this.fileStore.write.bind(this.fileStore);this.fileStore.write=async changes=>{const copy=new Map(Array.from(changes,([name,bytes])=>[name,bytes.slice()])),result=await write(copy);for(const[name,bytes]of copy)this.durableExitFiles.set(name,bytes);return result;};
 }
 closeForPage(){
  const c=this.runtime;if(!c||!['title','game','closed'].includes(this.phase))return false;
  try{if(this.phase!=='closed'){this.keys.clear();if(c.campaign_window_close_request()!==1||c.campaign_window_close_finish()!==1)throw Error('Window close failed at '+c.campaign_window_close_diagnostic(0).toString(16));this.phase='closed';}
   const files=new Map,n=c.campaign_config_written_bytes(),score=c.campaign_score_file_bytes();if(n)files.set('th143.cfg',this.bytes(c.campaign_config_written(),n).slice());if(score)files.set('scoreth143.dat',this.bytes(c.campaign_score_file_data(),score).slice());
   const string=p=>{const b=new Uint8Array(c.memory.buffer),text=[];for(let i=0;i<256;i++){const v=b[p+i];if(!v)return new TextDecoder().decode(Uint8Array.from(text));text.push(v);}throw Error('Exit file name is not terminated');};
   const pending=(name,p,n)=>{const bytes=this.bytes(p,n);if(!sameExitBytesV2(this.durableExitFiles?.get(name),bytes))files.set(name,bytes.slice());};
   for(let i=0;i<c.campaign_replay_written_count();i++)pending(string(c.campaign_replay_written_name(i)),c.campaign_replay_written_data(i),c.campaign_replay_written_bytes(i));
   for(let i=0;i<c.campaign_preview_file_count();i++)pending(string(c.campaign_preview_file_name(i)),c.campaign_preview_file_data(i),c.campaign_preview_file_bytes(i));
   this.lastExitJournalFiles=Array.from(files,([name,b])=>({name,bytes:b.length}));let journal;try{journal=writeExitJournalV2(files);this.exitJournalWritten=true;}finally{this.exitFlush=this.flushPersistence().then(()=>{if(journal)clearExitJournalV2(journal);}).catch(error=>{this.persistenceError=error;});}return true;
  }finally{this.disposeForExit();}
 }
 stateSnapshot(){const s=super.stateSnapshot();s.exitJournalVersion=2;s.exitJournalFiles=this.lastExitJournalFiles||[];return s;}
}
