import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {queueSound} from './sound-queue.mjs';
const F=Math.fround,emptyBank=new AnmBank();
export const pauseAsset={archive:'th06IN.dat',file:'intext.anm',slot:53,base:0x76b};
const resume=['EXE_PAUSE_RESUME',0],title=['EXE_PAUSE_RETURN_TITLE',6],restart=['EXE_PAUSE_RESTART_GAME',1];
export function pauseEntries({replayPlayback=false,spellPractice=false,practice=false}={}){
 return replayPlayback?[resume,['EXE_PAUSE_RETURN_REPLAY_SELECT',4],title,['EXE_PAUSE_REPLAY_AGAIN',3]]:spellPractice?[resume,['EXE_SPELL_PRACTICE_RETURN_SPELL_SELECT',5],title,restart]:practice?[resume,['EXE_PAUSE_RETURN_STAGE_SELECT',2],title,restart]:[resume,title,restart];
}
// ASCII manager's pause owner at +52d0, normal update a120 and draw aee0.
// Screenshot capture is a separate optional owner; this owner uses live ANMs.
export class PauseMenu {
 constructor(bank,{environment={},publishText=null,localization={},soundSlots=[-1,-1,-1],soundDisabled=false,fade=null,musicHandle=-1,musicPaused=false}={}){
  this.bank=bank;this.environment=environment;this.publishText=publishText;this.localization=localization;this.sounds=soundSlots;this.soundDisabled=soundDisabled;this.fade=fade;this.musicHandle=musicHandle;this.musicPaused=musicPaused;
  this.bytes=new Uint8Array(0xda0);this.v=new DataView(this.bytes.buffer);this.vms=new Map();this.active=true;this.event=null;
 }
 get state(){return this.v.getInt32(0xd94,true);}set state(x){this.v.setInt32(0xd94,x,true);}
 get selection(){return this.v.getInt32(0xb44,true);}set selection(x){this.v.setInt32(0xb44,x,true);}
 get clock(){return this.v.getInt32(0xb4c,true);}set clock(x){this.v.setInt32(0xb4c,x,true);}
 vm(offset){if(!this.vms.has(offset)){const id=this.v.getUint16(offset+0x38,true),vm=this.bank.createVm(id,{allowMissing:true,resolveSprite:id=>this.bank.sprites.get(id)});vm.state=this.bytes.subarray(offset,offset+288);vm.v=new DataView(this.bytes.buffer,offset,288);const binding=this.v.getBigUint64(offset+0x100,true);vm.boundBinding=binding?this.bank.sprites.get(Number(binding)-1):undefined;this.vms.set(offset,vm);}return this.vms.get(offset);}
 bind(offset,id){const vm=rebindAnm(this.bank,id,this.bytes.subarray(offset,offset+288));this.vms.set(offset,vm);return vm;}
 interrupt(offset,id){this.v.setInt16(offset+0x8a,id,true);}
 sound(id){if(!this.soundDisabled)queueSound(this.sounds,id);}
 labels(){
  const entries=pauseEntries(this.environment),step=entries.length===3?32:30,top=F(250-F(F(F(entries.length-1)*F(32))*F(.5)));
  entries.forEach(([key],index)=>{
   const offset=(index+6)*288,id=this.v.getUint16(offset+0x38,true),vm=rebindAnm(emptyBank,id,this.bytes.subarray(offset,offset+288),{resolveSprite:id=>this.bank.sprites.get(id)});this.vms.set(offset,vm);vm.bindSprite(0x740+index);vm.v.setInt32(0xb4,-1,true);vm.v.setUint16(0x108,0xf0f,true);
   const colors=index===this.selection?[0xc0e0ff,0x302080,0x10101,0x40202]:[0xffffff,0,0x10101,0x40202];this.publishText?.(vm,{key,text:this.localization[key]??key,colors});
   vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x400)|0x300,true);vm.v.setFloat32(0xc8,192,true);vm.v.setFloat32(0xcc,F(F(F(index)*F(step))+top),true);vm.v.setFloat32(0xd0,0,true);
  });
 }
 hide(){for(const p of [0,0x120,0x240,0x360,0x480,0x5a0,0xc70])this.v.setUint32(p+0xc4,this.v.getUint32(p+0xc4,true)&~1,true);}
 exitInterrupts(){for(let p=0;p<6*288;p+=288)if(this.v.getUint8(p+0xc4)&1)this.interrupt(p,2);this.interrupt(0xc70,2);this.v.setUint8(0xd90,0);this.clock=0;}
 tick({held=0,previous=0}={}){
  this.event=null;const v=this.v,edge=bit=>(held&bit)!==0&&(previous&bit)!==(held&bit),entries=pauseEntries(this.environment);
  if(![2,5,6,7].includes(this.state)){
   if(edge(0x4000)){this.sound(10);this.state=7;this.exitInterrupts();}
   else if(edge(0x800)){this.sound(10);this.state=5;this.exitInterrupts();}
   else if(edge(0x400)){this.sound(11);this.state=2;this.exitInterrupts();this.interrupt(0xb50,1);}
  }
  switch(this.state){
   case 0:
    for(const [offset,id]of [[0,0x76b],[0x360,0x76e],[0x480,0x76f],[0x5a0,0x770]])this.bind(offset,id);
    this.selection=0;this.labels();v.setInt32(0xb40,0,true);v.setUint8(0xb48,0);this.interrupt(0,1);this.bind(0xc70,0x773);this.interrupt(0xc70,1);this.state=1;this.clock=0;break;
   case 1:{
    if(this.clock<4)break;const old=this.selection;
    if(edge(16))this.selection=(this.selection+entries.length-1)%entries.length;
    if(edge(32))this.selection=(this.selection+1)%entries.length;
    if(this.selection!==old){this.sound(12);this.labels();}
    if(!edge(256))break;
    const command=entries[this.selection][1];this.sound(command===0?11:10);this.interrupt(0,2);
    if(command===0){this.state=2;this.interrupt(0xb50,1);}
    else if([1,2,5].includes(command)){for(const p of [0x360,0x480,0x5a0])this.interrupt(p,1);this.state=4;}
    else if(command===3)this.state=7;
    else if(command===4)this.state=5;
    else if(command===6){if(this.environment.replayPlayback){v.setUint8(0xb48,1);this.state=5;}else{for(const p of [0x360,0x480,0x5a0])this.interrupt(p,1);this.state=4;}}
    if(this.state===4){for(const p of [0x480,0x5a0]){v.setUint32(p+0xec,0xffffffff,true);v.setFloat32(p+0xe4,1,true);v.setFloat32(p+0xe8,1,true);}for(const [p,xy]of [[0x480,0],[0x5a0,-4]]){v.setFloat32(p+0x18,xy,true);v.setFloat32(p+0x1c,xy,true);v.setInt32(p+0x20,0,true);}this.interrupt(0,3);this.interrupt(0x360,4);this.clock=0;}
    else{if([2,5,7].includes(this.state)){this.interrupt(0xc70,2);v.setUint8(0xd90,0);}this.clock=0;}
    break;
   }
   case 2:
    if(this.clock>=20){this.state=0;this.active=false;this.hide();if(!this.environment.spellPractice&&this.musicHandle!==-1)this.event={kind:'resumeMusic',handle:this.musicHandle,mode:this.musicPaused?3:1};}break;
   case 3:case 4:{
    const yes=this.state===3;
    for(const p of [0x480,0x5a0]){v.setFloat32(p+0xe4,1,true);v.setFloat32(p+0xe8,1,true);const xy=(p===0x480)===yes?-4:0;v.setFloat32(p+0x18,xy,true);v.setFloat32(p+0x1c,xy,true);v.setInt32(p+0x20,0,true);}
    if(this.clock<4)break;
    if(edge(16)||edge(32)||(yes&&edge(512))){this.sound(yes&&edge(512)?11:12);this.state=yes?4:3;}
    if(yes&&edge(256)){
     this.sound(10);for(const p of [0x360,0x480,0x5a0,0xc70])this.interrupt(p,2);v.setUint8(0xd90,0);const command=entries[this.selection][1];if(command!==1)v.setUint8(0xb48,Number(command===6));this.state=command===1?7:5;this.clock=0;
    }else if(!yes&&(edge(256)||edge(512))){this.sound(11);this.interrupt(0x480,2);this.interrupt(0x5a0,2);this.interrupt(0,4);this.interrupt(0x360,3);this.state=1;this.clock=0;}
    break;
   }
   case 5:if(this.clock>=20){this.fade?.requestOut(0,30);this.state=6;this.clock=0;}break;
   case 6:if(this.fade?.mode===2){this.state=0;this.active=false;this.hide();this.event={kind:'returnTitle',command:entries[this.selection][1]};}break;
   case 7:if(this.clock>=20){this.state=0;this.active=false;this.hide();this.event={kind:'restart'};}break;
  }
  let transition=v.getInt32(0xb40,true);if(this.state===1){if(transition<12)transition++;}else if(transition>0)transition--;v.setInt32(0xb40,transition,true);
  for(const p of [0,0x120,0x240,0x360,0x480,0x5a0,0xc70])this.vm(p).tick();this.clock=(this.clock+1)|0;return this.event;
 }
 draw(draw){
  const v=this.v,pulse=()=>{const x=this.clock%72;return (x<30?128+Math.trunc(x*127/30):x<42?255:128+Math.trunc((72-x)*127/30))&255;},emit=(offset,change=null)=>{const vm=this.vm(offset);if(!(vm.v.getUint8(0xc4)&1))return;const before=vm.state.slice();try{change?.(vm.v);draw(vm,{snap:true,space:'screen',part:'pause',offset});}finally{vm.state.set(before);}};
  emit(0xc70);
  for(let i=0;i<6;i++)emit(i*288,a=>{if(i<4)a.setFloat32(0x1c,F(a.getFloat32(0x1c,true)+F(-11.11111068725586)),true);else{const selected=(i===4)===([3,5,6,7].includes(this.state)),alpha=Math.trunc((selected?pulse():166)*a.getUint8(0xef)/255);a.setFloat32(0xcc,F(a.getFloat32(0xcc,true)-F(5.333333492279053)),true);if(i===5)a.setFloat32(0xcc,F(a.getFloat32(0xcc,true)-F(8.88888931274414)),true);a.setUint32(0xec,((alpha<<24)|(selected?0xffc0c0:0x808080))>>>0,true);}});
  const transition=v.getInt32(0xb40,true);if(transition<=0)return;
  pauseEntries(this.environment).forEach((_,i)=>{const offset=(i+6)*288,a=this.vm(offset).v,selected=i===this.selection,alpha=Math.trunc(Math.trunc(transition*255/12)*(selected?pulse():166)/255);a.setUint32(0xec,((alpha<<24)|(selected?0xffffff:0x808080))>>>0,true);const y=F(F(F(F(12-transition)*F(-3))/F(12))-(selected?F(4):F(0)));a.setFloat32(0x18,selected&&!this.environment.spellPractice?-4:0,true);a.setFloat32(0x1c,F(y-F(11.11111068725586)),true);a.setFloat32(0x20,0,true);draw(this.vm(offset),{snap:true,space:'screen',part:'pause',offset});});
 }
}
