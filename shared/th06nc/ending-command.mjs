import {readEndingInteger} from './ending-stream.mjs';
const F=Math.fround;
// One original @ command and its trailing line advance. The outer update,
// localization/text queue, ANM services and scene lifetime are separate.
// Script cursor is an offset in bytes+1250; production may supply scriptBase.
export function applyEndingCommand(state,services={}){
 const {bytes,script}=state,v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),base=()=>BigInt(state.scriptBase??0),cursor=()=>Number(v.getBigUint64(0x1250,true)-base()),seek=p=>v.setBigUint64(0x1250,base()+BigInt(p),true),start=cursor();
 if(bytes.length!==0x1280||script[start]!==64)throw Error('TH06nc ending: expected command');
 const command=String.fromCharCode(script[start+1]);seek(start+1);
 const read=()=>{const r=readEndingInteger(script,cursor());seek(r.next);return r.value;},text=p=>{let end=p;while(end<script.length&&script[end])end++;if(end===script.length)throw Error('TH06nc ending: unterminated string');return new TextDecoder().decode(script.subarray(p,end));};
 let action='continue';
 const resetVms=()=>{for(let i=0;i<16;i++)v.setUint16(0x70+i*288,0,true);};
 const finishLine=()=>{const data=state.script;let p=cursor();while(p<data.length&&data[p]!==10&&data[p]!==13)p++;while(p<data.length&&(data[p]===10||data[p]===13))p++;if(p===data.length)throw Error('TH06nc ending: line outside stream');seek(p);};
 switch(command){
  case 'z':return 'end';
  case 'b':if(services.loadBackground(text(start+2))!==0)return 'end';break;
  case 'a':{seek(start+2);const slot=read(),scriptId=read(),sprite=read();services.bindAnm(0x38+slot*288,scriptId+0x620);services.bindSprite(0x38+slot*288,sprite+0x620);break;}
  case 'V':{seek(start+2);const value=read(),duration=read();v.setFloat32(0x1248,F(F(value)/F(duration)),true);break;}
  case 'v':seek(start+2);v.setFloat32(0x1244,F(read()),true);break;
  case 'F':{
   if(services.switchScript(text(start+2))!==0)return 'end';
   const cleared=services.cleared;if(!(cleared instanceof Uint8Array)||cleared.length!==96)throw Error('TH06nc ending: CLRD missing');
   for(let profile=0;profile<4;profile++)for(let difficulty=0;difficulty<4;difficulty++)if(cleared[profile*24+12+difficulty]===99||cleared[profile*24+17+difficulty]===99)v.setUint8(0x124c,1);
   resetVms();break;
  }
  case 'R':resetVms();break;
  case 'm':services.playMusic(text(start+2));break;
  case 'M':seek(start+2);services.fadeMusic(F(read()));break;
  case 's':seek(start+2);v.setInt32(0x18,read(),true);v.setInt32(0x1c,read(),true);break;
  case 'c':seek(start+2);v.setInt32(0x10,read(),true);break;
  case '0':case '1':case '2':case '3':seek(start+2);v.setInt32(0x30,Number(command)+1,true);v.setInt32(0,0,true);v.setInt32(4,read(),true);break;
  case 'r':case 'w':{
   seek(start+2);const p=command==='r'?0x126c:0x1264;v.setInt32(p,read(),true);v.setInt32(p-4,-999,true);v.setInt32(command==='r'?0x1238:0x123c,read(),true);action='yield';break;
  }
  default:break;
 }
 finishLine();return action;
}
