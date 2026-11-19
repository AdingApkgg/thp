import {PauseMenu} from './pause-menu.mjs';
import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
import {spellPulseAlpha} from './spell-practice-draw-effects.mjs';
const F=Math.fround,emptyBank=new AnmBank();
export const spellResultKeys=['EXE_SPELL_PRACTICE_RETURN_SPELL_SELECT','EXE_SPELL_PRACTICE_SAVE_REPLAY','EXE_SPELL_PRACTICE_RETRY'];

// ASCII +6070 result owner, c230 update and c950 draw. The replay result
// owner is an explicit synchronous host service, prepared before creation.
export class SpellPracticeResultMenu extends PauseMenu {
 constructor(bank,{captured=false,replayServices=null,resultServices=null,...options}={}){
  super(bank,options);this.v.setUint8(0xd98,Number(Boolean(captured)));this.replayServices=replayServices;this.resultServices=resultServices;
 }
 get captured(){return Boolean(this.v.getUint8(0xd98));}
 labels(){
  spellResultKeys.forEach((key,index)=>{
   const offset=0x6c0+index*288,bytes=this.bytes.subarray(offset,offset+288),id=this.v.getUint16(offset+0x38,true),vm=rebindAnm(emptyBank,id,bytes,{resolveSprite:id=>this.bank.sprites.get(id)});
   this.vms.set(offset,vm);vm.bindSprite(0x740+index);vm.v.setInt32(0xb4,-1,true);vm.v.setUint16(0x108,0xf0f,true);
   this.publishText?.(vm,{key,text:this.localization[key]??key,colors:[0xffffff,0,0x10101,0x40202]});
   vm.v.setUint32(0xc4,(vm.v.getUint32(0xc4,true)&~0x400)|0x300,true);vm.v.setFloat32(0xc8,192,true);vm.v.setFloat32(0xcc,F(F(F(index)*F(32))+F(218)),true);vm.v.setFloat32(0xd0,0,true);
  });
 }
 recordingAvailable(){return !this.environment.replayPlayback&&Boolean(this.replayServices?.recordingAvailable);}
 tick({held=0,previous=0}={}){
  this.event=null;const v=this.v,e=this.environment,edge=bit=>Boolean(held&bit)&&((held&bit)!==(previous&bit));
  const exit=state=>{this.state=state;this.clock=0;this.interrupt(0,2);this.interrupt(0xc70,2);v.setUint8(0xd90,0);};
  const fadeIn=()=>{if(this.fade?.mode)this.fade.requestIn(this.fade.color,10);};
  switch(this.state){
   case 0:
    this.selection=this.captured?0:2;this.labels();v.setInt32(0xb40,0,true);this.bind(0,this.captured?0x775:0x776);this.interrupt(0,1);
    this.bind(0xc70,this.captured?0x774:0x777);this.interrupt(0xc70,1);this.state=1;this.clock=0;break;
   case 1:{
    if(this.clock<4)break;const old=this.selection;
    if(edge(16))this.selection=(this.selection+2)%3;if(edge(32))this.selection=(this.selection+1)%3;if(old!==this.selection)this.sound(12);
    if(edge(0x4000)){this.selection=2;this.sound(10);exit(5);break;}
    if(!edge(256))break;
    if(this.selection===0){this.sound(10);exit(4);}
    else if(this.selection===2){this.sound(10);exit(5);}
    else if(this.selection===1){if(this.recordingAvailable()){this.sound(10);this.fade?.requestOut(0,10);this.state=2;this.clock=0;}else this.sound(11);}
    break;
   }
   case 2:
    if(this.fade?.mode===2){
     const created=!this.resultServices?.present?.()&&Boolean(this.resultServices?.open?.());
     if(created){this.state=3;this.event={kind:'openReplayResult'};}
     else{fadeIn();this.state=1;}
     this.clock=0;
    }break;
   case 3:
    if(!this.resultServices?.present?.()){fadeIn();this.state=1;this.clock=0;this.labels();}break;
   case 4:case 5:{
    if(this.clock===20){this.fade?.requestOut(0,30);}
    else if(this.clock<20)break;
    if(this.fade?.mode!==2)break;
    const retry=this.state===5;this.state=0;this.active=false;e.spellResultVisible=false;
    if(retry){e.spellRestartRequested=true;e.gameState=12;this.event={kind:'restartSpellPractice'};}
    else{e.resumeSpell=true;e.gameState=1;this.event={kind:'returnSpellSelection'};}
    break;
   }
  }
  let transition=v.getInt32(0xb40,true);if(this.state===1){if(transition<12)transition++;}else if(transition>0)transition--;v.setInt32(0xb40,transition,true);
  this.vm(0).tick();this.vm(0xc70).tick();this.clock=(this.clock+1)|0;return this.event;
 }
 draw(draw){
  if(this.environment.spellResultVisible===false||this.state===0||this.state===3)return;
  const emit=(offset,adjust=null)=>{const vm=this.vm(offset);if(!(vm.v.getUint8(0xc4)&1))return;const before=vm.state.slice();try{adjust?.(vm.v);draw(vm,{snap:true,space:'screen',part:'pause',offset});}finally{vm.state.set(before);}};
  emit(0xc70);emit(0,v=>v.setFloat32(0x1c,F(v.getFloat32(0x1c,true)+F(-17.333332061767578)),true));
  const transition=this.v.getInt32(0xb40,true);if(transition<=0)return;
  for(let i=0;i<3;i++){
   const vm=this.vm(0x6c0+i*288),v=vm.v,selected=i===this.selection,disabled=i===1&&!this.recordingAvailable(),pulse=selected?spellPulseAlpha(this.clock,128):disabled?144:166;
   const alpha=Math.trunc(Math.trunc(Math.imul(transition,255)/12)*pulse/255),rgb=disabled?0x505860:selected?0xd8ecff:0x788898;
   v.setUint32(0xec,((alpha<<24)|rgb)>>>0,true);v.setFloat32(0x18,0,true);v.setFloat32(0x20,0,true);
   let y=F(F(F(12-transition)*F(-3))/F(12));if(selected)y=F(y-F(4));y=F(y-F(11.11111068725586));y=F(y-F(6.222222328186035));v.setFloat32(0x1c,y,true);
   draw(vm,{snap:true,space:'screen',part:'pause',offset:0x6c0+i*288});
  }
 }
}
