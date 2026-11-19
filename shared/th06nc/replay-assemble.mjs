import {encodeReplayFile} from './replay-file.mjs';
const F=Math.fround,view=bytes=>new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
// Record-mode writer 6c420: header/stage assembly, four RNG draws and codec.
// File delivery is the caller's responsibility; no successful write is implied.
export function assembleRecordedReplay(recorder,{environment,name,date,preserveRecording=false}={}){
 const r=recorder,e=environment;if(r.bytes[8]||!r.header||!r.stages[r.stageIndex-1])throw Error('TH06nc replay: live recording required');if(!e?.rng?.next16)throw Error('TH06nc replay: native RNG required');if(typeof date!=='string'||!/^[0-9]{2}\/[0-9]{2}\/[0-9]{2}$/.test(date))throw Error('TH06nc replay: local date required');
 const input=typeof name==='string'?Uint8Array.from([...name].map(c=>c.charCodeAt(0))):name;if(!(input instanceof Uint8Array))throw Error('TH06nc replay: name bytes required');const terminator=input.indexOf(0),length=terminator<0?input.length:terminator;if(length>8)throw Error('TH06nc replay: name exceeds eight bytes');
 r.finish();view(r.stages[r.stageIndex-1]).setBigUint64(0,BigInt.asUintN(64,BigInt(e.score??0)),true);const header=r.header.slice(),h=view(header);header.fill(0,9,16);header.fill(0,38,40);header.fill(0,60,120);h.setBigUint64(40,BigInt.asUintN(64,BigInt(e.displayScore??0)),true);
 const ratio=F(F(e.timingNumerator??0)/F(e.timingDenominator??0)),scaled=F(F(ratio-F(.5))*F(2)),clamped=scaled<0?0:Number.isNaN(scaled)?NaN:Math.min(1,scaled),slow=F(F(F(1)-F(clamped))*F(100));
 for(const [p,value]of [[48,F(slow+F(1.12))],[52,slow],[56,F(slow+F(2.34))]]){if(Number.isNaN(value))h.setUint32(p,0xffc00000,true);else h.setFloat32(p,value,true);}
 header.set(input.subarray(0,length),29);header[29+length]=0;header.set([...date].map(c=>c.charCodeAt(0)),20);header[28]=0;
 header[18]=(e.rng.next16()&127)+64;header[19]=e.rng.next16()&255;header[16]=e.rng.next16()&255;header[17]=e.rng.next16()&255;
 let size=120;for(let i=0;i<7;i++)if(r.stages[i]){if(r.ends[i]<32)throw Error('TH06nc replay: unsealed stage');h.setBigUint64(64+i*8,BigInt(size),true);size+=r.ends[i];}
 const plain=new Uint8Array(size);plain.set(header);let cursor=120;for(let i=0;i<7;i++)if(r.stages[i]){plain.set(r.stages[i].subarray(0,r.ends[i]),cursor);cursor+=r.ends[i];}const encoded=encodeReplayFile(plain);
 if(!preserveRecording){for(let i=0;i<7;i++){r.stages[i]=null;view(r.header).setBigUint64(64+i*8,0n,true);}}
 return encoded;
}
