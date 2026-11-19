import {createScoreChunk,scoreChunkTag} from './score-file.mjs';
const view=b=>new DataView(b.buffer,b.byteOffset,b.byteLength);
// Native 6cc40 leaves absent CATK slots intact. The caller supplies the
// initialized global owner; its startup/default producer is a separate step.
export function loadCardAttackScores(records,destination){
 if(!(destination instanceof Uint8Array)||destination.length!==134*384)throw Error('TH06nc CATK: invalid owner');
 const out=view(destination);
 for(const record of records){if(scoreChunkTag(record)!=='CATK'||record[8]!==21)continue;if(record.length<384)throw Error('TH06nc CATK: truncated record');const index=view(record).getUint16(16,true);if(index>=134)break;const p=index*384;destination.set(record.subarray(0,384),p);
  for(const offset of [60,62])out.setUint16(p+offset,Math.min(out.getUint16(p+offset,true),9999),true);
  for(let offset=0xe0;offset<0x180;offset+=4)out.setUint32(p+offset,Math.min(out.getUint32(p+offset,true),999999999),true);
 }
 return destination;
}
// Native Result initialization 7434f..743f4, including its early termination
// on a matching CLRD with an out-of-range character.
export function loadClearedScores(records){
 const out=new Uint8Array(96);
 for(let profile=0;profile<4;profile++){const r=createScoreChunk('CLRD',24);r.fill(1,12,22);r[22]=profile;out.set(r,profile*24);}
 for(const record of records){if(scoreChunkTag(record)!=='CLRD'||record[8]!==21)continue;if(record.length<24)throw Error('TH06nc CLRD: truncated record');const index=record[22];if(index>=4)break;out.set(record.subarray(0,24),index*24);}
 return out;
}
// Native 6ce20 initializes 96 PSCR slots but accepts wider indices while
// loading: character<4, difficulty<5, stage<7 with stride 4 and 6. Preserve
// the resulting aliases and writes beyond the 96 serialized slots. An
// explicit 101-slot span exposes those writes without truncating them.
export function loadPracticeScores(records,destination=new Uint8Array(101*24)){
 if(!(destination instanceof Uint8Array)||destination.length<101*24)throw Error('TH06nc PSCR: expected full native write span');
 for(let profile=0;profile<4;profile++)for(let stage=0;stage<6;stage++)for(let difficulty=0;difficulty<4;difficulty++){
  const r=createScoreChunk('PSCR',24);r[20]=profile;r[21]=difficulty;r[22]=stage;destination.set(r,((profile*6+stage)*4+difficulty)*24);
 }
 for(const record of records){if(scoreChunkTag(record)!=='PSCR'||record[8]!==21)continue;if(record.length<24)throw Error('TH06nc PSCR: truncated record');const [profile,difficulty,stage]=record.subarray(20,23);if(profile>=4||difficulty>=5||stage>=7)break;destination.set(record.subarray(0,24),((profile*6+stage)*4+difficulty)*24);}
 return destination;
}
// Native title 56042..560be skips both initialization and file loading if
// the first slot already bears CATK, even when other slots are incomplete.
export function initializeTitleCardAttackScores(records,destination){
 if(!(destination instanceof Uint8Array)||destination.length!==134*384)throw Error('TH06nc CATK: invalid owner');
 if(view(destination).getUint32(0,true)===0x4b544143)return destination;
 for(let index=0;index<134;index++){const r=createScoreChunk('CATK',384);view(r).setUint16(16,index,true);destination.set(r,index*384);}
 return loadCardAttackScores(records,destination);
}
// Native boot 45776..457cd takes the last matching MUSC without clamping.
export function loadMusicScores(records){
 let out=createScoreChunk('MUSC',16);
 for(const record of records){if(scoreChunkTag(record)!=='MUSC'||record[8]!==21)continue;if(record.length<16)throw Error('TH06nc MUSC: truncated record');out=record.slice(0,16);}
 return out;
}
