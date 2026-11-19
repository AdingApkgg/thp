const KEY='th143.exit-journal.v2',FILE_LIMIT=1024*1024,TOTAL_LIMIT=1500000;
const allowed=name=>typeof name==='string'&&(name==='th143.cfg'||name==='scoreth143.dat'||/^replay\/th143_(?:0[1-9]|1[0-9]|2[0-5])\.rpy$/.test(name)||/^savedata\/sc(?:0[1-9]|10)_[0-9]{2}\.dat$/.test(name));
const encode=b=>{let s='';for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s);};
const checksum=b=>{let h=2166136261;for(const v of b)h=Math.imul(h^v,16777619);return(h>>>0).toString(16).padStart(8,'0');};
export function sameExitBytesV2(a,b){if(!a||a.length!==b.length)return false;for(let i=0;i<a.length;i++)if(a[i]!==b[i])return false;return true;}
export function writeExitJournalV2(files,storage=localStorage){
 if(files.size>102)throw Error('Too many exit journal files');const rows=[];let total=0;for(const[name,bytes]of files){if(!allowed(name)||!(bytes instanceof Uint8Array)||bytes.length<1||bytes.length>FILE_LIMIT||name==='th143.cfg'&&bytes.length!==92)throw Error('Invalid exit journal file');total+=bytes.length;if(total>TOTAL_LIMIT)throw Error('Exit journal exceeds synchronous storage budget');rows.push({name,bytes:bytes.length,checksum:checksum(bytes),data:encode(bytes)});}
 const raw=JSON.stringify({version:2,title:'th143-1.00a',files:rows});storage.setItem(KEY,raw);return raw;
}
export function clearExitJournalV2(raw,storage=localStorage){if(storage.getItem(KEY)===raw)storage.removeItem(KEY);}
export async function recoverExitJournalV2(store,storage=localStorage){
 const raw=storage.getItem(KEY);if(raw===null)return{recovered:false,files:[]};if(raw.length>TOTAL_LIMIT*1.4+20000)throw Error('Exit journal is too large');const record=JSON.parse(raw);if(record.version!==2||record.title!=='th143-1.00a'||!Array.isArray(record.files)||record.files.length>102)throw Error('Invalid exit journal');const files=new Map;let total=0;
 for(const row of record.files){if(!allowed(row.name)||files.has(row.name)||!Number.isInteger(row.bytes)||row.bytes<1||row.bytes>FILE_LIMIT||typeof row.data!=='string'||row.data.length>Math.ceil(FILE_LIMIT/3)*4)throw Error('Invalid exit journal entry');total+=row.bytes;if(total>TOTAL_LIMIT)throw Error('Exit journal exceeds synchronous storage budget');const bytes=Uint8Array.from(atob(row.data),c=>c.charCodeAt(0));if(bytes.length!==row.bytes||checksum(bytes)!==row.checksum||row.name==='th143.cfg'&&bytes.length!==92)throw Error('Exit journal checksum changed');files.set(row.name,bytes);}
 const restored=await store.write(files);clearExitJournalV2(raw,storage);return{recovered:true,files:restored};
}
