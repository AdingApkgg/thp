const validName=name=>/^replay\/th143_(?:[0-9]{2}|ud[^/\\\x00]{4})\.rpy$/.test(name)||name==='scoreth143.dat'||name==='th143.cfg'||/^savedata\/sc(?:0[1-9]|10)_(?:0[1-9]|10)\.dat$/.test(name);
const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
// Store complete closed files in one transaction; resolve after commit, so a
// following reload can rely on the bytes having reached IndexedDB.
export class BinaryGameFileStoreV2{
 constructor(){this.database=null;}
 async open(){
  this.database=await new Promise((resolve,reject)=>{const request=indexedDB.open('th143-v100a-0162924204a6-files',1);request.onupgradeneeded=()=>request.result.createObjectStore('files',{keyPath:'name'});request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);request.onblocked=()=>reject(Error('Game file database upgrade blocked'));});
  this.database.onversionchange=()=>this.close();return this;
 }
 async readAll(){
  if(!this.database)throw Error('Game file database is closed');
  const rows=await new Promise((resolve,reject)=>{const tx=this.database.transaction('files','readonly'),request=tx.objectStore('files').getAll();let result;request.onsuccess=()=>{result=request.result;};tx.oncomplete=()=>resolve(result);tx.onabort=()=>reject(tx.error||Error('Game file read aborted'));tx.onerror=()=>{};});
  const files=new Map;for(const row of rows){if(!validName(row.name)||row.version!==1||!(row.bytes instanceof ArrayBuffer)||row.bytes.byteLength>0x4000000)throw Error('Invalid saved game file record');const bytes=new Uint8Array(row.bytes);if(await digest(bytes)!==row.sha256)throw Error('Saved game file checksum mismatch: '+row.name);files.set(row.name,{bytes,sha256:row.sha256});}return files;
 }
 async write(files){
  if(!this.database)throw Error('Game file database is closed');const records=[];
  for(const [name,input] of files){
   if(!validName(name)||input.byteLength>0x4000000)throw Error('Invalid game file name/size');
   const bytes=new Uint8Array(input).slice();
   records.push({name,version:1,bytes:bytes.buffer});
  }
  for(const record of records)record.sha256=await digest(record.bytes);
  await new Promise((resolve,reject)=>{
   const tx=this.database.transaction('files','readwrite');
   let enqueueError;
   tx.oncomplete=()=>resolve();
   tx.onabort=()=>reject(enqueueError??tx.error??Error('Game file write aborted'));
   try{
    const store=tx.objectStore('files');
    for(const record of records)store.put(record);
   }catch(error){
    enqueueError=error;
    // A synchronous exception does not automatically abort earlier requests.
    tx.abort();
   }
  });
  return records.map(({name,sha256,bytes})=>({name,sha256,bytes:bytes.byteLength}));
 }
 close(){this.database?.close();this.database=null;}
}
