// Record owner: 1a0 bytes. Heap pointers use stable identity tokens for raw
// owner comparisons, never native process addresses or on-disk offsets.
export const replayHeaderToken=0x1000,replayStageCapacity=0x9e33c;
export const replayStageToken=index=>0x100000+index*0x100000;
const data=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
export class ReplayRecorder {
 constructor(){this.bytes=new Uint8Array(0x1a0);this.v=data(this.bytes);this.header=null;this.stages=Array(7).fill(null);this.stageIndex=0;this.cursor=0;this.ends=Array(7).fill(0);for(const p of [0x9c,0x10c,0x12c,0x154])this.v.setInt32(p,-1,true);this.v.setInt16(0xac,-1,true);}
 // Record task init 6bfd0. Stage allocations are zero-filled host buffers;
 // unused malloc padding is outside allocator-equivalence claims.
 initializeStage(environment){
  const e=environment,index=(e.stageIndex|0)-1;if(index<0||index>=7)throw Error('TH06nc replay: invalid stage');this.v.setInt32(0x30,0,true);this.bytes[9]=0;
  if(!this.header){this.header=new Uint8Array(120);const h=data(this.header);h.setUint32(0,0x50523654,true);h.setUint16(4,0x10f,true);this.header[7]=((e.character&255)*2+(e.shot&255))&255;this.header[8]=(e.difficulty??0)&255;this.header[6]=e.spellPractice?3:e.lifeProtection?1:0;if(e.spellPractice)this.header[8]=(e.spellPracticeIndex??0)&255;this.header.set([78,79,32,78,65,77,69,0],29);this.v.setBigUint64(0x70,BigInt(replayHeaderToken),true);}
  else{const previous=this.stages[index-1];if(!previous)return -1;data(previous).setBigUint64(0,BigInt.asUintN(64,BigInt(e.score??0)),true);}
  const stage=new Uint8Array(replayStageCapacity),v=data(stage);this.stages[index]=stage;this.stageIndex=index+1;data(this.header).setBigUint64(64+index*8,BigInt(replayStageToken(index)),true);
  v.setUint16(8,(e.replaySeed??0)&65535,true);v.setUint16(10,(e.pointTotalCount??0)&65535,true);stage[12]=(e.playerPower??0)&255;stage[13]=(e.lives??0)&255;stage[14]=(e.bombs??0)&255;stage[16]=(e.powerItemChain??0)&255;v.setUint16(18,(e.deathCount??0)&65535,true);this.cursor=20;this.v.setBigUint64(0,BigInt(replayStageToken(index)+this.cursor),true);return 0;
 }
 advance(held,previous,{active=true}={}){
  if(!active||this.bytes[9])return 1;const index=this.stageIndex-1,stage=this.stages[index];if(!stage)throw Error('TH06nc replay: stage not initialized');const v=data(stage),masked=held&1023;
  if(masked!==v.getUint32(this.cursor+4,true)){this.cursor+=12;this.requireSpace(12);this.v.setBigUint64(0,BigInt(replayStageToken(index)+this.cursor),true);this.ends[index]=this.cursor+12;this.v.setBigUint64(0x38+index*8,BigInt(replayStageToken(index)+this.ends[index]),true);v.setInt32(this.cursor,this.v.getInt32(0x30,true),true);v.setUint32(this.cursor+4,masked,true);v.setUint32(this.cursor+8,previous&1023,true);}
  this.v.setInt32(0x30,(this.v.getInt32(0x30,true)+1)|0,true);return 1;
 }
 requireSpace(count){if(this.cursor+count>replayStageCapacity)throw Error('TH06nc replay: native recording capacity exceeded');}
 // 6c3a0 seals once: zero input at the current frame, then 9,999,999 sentinel.
 finish(){
  const index=this.stageIndex-1;if(this.bytes[8]||this.bytes[9]||!this.header||index<0||index>=7||!this.stages[index])return;this.requireSpace(36);const v=data(this.stages[index]);this.cursor+=12;this.bytes[9]=1;v.setInt32(this.cursor,this.v.getInt32(0x30,true),true);v.setUint32(this.cursor+4,0,true);v.setUint32(this.cursor+8,0,true);this.cursor+=12;v.setInt32(this.cursor,9999999,true);v.setUint32(this.cursor+4,0,true);v.setUint32(this.cursor+8,0,true);this.ends[index]=this.cursor+12;this.v.setBigUint64(0,BigInt(replayStageToken(index)+this.cursor),true);this.v.setBigUint64(0x38+index*8,BigInt(replayStageToken(index)+this.ends[index]),true);
 }
 report(){return {stage:this.stageIndex,frame:this.v.getInt32(0x30,true),stopped:Boolean(this.bytes[9]),records:this.stages[this.stageIndex-1]?Math.trunc((this.cursor-20)/12)+1:0};}
}
