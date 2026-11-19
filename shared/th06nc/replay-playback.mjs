const view=b=>new DataView(b.buffer,b.byteOffset,b.byteLength),token=0x1000;
// Playback task 6c1b0/6ba40. Decoded stage references remain file offsets;
// the raw owner uses one stable file identity for pointer comparisons.
export class ReplayPlayback {
 constructor(decoded){this.file=decoded.bytes.slice();this.offsets=[...decoded.stageOffsets];this.bytes=new Uint8Array(0x1a0);this.v=view(this.bytes);this.bytes[8]=1;this.v.setBigUint64(0x70,BigInt(token),true);this.cursor=0;this.stageEnd=0;}
 initializeStage(e){
  this.v.setInt32(0x30,0,true);const index=(e.stageIndex|0)-1,offset=this.offsets[index];if(offset==null)return -1;const first=this.offsets.find(p=>p!==null),v=view(this.file),h=this.file;
  e.defaultLives=h[first+13];e.defaultBombs=h[first+14];e.character=h[7]>>>1;e.shot=h[7]&1;if(h[6]!==3)e.difficulty=h[8];e.lifeProtection=h[6]===1;e.pointTotalCount=v.getUint16(offset+10,true);e.rng.seed=v.getUint16(offset+8,true);e.rng.count=0;e.lives=h[offset+13];e.bombs=h[offset+14];e.playerPower=h[offset+12];e.powerItemChain=h[offset+16];e.deathCount=v.getInt16(offset+18,true);
  if(index>=1&&this.offsets[index-1]!=null)e.score=e.displayScore=v.getBigUint64(this.offsets[index-1],true);this.cursor=offset+20;this.stageEnd=this.offsets.slice(index+1).find(p=>p!==null)??this.file.length;this.v.setBigUint64(0,BigInt(token+this.cursor),true);return 0;
 }
 advance(input,{active=true}={}){
  if(!active)return 1;const v=view(this.file),frame=this.v.getInt32(0x30,true);
  for(;;){if(this.cursor+16>this.stageEnd)throw Error('TH06nc replay: input stream lacks a sentinel');if(frame<v.getInt32(this.cursor+12,true))break;this.cursor+=12;this.v.setBigUint64(0,BigInt(token+this.cursor),true);}
  const held=v.getUint32(this.cursor+4,true);input.held=((input.held&~1023)|held)>>>0;input.previous=frame===v.getInt32(this.cursor,true)?v.getUint32(this.cursor+8,true):held;input.repeat=0;input.repeatClock=0;this.v.setInt32(0x30,(frame+1)|0,true);return 1;
 }
}
// Playback dialogue task 6b9f0; native scheduling of returned task code 6 is
// separate from the input stream and must not be replaced with an input flag.
export function replayDialogueTaskResult(frame,{active=true,messageField=-1,indicator=false}={}){return active&&messageField>=0&&indicator&&(frame|0)%3!==2?6:1;}
