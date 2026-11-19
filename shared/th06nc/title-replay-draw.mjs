import {enqueueAsciiText} from './ascii-text.mjs';
const F=Math.fround,profiles=['ReimuA ','ReimuB ','MarisaA','MarisaB'],modes=['Standard ','Challenge','Mouse    ','SpellPr  '],stages=['STAGE1','STAGE2','STAGE3','STAGE4','STAGE5','STAGE6','EXTRA '];
// Title replay text/difficulty overlay 55266..556a7. The ordinary title draw
// loop owns the two visible replay00 VMs; the other VMs are text anchors.
export function drawTitleReplay(group,draw,{state,records,decoded=null,ascii}){
 const font=ascii.v,pos=p=>[0,1,2].map(i=>group.slots.get(p).v.getFloat32(0xc8+i*4,true)),color=c=>font.setUint32(0x52cc,c,true),text=(value,position)=>enqueueAsciiText(ascii,{text:value,position}),pulse=()=>{const t=state.pulse%72,a=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);return ((a<<24)|0xffffff)>>>0;},cstring=(b,p)=>{let end=p;while(end<b.length&&b[end])end++;return String.fromCharCode(...b.subarray(p,end));};
 text('No.   Name      Date     Player  Mode      Detail',pos(0x13de0));
 const first=Math.trunc(state.replaySelection/15)*15;
 for(let row=first;row<first+15&&row<records.length;row++){
  const selected=row===state.replaySelection,header=records[row].header,mode=header[6],profile=header[7],detail=header[8],at=pos(0x13f00+(row-first)*288);ascii.bytes[0x52c9]=Number(selected);color(selected?([18,19].includes(state.state)?pulse():0xffffffff):0xff808080);
  text(`${records[row].label} ${cstring(header,29).padStart(8,' ')}  ${cstring(header,20).padStart(8,' ')} ${profiles[profile].padStart(7,' ')} ${modes[mode].padStart(9,' ')}`+(mode===3?` No.${String(detail+1).padStart(3,'0')}`:''),at);
  if(mode!==3&&detail<=4){const vm=group.slots.get(0x16050),v=vm.v;vm.bindSprite(0x792+detail);at.forEach((x,i)=>v.setFloat32(0xc8+i*4,x,true));v.setFloat32(0xc8,F(at[0]+F(516)),true);v.setFloat32(0xcc,F(at[1]+F(0)),true);v.setFloat32(0xe4,1,true);v.setFloat32(0xe8,1,true);v.setUint32(0xec,font.getUint32(0x52cc,true),true);draw(vm,{snap:true,offset:0x16050,path:'flat'});}
 }
 if([20,26].includes(state.state)&&decoded){
  color(0xffffffff);ascii.bytes[0x52c9]=0;const at=pos(0x13cc0),v=new DataView(decoded.bytes.buffer,decoded.bytes.byteOffset,decoded.bytes.byteLength),slow=v.getFloat32(52,true);text('       '+slow.toFixed(3).padStart(5,' ')+'%',[F(at[0]+F(-55)),F(at[1]+F(15)),at[2]]);text('STAGE  LastScore',pos(0x14fe0));
  for(let i=0;i<7;i++){const selected=i===state.selection;ascii.bytes[0x52c9]=Number(selected);color(selected?pulse():0xff808080);const offset=decoded.stageOffsets[i],score=offset===null?'---------':String(v.getBigInt64(offset,true)).padStart(9,' ');text(`${stages[i]} ${score}`,pos(0x15100+i*288));}
 }
 color(0xffffffff);ascii.bytes[0x52c9]=0;
}
