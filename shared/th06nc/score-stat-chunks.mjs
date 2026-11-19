// Native writer 747a4..74a3a. Raw global owners are explicit inputs; this
// does not load/update gameplay statistics; those owners are separate.
// optionalRecords is the PSCR region (96 slots visited by this writer).
const lengths={cleared:96,cardAttack:134*384,optionalRecords:96*24,music:16};
const tag=(b,p,s)=>{for(let i=0;i<4;i++)b[p+i]=s.charCodeAt(i);};
const header=(b,p,size)=>{const v=new DataView(b.buffer,b.byteOffset,b.byteLength);v.setUint16(p+4,size,true);v.setUint16(p+6,size,true);b[p+8]=21;};
export function serializeScoreStatChunks(owners){
 for(const [key,length]of Object.entries(lengths))if(!(owners[key]instanceof Uint8Array)||owners[key].length!==length)throw Error('TH06nc score stats: invalid '+key);
 const {cleared,cardAttack,optionalRecords,music}=owners,records=[];
 for(let p=0;p<96;p+=24){tag(cleared,p,'CLRD');header(cleared,p,24);records.push(cleared.slice(p,p+24));}
 const cards=new DataView(cardAttack.buffer,cardAttack.byteOffset,cardAttack.byteLength);
 for(let i=0;i<134;i++){const p=i*384;if(cards.getUint32(p,true)!==0x4b544143)continue;header(cardAttack,p,384);cards.setUint16(p+16,i,true);records.push(cardAttack.slice(p,p+384));}
 const optional=new DataView(optionalRecords.buffer,optionalRecords.byteOffset,optionalRecords.byteLength);
 for(let p=0;p<96*24;p+=24){if(optional.getBigUint64(p+12,true)===0n)continue;header(optionalRecords,p,24);records.push(optionalRecords.slice(p,p+24));}
 tag(music,0,'MUSC');header(music,0,16);records.push(music.slice());
 return records;
}
