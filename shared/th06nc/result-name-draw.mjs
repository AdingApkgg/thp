import {enqueueAsciiText} from './ascii-text.mjs';
import {scoreNameCharacters} from './score-name-input.mjs';
const F=Math.fround;
// Name-page path of 72890. Other result states have distinct draw owners.
export function drawResultName(state,draw,{ascii,tables,shot=0,setupCamera=null}={}){
 const {v,bytes}=state;if(v.getInt32(0x9e94,true)!==9||v.getInt32(0x9e9c,true)===8)throw Error('TH06nc result: name-page draw required');
 const emit=(offset,path='flat')=>draw(state.vm(offset),{snap:true,space:'screen',part:'result',offset,path}),font=ascii.v,color=x=>font.setUint32(0x52cc,x,true),text=(value,position)=>enqueueAsciiText(ascii,{text:value,position});setupCamera?.({minZ:-1,maxZ:-1});
 for(const [p,path]of [[0x3d70,'flat'],[0x3fb0,'rotated'],[0x41f0,'rotated'],[0x40d0,'flat']])emit(p,path);
 for(let i=0;i<38;i++){
  const p=0xb0+i*288,old=[0,1,2].map(i=>v.getUint32(p+0xc8+i*4,true));for(let k=0;k<3;k++)v.setFloat32(p+0xc8+k*4,F(v.getFloat32(p+0xc8+k*4,true)+v.getFloat32(p+0x18+k*4,true)),true);try{emit(p);}finally{old.forEach((x,k)=>v.setUint32(p+0xc8+k*4,x,true));}
 }
 const base=[0,1,2].map(k=>v.getFloat32(0x1138+k*4,true));
 if(base[0]<640){
  for(const [p,extra]of [[0x2b70,160],[0x2c90,460]]){v.setUint32(p+0xc4,(v.getUint32(p+0xc4,true)&~0x400)|0x300,true);for(let k=0;k<3;k++)v.setUint32(p+0xc8+k*4,v.getUint32(0x1138+k*4,true),true);let x=base[0];if(p===0x2c90)x=F(x+F(320));v.setFloat32(p+0xc8,F(x+F(p===0x2c90?140:extra)),true);emit(p);}
  let x=base[0],y=F(base[1]+F(36)),z=base[2];const character=v.getInt32(4,true),difficulty=v.getInt32(0xa8,true),mode=v.getInt32(0xac,true),left=tables.get(`${mode}/${difficulty}/${character*2}`),right=tables.get(`${mode}/${difficulty}/${character*2+1}`);
  const name=record=>{const end=record.subarray(24).indexOf(0),data=record.subarray(24,end<0?record.length:24+end);return String.fromCharCode(...data).padStart(8,' ');},line=record=>{const d=new DataView(record.buffer,record.byteOffset,record.byteLength),stage=record[23],suffix=stage<=6?String(stage):stage===7?'1':'C';return name(record)+' '+String(d.getBigUint64(12,true)).padStart(9,' ')+'('+suffix+')';},under=()=>{const cursor=Math.min(v.getInt32(0x9e7c,true),7),cells=Array(8).fill(' ');cells[cursor]='_';return cells.join('');};
  if(!left||!right||left.length<10||right.length<10)throw Error('TH06nc result: incomplete rank tables');
  for(let row=0;row<10;row++){
   if(shot!==0)color(0x80ffc0c0);else if(left[row][9]){color(0xfff0f0ff);text(under(),[F(x+F(36)),F(y+F(3.5)),z]);}else color(0x80ffffc0);
   text(String(row+1).padStart(2,' '),[x,y,z]);x=F(x+F(36));text(line(left[row]),[x,y,z]);x=F(x+F(300));
   if(shot!==1)color(0x80c0c0ff);else if(right[row][9]){color(0xfffff0f0);text(under(),[x,F(y+F(3.5)),z]);}else color(0xc0c0c0ff);
   text(line(right[row]),[x,y,z]);x=F(x+F(-336));y=F(y+F(18));
  }
 }
 let y=F(356),x=F(160);const selected=v.getInt32(0,true),clock=v.getInt32(0x4450,true);
 for(let row=0;row<6;row++){
  for(let column=0;column<16;column++){
   const index=row*16+column;let offset=F(0);if(index===selected){color(0xffffffc0);let scale=F(F(F(clock%32)*F(.8))*F(.03125));scale=clock%64<32?F(scale+F(1.2)):F(F(2)-scale);font.setFloat32(0,scale,true);font.setFloat32(4,scale,true);offset=F(F(-F(scale-F(1)))*F(8));}
   else{color(0x60c0c0c0);font.setFloat32(0,1,true);font.setFloat32(4,1,true);}
   text(String.fromCharCode(index===94?128:index===95?129:scoreNameCharacters.charCodeAt(index)),[F(x+offset),F(y+offset),0]);x=F(x+F(20));
  }y=F(y+F(18));x=F(x-F(320));
 }
 font.setFloat32(0,1,true);font.setFloat32(4,1,true);color(0xffffffff);emit(0x3e90);
}
