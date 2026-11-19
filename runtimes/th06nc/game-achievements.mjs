// Local browser replacement for the native platform award/StoreStats boundary.
// Producer conditions remain in the native-derived scene/gameplay modules.
const valid=key=>typeof key==='string'&&/^Achievement(0[1-9]|1[0-9]|2[0-4])$/.test(key);
export class GameAchievements {
 constructor(db){this.db=db;this.unlocked=new Set();this.pending=new Set();this.queue=Promise.resolve();this.error=null;this.commits=0;}
 async open(){
  const tx=this.db.transaction('config','readonly'),request=tx.objectStore('config').get('achievements');
  await this.complete(tx);
  for(const key of Array.isArray(request.result)?request.result:[])if(valid(key))this.unlocked.add(key);
 }
 award(key){if(!valid(key))throw Error('TH06nc achievement: invalid key');if(!this.unlocked.has(key))this.pending.add(key);}
 complete(tx){return new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onabort=()=>reject(tx.error??Error('TH06nc achievement: transaction aborted'));tx.onerror=()=>reject(tx.error??Error('TH06nc achievement: transaction failed'));});}
 commit(){
  const requested=[...this.pending];
  const operation=this.queue.then(async()=>{
   if(!requested.length)return;
   const tx=this.db.transaction('config','readwrite'),store=tx.objectStore('config'),read=store.get('achievements');
   let merged;
   read.onsuccess=()=>{
    merged=new Set((Array.isArray(read.result)?read.result:[]).filter(valid));
    for(const key of requested)merged.add(key);
    store.put([...merged].sort(),'achievements');
   };
   try{await this.complete(tx);this.unlocked=merged;for(const key of requested)this.pending.delete(key);this.error=null;this.commits++;}
   catch(reason){this.error=String(reason?.message??reason);throw reason;}
  });
  this.queue=operation.catch(()=>{});
  return operation;
 }
 report(){return {backend:'local-indexedDB',unlocked:[...this.unlocked].sort(),pending:[...this.pending].sort(),commits:this.commits,error:this.error};}
}
