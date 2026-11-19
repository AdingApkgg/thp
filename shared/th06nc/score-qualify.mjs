import {sanitizeScoreName,insertHighScore} from './score-tables.mjs';
import {initializeScoreNameCursor} from './score-name-input.mjs';
// Candidate and rank qualification, 70bab..70dca. Caller has already selected
// owner +4/+a8/+ac and published the two profile labels for state 9.
export function qualifyResultScore(state,table,{shot=0,score=0n,stageIndex=1,cleared=false,previousName=''}={}){
 const {bytes,v}=state;bytes[0x9e6c]=(v.getInt32(4,true)*2+(shot&255))&255;bytes[0x9e6d]=v.getInt32(0xa8,true)&255;bytes[0x9e6e]=v.getInt32(0xac,true)&255;v.setBigUint64(0x9e64,BigInt.asUintN(64,BigInt(score)),true);bytes[0x9e60]=0x10;v.setUint32(0x9e58,0x52435348,true);bytes[0x9e61]=1;bytes[0x9e6f]=cleared?99:stageIndex&255;bytes.set(sanitizeScoreName(previousName),0x9e70);
 // Keep a view: name edits must update the candidate already in the rank list.
 const record=bytes.subarray(0x9e58,0x9e7c),rank=insertHighScore(table,record);
 if(rank>=10){v.setInt32(0x9e94,15,true);v.setInt32(0x4450,0,true);for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,2,true);bytes.set(bytes.subarray(0x9e70,0x9e79),0x9e88);}
 else{initializeScoreNameCursor(state);bytes[0x9e88]=0;}return {rank,record,qualifies:rank<10};
}
