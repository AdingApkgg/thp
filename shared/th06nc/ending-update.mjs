import {applyEndingCommand} from './ending-command.mjs';
const F=Math.fround;
export function endingTextLines(key,{lifeProtection=false,localization={}}={}){
 if(lifeProtection){if(key==='ED_END00B_04')key='ED_END00B_05';else if(key==='ED_END10B_04')key='ED_END10B_05';}
 const text=localization[key]??key;if(text==='')return [];const lines=text.split('\n');if(text.endsWith('\n'))lines.pop();return lines;
}
// Original update 2bac0. ANM, publication, and platform services remain explicit.
// textQueue represents the original deque's values, not its allocator layout.
export function advanceEnding(state,{held=0,previous=0,lifeProtection=false,localization={}}={},services={}){
 const {bytes}=state,v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),queue=state.textQueue??= [],get=p=>v.getInt32(p,true),put=(p,x)=>v.setInt32(p,x,true),cursor=()=>Number(v.getBigUint64(0x1250,true)-BigInt(state.scriptBase??0)),seek=p=>v.setBigUint64(0x1250,BigInt(state.scriptBase??0)+BigInt(p),true),confirm=(held&256)!==0&&(held&256)!==(previous&256),skip=()=>v.getUint8(0x124c)!==0&&(held&8)!==0;
 let repeats=0;
 for(;;){
  let consume=false;
  if(get(0x126c)>0){
   put(0x126c,get(0x126c)-1);
   if(get(0x1238)!==0)put(0x1238,get(0x1238)-1);
   else if(confirm||skip()){put(0x126c,0);put(0x1268,-999);}
   if(get(0x126c)>0)consume=true;
   else{bytes.fill(0,0x38,0x1238);put(0x1270,0);}
  }
  if(!consume&&get(0x1264)>0){
   put(0x1264,get(0x1264)-1);
   if(get(0x123c)!==0)put(0x123c,get(0x123c)-1);
   else if(confirm||skip()){put(0x1264,0);put(0x1260,-999);}
   consume=true;
  }
  if(!consume&&queue.length){
   const text=queue.shift(),line=get(0x1270),offset=0x38+line*2*288,id=0x737+line*2;
   if(text!==''){v.setUint16(offset+0x38,id,true);services.prepareText(offset,id);services.publishText({offset,id,text,color:v.getUint32(0x10,true),colors:[0xc0d0d0,0x10101,0x40202]});}
   const duration=get((held&256)!==0?0x1c:0x18);put(0x1264,duration);put(0x1260,-999);put(0x123c,duration);put(0x1270,line+1);consume=true;
  }
  if(!consume){
   const key=[];let operations=0;
   for(;;){
    if(++operations>100000)throw Error('TH06nc ending: unbounded command stream');
    const script=state.script,p=cursor(),byte=script[p];if(byte===undefined)throw Error('TH06nc ending: cursor outside script');
    if(byte===64){const action=applyEndingCommand(state,services);if(action==='end')return 0;if(action==='yield')break;continue;}
    if(byte===0||byte===10||byte===13){
     if(key.length)queue.push(...endingTextLines(new TextDecoder().decode(Uint8Array.from(key)),{lifeProtection,localization}));
     let next=cursor();while(next<script.length&&[0,10,13].includes(script[next]))next++;if(next===script.length)throw Error('TH06nc ending: unterminated stream');seek(next);break;
    }
    if(key.length<39)key.push(byte);seek(p+1);
   }
  }
  put(0x1258,get(0x125c));put(0x125c,get(0x125c)+1);
  const scroll=F(v.getFloat32(0x1244,true)-v.getFloat32(0x1248,true));v.setFloat32(0x1244,scroll,true);if(scroll<=0)v.setBigUint64(0x1244,0n,true);
  for(let i=0;i<16;i++){const offset=0x38+i*288;if(v.getUint16(offset+0x38,true)!==0)services.tickAnm(offset);}
  if(!skip()||repeats>=4)return 1;repeats++;
 }
}
