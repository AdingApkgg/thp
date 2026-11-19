const KEY='th143.exit-journal.v1',LIMIT=1024*1024;
const encode=b=>{let s='';for(let i=0;i<b.length;i+=16384)s+=String.fromCharCode(...b.subarray(i,i+16384));return btoa(s);};
const checksum=b=>{let h=2166136261;for(const v of b)h=Math.imul(h^v,16777619);return(h>>>0).toString(16).padStart(8,'0');};
export function writeExitJournalV1(files,storage=localStorage){
 const rows=[];for(const[name,bytes]of files){if(name!=='th143.cfg'&&name!=='scoreth143.dat')throw Error('Unexpected exit journal file');if(!(bytes instanceof Uint8Array)||bytes.length>LIMIT||name==='th143.cfg'&&bytes.length!==92)throw Error('Invalid exit journal file');rows.push({name,bytes:bytes.length,checksum:checksum(bytes),data:encode(bytes)});}
 const raw=JSON.stringify({version:1,title:'th143-1.00a',files:rows});storage.setItem(KEY,raw);return raw;
}
export function clearExitJournalV1(raw,storage=localStorage){if(storage.getItem(KEY)===raw)storage.removeItem(KEY);}
export async function recoverExitJournalV1(store,storage=localStorage){
 const raw=storage.getItem(KEY);if(raw===null)return{recovered:false,files:[]};if(raw.length>LIMIT*3)throw Error('Exit journal is too large');const record=JSON.parse(raw);if(record.version!==1||record.title!=='th143-1.00a'||!Array.isArray(record.files)||record.files.length>2)throw Error('Invalid exit journal');const files=new Map;
 for(const row of record.files){if(row.name!=='th143.cfg'&&row.name!=='scoreth143.dat'||files.has(row.name)||!Number.isInteger(row.bytes)||row.bytes<1||row.bytes>LIMIT||typeof row.data!=='string'||row.data.length>Math.ceil(LIMIT/3)*4)throw Error('Invalid exit journal entry');const bytes=Uint8Array.from(atob(row.data),c=>c.charCodeAt(0));if(bytes.length!==row.bytes||checksum(bytes)!==row.checksum||row.name==='th143.cfg'&&bytes.length!==92)throw Error('Exit journal checksum changed');files.set(row.name,bytes);}
 const restored=await store.write(files);clearExitJournalV1(raw,storage);return{recovered:true,files:restored};
}
