import {PauseMenu} from './pause-menu.mjs';
const F=Math.fround,U=n=>BigInt.asUintN(64,BigInt(n??0));
// ASCII manager +6070, original b4f0 update and bce0 draw. The score-entry
// owner is a separate destination, not a title-menu shortcut.
export class GameOverMenu extends PauseMenu {
 hide(){for(const p of [0,0x120,0x240,0x360,0xc70])this.v.setUint32(p+0xc4,this.v.getUint32(p+0xc4,true)&~1,true);}
 finish(kind){this.active=false;this.environment.gameOverRequested=false;this.event={kind};}
 tick({held=0,previous=0}={}){
  this.event=null;const e=this.environment,v=this.v,edge=bit=>(held&bit)!==0&&(previous&bit)!==(held&bit);
  if(e.spellPractice&&!e.replayPlayback){e.displayScore=U(e.score);e.spellPracticeResultRequested=true;this.finish('spellPracticeResult');return this.event;}
  if(e.practice){e.displayScore=U(e.score);this.finish('scoreEntry');return this.event;}
  if(e.replayPlayback){e.displayScore=U(e.score);this.finish('replaySelect');return this.event;}
  if(((e.continuesUsed??0)&255)>=3||(e.difficulty??0)>=4){e.displayScore=U(e.score);this.finish('scoreEntry');return this.event;}
  switch(this.state){
   case 0:
    if(this.clock===0){this.soundDisabled=false;for(const [p,id]of [[0,0x771],[0x120,0x772],[0x240,0x76f],[0x360,0x770]]){this.bind(p,id);this.interrupt(p,1);}for(const p of [0x240,0x360])v.setUint32(p+0xec,0xffffffff,true);this.bind(0xc70,0x773);this.interrupt(0xc70,1);}
    this.state=2;this.clock=0;break;
   case 1:case 2:{
    const yes=this.state===1;for(const p of [0x240,0x360]){v.setFloat32(p+0xe4,1,true);v.setFloat32(p+0xe8,1,true);}
    if(this.clock<(yes?4:30))break;
    if(edge(16)||edge(32)){this.sound(12);this.state=yes?2:1;}
    if(edge(256)){this.sound(yes?10:11);for(const p of [0,0x120,0x240,0x360,0xc70])this.interrupt(p,2);if(yes)this.interrupt(0xb50,1);v.setUint8(0xd90,0);this.state=yes?3:4;this.clock=0;}
    break;
   }
   case 3:
    if(this.clock>=30){
     this.state=0;this.clock=0;this.hide();const continues=((e.continuesUsed??0)+1)&255;e.continuesUsed=continues;e.scoreDisplayStep=0n;e.displayScore=BigInt(continues);e.score=BigInt(continues);e.lives=(e.defaultLives??2)&255;e.bombs=(e.defaultBombs??3)&255;e.inputFlags=(((e.inputFlags??0)&0xfffffeaa)|0x2aa)>>>0;e.totalGraze=0;e.playerPower=0;e.pointStageCount=0;e.continueState=0;this.finish('continue');return this.event;
    }break;
   case 4:
    if(this.clock===20)this.fade?.requestOut(0,30);
    if(this.clock>=20&&this.fade?.mode===2){this.state=0;this.clock=0;this.hide();e.displayScore=U(e.score);this.finish('scoreEntry');return this.event;}break;
  }
  for(const p of [0,0x120,0x240,0x360,0xc70])this.vm(p).tick();this.clock=(this.clock+1)|0;return this.event;
 }
 draw(draw){
  const v=this.v,emit=(offset,change=null,force=false)=>{const vm=this.vm(offset);if(!force&&!(vm.v.getUint8(0xc4)&1))return;const before=vm.state.slice();try{change?.(vm.v);draw(vm,{snap:true,space:'screen',part:'game-over',offset});}finally{vm.state.set(before);}},shift=a=>a.setFloat32(0x1c,F(a.getFloat32(0x1c,true)+F(-11.11111068725586)),true);
  emit(0xc70);
  if([1,2,4].includes(this.state)){
   this.bytes.copyWithin(0x480,0x120,0x240);this.vms.delete(0x480);const vm=this.vm(0x480),a=vm.v;a.setFloat32(0xc8,F(a.getFloat32(0xc8,true)+F(a.getFloat32(0xe8,true)*F(8))),true);const sprite=30-((this.environment.continuesUsed??0)&255);vm.pointer(0x100,sprite+1);vm.boundBinding=this.bank.sprites.get(sprite);emit(0x480,shift,true);
  }
  const x=this.clock%72,pulse=(x<30?128+Math.trunc(x*127/30):x<42?255:128+Math.trunc((72-x)*127/30))&255;
  for(let i=0;i<4;i++)emit(i*288,a=>{shift(a);if(i>=2){const selected=(i===2)===[1,3].includes(this.state),alpha=Math.trunc((selected?pulse:166)*a.getUint8(0xef)/255);a.setUint32(0xec,((alpha<<24)|(selected?0xffc0c0:0x808080))>>>0,true);}});
 }
}
