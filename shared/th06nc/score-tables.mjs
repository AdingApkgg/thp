import {createScoreChunk,scoreChunkTag} from './score-file.mjs';
const v=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),key=(mode,difficulty,character)=>`${mode}/${difficulty}/${character}`;
export function sanitizeScoreName(input){
 const source=typeof input==='string'?new TextEncoder().encode(input):input,out=new Uint8Array(9);out.fill(32,0,8);for(let i=0;i<8&&i<source.length&&source[i];i++)out[i]=source[i]>=32&&source[i]<=126?source[i]:32;return out;
}
export function createHighScoreRecord({score=0n,name='',character=0,difficulty=0,mode=0,stage=1,prototype=false}={}){
 const bytes=createScoreChunk(prototype?'SYMD':'HSCR',36),d=v(bytes);d.setBigUint64(12,BigInt.asUintN(64,BigInt(score)),true);bytes[20]=character;bytes[21]=difficulty;bytes[22]=mode;bytes[23]=stage;bytes.set(sanitizeScoreName(name),24);return bytes;
}
export function highScoreFields(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==36)throw Error('TH06nc score: invalid high-score record');return {score:v(bytes).getBigUint64(12,true),character:bytes[20],difficulty:bytes[21],mode:bytes[22],stage:bytes[23],name:String.fromCharCode(...bytes.subarray(24,32)),prototype:scoreChunkTag(bytes)==='SYMD'};
}
// Original 6cbc0 inserts before an equal unsigned 64-bit score. It does not
// truncate the linked list; serialization visits only its first ten nodes.
export function insertHighScore(table,record){const score=highScoreFields(record).score;let rank=0;while(rank<table.length&&highScoreFields(table[rank]).score>score)rank++;table.splice(rank,0,record);return rank;}
export function createDefaultScoreTables(){
 const tables=new Map();for(let mode=0;mode<3;mode++)for(let difficulty=0;difficulty<5;difficulty++)for(let character=0;character<4;character++)tables.set(key(mode,difficulty,character),Array.from({length:10},(_,rank)=>createHighScoreRecord({score:BigInt(1000000-rank*100000),name:'Nanashi ',character,difficulty,mode,stage:1,prototype:true})));return tables;
}
export function loadHighScoreTables(records){
 const tables=createDefaultScoreTables();for(const bytes of records){if(bytes.length!==36||scoreChunkTag(bytes)!=='HSCR'||bytes[8]!==0x15)continue;const table=tables.get(key(bytes[22],bytes[21],bytes[20]));if(table)insertHighScore(table,new Uint8Array(bytes));}return tables;
}
export function serializeHighScoreTables(tables){
 const records=[];for(let mode=0;mode<3;mode++)for(let difficulty=0;difficulty<5;difficulty++)for(let character=0;character<4;character++)for(const record of (tables.get(key(mode,difficulty,character))??[]).slice(0,10)){
  if(scoreChunkTag(record)!=='HSCR')continue;if(record.length!==36)throw Error('TH06nc score: invalid high-score record');const copy=new Uint8Array(record),d=v(copy);d.setUint16(4,36,true);d.setUint16(6,36,true);copy[8]=0x15;copy[9]=0;copy[20]=character;copy[21]=difficulty;copy[22]=mode;records.push(copy);
 }return records;
}
