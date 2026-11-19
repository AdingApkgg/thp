const F=Math.fround;
// Scan-index references in12d69..13019. The native layout/keyboard API
// supplies these physical states; browser KeyboardEvent.code is the adapter.
export const keyboardBindings=[
 ['KeyR',0x13,0x4000],['ArrowRight',0xcd,0x80],['ArrowUp',0xc8,0x10],['ArrowLeft',0xcb,0x40],['ArrowDown',0xd0,0x20],
 ['Numpad6',0x4d,0x80],['Numpad8',0x48,0x10],['Numpad4',0x4b,0x40],['Numpad2',0x50,0x20],['Numpad9',0x49,0x90],['Numpad7',0x47,0x50],['Numpad3',0x51,0xa0],['Numpad1',0x4f,0x60],
 ['KeyD',0x20,0x80],['KeyA',0x1e,0x40],['KeyW',0x11,0x10],['ShiftLeft',0x2a,4],['Space',0x39,4],['KeyL',0x26,4],['KeyS',0x1f,0x1020],['KeyQ',0x10,0x800],['Escape',1,0x600],['KeyK',0x25,0x202],['KeyX',0x2d,0x202],['Enter',0x1c,0x100],['ControlLeft',0x1d,8],['KeyJ',0x24,0x8101],['Semicolon',0x27,8],['KeyZ',0x2c,0x8101],
];
export function keyboardInputMask(held){let mask=0;for(const [code,,bits]of keyboardBindings)if(held.has(code))mask|=bits;return mask;}

// Native127d0, including raw controller secret mask, shared shot/focus hold,
// fixed menu buttons, configured actions and float32 analog direction cones.
export function composeControllerInput(keyboardMask,packet,{connected=true,config,state,gameState=0,paused=false,gameOver=false,spellResultVisible=false,atan2=Math.atan2}={}){
 let mask=keyboardMask|0;if(!connected)return mask;
 const raw=packet.slice(0,18);raw[16]=Number(packet[16]>=30);raw[17]=Number(packet[17]>=30);
 state.secretMask=[6,7,14,15,8,9].reduce((value,index,bit)=>value|(raw[index]?1<<bit:0),0);
 const v=new DataView(config.buffer,config.byteOffset,config.byteLength),binding=i=>v.getInt16(i*2,true),pressed=code=>code>=0&&Boolean(raw[code]),shot=binding(0),focus=binding(2),bomb=binding(1);
 if(pressed(shot))mask|=1;
 if(shot!==focus){if(pressed(focus))mask|=4;}
 else if(pressed(shot)){if(state.focusClock<16)state.focusClock=(state.focusClock+1)&0xffff;if(state.focusClock>=8)mask|=4;}
 else state.focusClock=state.focusClock>8?(state.focusClock-8)&0xffff:0;
 if(pressed(bomb))mask|=2;if(pressed(binding(3)))mask|=8;if(pressed(shot))mask|=0x8000;
 const confirm=config[22]?13:12,cancel=config[22]?12:13;
 if(raw[cancel])mask|=0x200;if(raw[confirm])mask|=0x100;
 if(shot!==cancel&&pressed(shot))mask|=0x100;
 if(bomb!==confirm&&pressed(bomb))mask|=0x200;
 if(pressed(binding(4)))mask|=0x400;
 for(let i=0;i<4;i++)if(raw[i])mask|=16<<i;
 const axes=new DataView(packet.buffer,packet.byteOffset,packet.byteLength),x=axes.getInt16(18,true),y=axes.getInt16(20,true),squared=F(F(x*x)+F(y*y));
 if(squared>100000000){
  const angle=F(atan2(y,x)),absolute=Math.abs(angle),extra=gameState===2&&!paused&&!gameOver&&!spellResultVisible?F(0.30543264746665955):0,low=F(F(0.7853981852531433)-extra),high=F(F(2.356194496154785)+extra);
  if(absolute<=F(extra+F(0.7853981852531433)))mask|=0x80;
  if(absolute>=F(F(2.356194496154785)-extra))mask|=0x40;
  if(angle>=low&&angle<=high)mask|=0x10;
  if(angle>=-high&&angle<=-low)mask|=0x20;
 }
 return mask;
}
