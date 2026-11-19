import {EndingAnimations} from './ending-animations.mjs';
import {initializeEndingScript,replaceEndingScript} from './ending-init.mjs';
import {advanceEnding} from './ending-update.mjs';
import {drawEnding} from './ending-draw.mjs';
import {markClearedCompletion} from './cleared-progress.mjs';
// Data/animation scene composition. Application registration, destruction,
// return-to-result and disk-commit ownership remain with the caller.
export class EndingScene extends EndingAnimations {
 constructor(bank,{scripts,environment,cleared,localization={},publishText,loadBackground,playMusic,fadeMusic,awardAchievement=()=>{},commitAchievements=()=>{},freeScript=()=>{},reportError=()=>{}}){
  super(bank);this.environment=environment;this.localization=localization;this.scriptTable=new Map([...scripts].map(([name,raw],index)=>[name,{raw,base:(index+1)*0x10000}]));this.textQueue=[];this.previous=0;this.active=true;this.script=null;this.scriptBase=0;this.scriptName=null;
  const v=new DataView(this.bytes.buffer);v.setInt32(0x18,8,true);v.setInt32(0x1258,-999,true);v.setInt32(0x1260,-999,true);
  this.scriptServices={loadScript:path=>{const name=path.split('/').at(-1),entry=this.scriptTable.get(name);if(!entry)return 0n;this.script=entry.raw;this.scriptBase=entry.base;this.scriptName=name;return BigInt(entry.base);},freeScript,reportError};
  const flags=markClearedCompletion(cleared,environment);v.setUint8(0x124c,Number(flags.alreadyCleared));this.restricted=flags.restricted;
  this.services={cleared,loadBackground,playMusic,fadeMusic,bindAnm:(offset,id)=>this.bind(offset,id),bindSprite:(offset,id)=>this.bindSprite(offset,id),prepareText:(offset,id)=>this.prepareText(offset,id),publishText:request=>publishText(this.vm(request.offset),{text:request.text,colors:[request.color,...request.colors]}),tickAnm:offset=>this.tick(offset),switchScript:path=>replaceEndingScript(this.bytes,path,this.scriptServices)};
  this.initialized=initializeEndingScript(this.bytes,environment,{restricted:flags.restricted,...this.scriptServices,awardAchievement,commitAchievements});if(this.initialized!==0)this.active=false;
 }
 update(held=0){if(!this.active)return 0;const result=advanceEnding(this,{held,previous:this.previous,lifeProtection:Boolean(this.environment.lifeProtection),localization:this.localization},this.services);this.previous=held;if(result===0)this.active=false;return result;}
 draw(options,{textureSize,drawBackground,drawVm,drawFade}){return drawEnding(this.bytes,options,{textureSize,drawBackground,drawVm:(offset,args)=>drawVm(this.vm(offset),{snap:true,offset,args}),drawFade});}
}
