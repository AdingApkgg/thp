import {gunzipSync} from 'node:zlib';
import {effectDrawIndependentBytes} from '../shared/th06nc/effect-compare.mjs';
export const comparisonPolicy='native-inactive-effect-position-and-item-draw-cache-v1';
export function unpackActorSnapshot(layout,compressed){
 const total=layout.reduce((sum,row)=>sum+row.bytes,0);if(!Number.isSafeInteger(total)||total<=0||total>32*1024*1024)throw Error('Invalid actor snapshot size');
 const bytes=gunzipSync(compressed,{maxOutputLength:total}),pools=new Map();let offset=0;
 for(const row of layout){if(!Number.isSafeInteger(row.bytes)||row.bytes<0||offset+row.bytes>bytes.length)throw Error('Invalid actor snapshot layout');pools.set(row.name,new Uint8Array(bytes.subarray(offset,offset+row.bytes)));offset+=row.bytes;}
 if(offset!==bytes.length)throw Error('Trailing actor snapshot bytes');return pools;
}
export function itemDrawIndependentBytes(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==1025*0x160)throw Error('Invalid item comparison pool');
 const copy=bytes.slice();
 for(let slot=0;slot<1024;slot++){
  const p=slot*0x160;if(copy[p]!==0)continue;const vm=p+0x38;
  // Only fields published by11b0a item drawing / sprite binding: sprite ID,
  // UV state, draw position, color, sprite binding and normal/arrow cache.
  for(const [offset,length]of [[0x34,2],[0x3c,0x40],[0xc8,12],[0xec,4],[0x100,8]])copy.fill(0,vm+offset,vm+offset+length);
  copy[p+0x158]=0;
 }
 return copy;
}
export function drawIndependentPool(name,bytes){return name==='effects'?effectDrawIndependentBytes(bytes):name==='items'?itemDrawIndependentBytes(bytes):bytes;}
