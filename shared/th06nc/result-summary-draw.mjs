import {enqueueAsciiText} from './ascii-text.mjs';
const F=Math.fround;
// Summary path of 72890 (states 15/16), including the exiting rank columns.
export function drawResultSummary(state,draw,{ascii,tables,environment,setupCamera=null}={}){
 const {v,bytes}=state;if(![15,16].includes(v.getInt32(0x9e94,true))||v.getInt32(0x9e9c,true)===8)throw Error('TH06nc result: summary draw required');
 const emit=(offset,path='flat')=>draw(state.vm(offset),{snap:true,space:'screen',part:'result',offset,path}),font=ascii.v,color=x=>font.setUint32(0x52cc,x,true),text=(value,position)=>enqueueAsciiText(ascii,{text:value,position});setupCamera?.({minZ:-1,maxZ:-1});
 for(const [p,path]of [[0x3d70,'flat'],[0x3fb0,'rotated'],[0x41f0,'rotated'],[0x40d0,'flat']])emit(p,path);
 for(let i=0;i<38;i++){
  const p=0xb0+i*288,old=[0,1,2].map(i=>v.getUint32(p+0xc8+i*4,true));for(let k=0;k<3;k++)v.setFloat32(p+0xc8+k*4,F(v.getFloat32(p+0xc8+k*4,true)+v.getFloat32(p+0x18+k*4,true)),true);try{emit(p);}finally{old.forEach((x,k)=>v.setUint32(p+0xc8+k*4,x,true));}
 }
 const base=[0,1,2].map(k=>v.getFloat32(0x1138+k*4,true));
 if(base[0]<640){
  for(const [p,extra]of [[0x2b70,160],[0x2c90,460]]){v.setUint32(p+0xc4,(v.getUint32(p+0xc4,true)&~0x400)|0x300,true);for(let k=0;k<3;k++)v.setUint32(p+0xc8+k*4,v.getUint32(0x1138+k*4,true),true);let x=base[0];if(p===0x2c90)x=F(x+F(320));v.setFloat32(p+0xc8,F(x+F(p===0x2c90?140:extra)),true);emit(p);}
  let x=base[0],y=F(base[1]+F(36)),z=base[2];const index=v.getInt32(4,true),character=index%2,difficulty=v.getInt32(0xa8,true),mode=Math.trunc(index/2),left=tables.get(`${mode}/${difficulty}/${character*2}`),right=tables.get(`${mode}/${difficulty}/${character*2+1}`);
  const name=record=>{const end=record.subarray(24).indexOf(0),data=record.subarray(24,end<0?record.length:24+end);return String.fromCharCode(...data).padStart(8,' ');},line=record=>{const d=new DataView(record.buffer,record.byteOffset,record.byteLength),stage=record[23],suffix=stage<=6?String(stage):stage===7?'1':'C';return name(record)+' '+String(d.getBigUint64(12,true)).padStart(9,' ')+'('+suffix+')';};;
  if(!left||!right||left.length<10||right.length<10)throw Error('TH06nc result: incomplete rank tables');
  for(let row=0;row<10;row++){
   color(0xffffc0c0);
   text(String(row+1).padStart(2,' '),[x,y,z]);x=F(x+F(36));text(line(left[row]),[x,y,z]);x=F(x+F(300));
   color(0xffc0c0ff);
   text(line(right[row]),[x,y,z]);x=F(x+F(-336));y=F(y+F(18));
  }
 }
 color(0xffffffff);
 const basePosition=[0,1,2].map(i=>v.getFloat32(0x2b18+i*4,true));let x=F(basePosition[0]+F(296)),y=F(basePosition[1]+F(62)),z=basePosition[2];
 color(v.getUint32(0x2b3c,true));text(String(BigInt.asUintN(64,BigInt(environment.score??0))),[x,y,z]);
 y=F(y+F(25.5));state.vm(0x4310).bindSprite(0x792+(environment.difficulty|0));for(const [p,value]of [[0x43d8,x],[0x43dc,y],[0x43e0,z],[0x43f4,1],[0x43f8,1]])v.setFloat32(p,value,true);v.setUint32(0x43fc,v.getUint32(0x2b3c,true),true);emit(0x4310);
 const row=value=>{y=F(y+F(25.5));text(value,[x,y,z]);};row(environment.lifeProtection?'Challenge':'Standard');
 const progress=F(F(environment.messageClock|0)/F((environment.difficulty|0)<4?89500:39600));row((environment.difficulty|0)!==0&&environment.cleared?'100%':F(progress*F(100)).toFixed(2)+'%');
 row(String((environment.continuesUsed??0)&255));row(String(environment.deathCount|0));row(String(environment.bombCount|0));row(String(environment.captures|0));
 const ratio=F(F(environment.timingNumerator??0)/F(environment.timingDenominator??0)),scaled=F(F(ratio-F(.5))*F(2)),clamped=scaled<0?0:Number.isNaN(scaled)?NaN:Math.min(1,scaled),slowdown=F(F(F(1)-F(clamped))*F(100));
 y=F(y+F(36));text(Number.isNaN(slowdown)?'-nan(ind)%':slowdown.toFixed(2)+'%',[x,y,z]);
 color(0xffffffff);emit(0x3e90);
}
