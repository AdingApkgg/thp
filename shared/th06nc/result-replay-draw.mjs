import {scoreNameCharacters} from './score-name-input.mjs';
import {enqueueAsciiText} from './ascii-text.mjs';
import {drawScoreSpellTable} from './score-spell-draw.mjs';
const F=Math.fround;
// Result draw 72890 for replay pages 10..14 and closing state 2; viewMode 8 is separate.
export function drawResultReplay(state,draw,{ascii,tables,spellRecords,spellTable,environment={},setupCamera=null}={}){
 const {v,bytes}=state;if(![0,1,2,3,4,5,6,7,8,10,11,12,13,14].includes(v.getInt32(0x9e94,true)))throw Error('TH06nc result: score/replay-page draw required');
 const emit=(offset,path='flat')=>draw(state.vm(offset),{snap:true,space:'screen',part:'result',offset,path}),font=ascii.v,color=x=>font.setUint32(0x52cc,x,true),text=(value,position)=>enqueueAsciiText(ascii,{text:value,position});setupCamera?.({minZ:-1,maxZ:-1});
 for(const [p,path]of [[0x3d70,'flat'],[0x3fb0,'rotated'],[0x41f0,'rotated'],[0x40d0,'flat']])emit(p,path);
 for(let i=0;i<38;i++){
  const p=0xb0+i*288,old=[0,1,2].map(i=>v.getUint32(p+0xc8+i*4,true));for(let k=0;k<3;k++)v.setFloat32(p+0xc8+k*4,F(v.getFloat32(p+0xc8+k*4,true)+v.getFloat32(p+0x18+k*4,true)),true);try{emit(p);}finally{old.forEach((x,k)=>v.setUint32(p+0xc8+k*4,x,true));}
 }
 const base=[0,1,2].map(k=>v.getFloat32(0x1138+k*4,true));
 if(base[0]<640&&v.getInt32(0x9e9c,true)===8)drawScoreSpellTable(state,emit,{ascii,spellRecords,spellTable});
 else if(base[0]<640){
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
 const kind=v.getInt32(0x9e94,true);
 if(kind===13){
 let y=F(356),x=F(160);const selected=v.getInt32(0,true),clock=v.getInt32(0x4450,true);
 for(let row=0;row<6;row++){
  for(let column=0;column<16;column++){
   const index=row*16+column;let offset=F(0);if(index===selected){color(0xffffffc0);let scale=F(F(F(clock%32)*F(.8))*F(.03125));scale=clock%64<32?F(scale+F(1.2)):F(F(2)-scale);font.setFloat32(0,scale,true);font.setFloat32(4,scale,true);offset=F(F(-F(scale-F(1)))*F(8));}
   else{color(0x60c0c0c0);font.setFloat32(0,1,true);font.setFloat32(4,1,true);}
   text(String.fromCharCode(index===94?128:index===95?129:scoreNameCharacters.charCodeAt(index)),[F(x+offset),F(y+offset),0]);x=F(x+F(20));
  }y=F(y+F(18));x=F(x-F(320));
 }
  font.setFloat32(0,1,true);font.setFloat32(4,1,true);
 }
 if(kind>=10&&kind<=14){
  for(let i=0;i<6;i++)emit(0x1190+i*288);
  const position=p=>[0,1,2].map(k=>v.getFloat32(p+k*4,true)),string=p=>{let end=p;while(end<bytes.length&&bytes[end])end++;return String.fromCharCode(...bytes.subarray(p,end));};
  text('No.   Name      Date     Player  Mode      Detail',position(0x1918));
  const selected=v.getInt32(0x4438,true),first=Math.trunc(selected/15)*15,profiles=['ReimuA ','ReimuB ','MarisaA','MarisaB'],modes=['Standard ','Challenge','Mouse    ','SpellPr  '];
  for(let row=first;row<first+15&&row<60;row++){
   const at=position(0x1a38+(row-first)*288),selectedRow=row===selected,rowColor=selectedRow?0xffff8080:0xff808080;let record=0x9eb0+row*120;const pending=kind===13&&selectedRow;color(rowColor);
   if(pending)record=0xbad0;
   if(!pending&&(v.getUint32(record,true)!==0x50523654||v.getUint16(record+4,true)!==0x10f)){text(`No.${String(row+1).padStart(2,'0')} --------  --/--/-- ------- --------- -------`,at);continue;}
   const mode=bytes[record+6],profile=pending?(environment.character&255)*2+(environment.shot&255):bytes[record+7],detail=bytes[record+8],name=pending?string(0x9e88):string(record+29),date=pending?string(0xbae4):string(record+20);
   if(!profiles[profile]||!modes[mode])throw Error('TH06nc replay: invalid profile/mode label');
   const line=`No.${String(row+1).padStart(2,'0')} ${name.padStart(8,' ')}  ${date.padStart(8,' ')} ${profiles[profile].padStart(7,' ')} ${modes[mode].padStart(9,' ')}`+(mode===3?` No.${String(detail+1).padStart(3,'0')}`:'');text(line,at);
   if(pending){const cursor=Math.min(v.getInt32(0x9e7c,true),7),cells=Array(8).fill(' ');cells[cursor]='_';color(0xfff0f0ff);text(cells.join(''),[F(at[0]+F(72)),F(at[1]+F(3.5)),at[2]]);}
   if(mode!==3&&detail<=4){state.vm(0x4310).bindSprite(0x792+detail);for(let i=0;i<3;i++)v.setFloat32(0x43d8+i*4,at[i],true);v.setFloat32(0x43d8,F(at[0]+F(516)),true);v.setFloat32(0x43f4,1,true);v.setFloat32(0x43f8,1,true);v.setUint32(0x43fc,rowColor,true);emit(0x4310);}
  }
 }
 color(0xffffffff);emit(0x3e90);
}
