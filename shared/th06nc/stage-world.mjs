import {cancelTimeoutProjectiles,cancelBossProjectiles} from './projectile-cancel.mjs';
import {clearProjectiles,clearProjectilesWithScore} from './projectile-clear.mjs';
import {EnemyWorld} from './enemy-world.mjs';
import {EffectPool} from './effect-pool.mjs';
import {LaserPool} from './laser-pool.mjs';
import {BulletPool} from './bullet-pool.mjs';
import {ItemPool} from './item-pool.mjs';
import {ScorePopupPool} from './score-popup-pool.mjs';
import {advanceScorePopups} from './score-popup-update.mjs';
import {MessageState} from './message-state.mjs';
import {initializeStd} from './std-state.mjs';
import {advanceStd} from './std-update.mjs';
import {drawStdPass} from './std-pass.mjs';
import {ScreenShakePool} from './screen-shake.mjs';
import {queryPlayerBombCancel} from './player-bomb-cancel.mjs';
import {collidePlayerWithLaser} from './player-laser-contact.mjs';
import {collidePlayerWithBullet} from './player-bullet-contact.mjs';
import {queryPlayerDamage} from './player-damage.mjs';
import {prepareSpellPracticeBackground} from './spell-practice-background.mjs';
// Native task priorities: player 7, enemies 9, effects 10, projectiles 11.
// Items precede bullet/laser motion inside priority 11.
export class StageWorld {
 constructor(program,{anmBank,environment={},observeEffect=null,messageProgram=null,stdProgram=null,...services}={}){
  services.soundSlots??=[-1,-1,-1];
  this.environment=environment;
  this.screenShake=new ScreenShakePool(environment);this.bombCaption=null;
  this.background=stdProgram?initializeStd(stdProgram,{anmBank}):null;
  this.backgroundPaused=services.backgroundPaused??(()=>Boolean(environment.backgroundPaused));
  this.backgroundServices={setFogColor:services.setFogColor,setFogRange:services.setFogRange};
  this.spellBackgroundPreparation=environment.spellPractice&&this.background?prepareSpellPracticeBackground(this.background,program,services.spellPracticeTable,environment,this.backgroundServices):null;
  if(this.background)services.spellBackground=this.background;
  this.effects=new EffectPool({anmBank,rng:environment.rng,sin:services.sin??Math.sin,cos:services.cos??Math.cos});
  const spawnEffect=request=>{observeEffect?.(request);return this.effects.spawn(request);};this.player=services.player??null;
  if(this.player?.v)Object.defineProperty(environment,'grazeCountersDisabled',{enumerable:true,configurable:true,get:()=>Boolean(this.player.v.getUint8(0x9ec8))});
  this.previousInput=0;
  this.popups=new ScorePopupPool();
  this.popupSuspended=services.popupSuspended??(()=>Boolean(environment.popupUiActive||environment.gameOverRequested||environment.hideDuringRespawn));
  this.items=services.dropItem?null:new ItemPool({anmBank,environment});
  const dropItem=services.dropItem??(request=>{services.observeItem?.(request);return this.items.spawn(request);}),spawnPointItem=services.spawnPointItem??(request=>{services.observePointItem?.(request);return this.items.spawn({...request,type:1,mode:0});});
  if(this.items){services.dropItem=dropItem;services.spawnPointItem=spawnPointItem;services.spawnCancelItem??=request=>this.items.spawnPoint(request);}
  this.bullets=services.fireBullets?null:new BulletPool({anmBank,environment,sin:services.sin??Math.sin,cos:services.cos??Math.cos,atan2:services.atan2??Math.atan2,soundSlots:services.soundSlots,soundDisabled:services.soundDisabled});
  if(this.player?.v)services.queryBulletCancel??=query=>queryPlayerBombCancel(this.player,query);
  this.bulletOptions={player:this.player,queryCancel:services.queryBulletCancel,collision:services.bulletCollision??(this.player?query=>collidePlayerWithBullet(query,{player:this.player,environment,queryCancel:services.queryBulletCancel,spawnEffect,soundSlots:this.enemies.services.soundSlots,soundDisabled:services.soundDisabled}):null),spawnEffect,spawnCancelItem:services.spawnCancelItem};
  this.lasers=new LaserPool({anmBank,environment,atan2:services.atan2??Math.atan2});
  if(this.items&&this.bullets){
   services.cancelBullets??=request=>{const pools={bullets:this.bullets.storage,lasers:this.lasers.storage.subarray(0,64*0x298),itemPool:this.items,sin:services.sin??Math.sin,cos:services.cos??Math.cos};return request.convert?clearProjectilesWithScore({...pools,items:true,popups:this.popups,environment,bossState:this.enemies.bossState}):clearProjectiles({...pools,items:Boolean(request.items)});};
   services.cancelBossProjectiles??=pools=>cancelBossProjectiles({...pools,publishScore:request=>this.popups.publish(request)});
  }
  this.laserCollision=services.laserCollision??(this.player?query=>{services.observeLaserCollision?.(query);return collidePlayerWithLaser(query,{player:this.player,environment,spawnEffect,soundSlots:this.enemies.services.soundSlots,soundDisabled:services.soundDisabled,sin:services.sin??Math.sin,cos:services.cos??Math.cos});}:null);
  const position=entry=>Array.from({length:3},(_,i)=>entry.v.getFloat32(0xb0+i*4,true));
  const cancelTimeout=services.cancelTimeoutProjectiles??(this.bullets?()=>cancelTimeoutProjectiles({bullets:this.bullets.storage,lasers:this.lasers.storage.subarray(0,64*0x298)}):undefined);
  this.message=services.messageState??(messageProgram?new MessageState(messageProgram,{anmBank,environment}):null);this.advanceHud=services.advanceHud??null;
  if(this.message){if(!anmBank.scripts.has(0x785)||!anmBank.scripts.has(0x731))throw Error('TH06nc: message frame/text ANM missing');this.message.rebind(0x3b60,0x785);services.openMessage??=id=>{services.observeMessage?.(id);return this.message.open(id,{cancelProjectiles:cancelTimeout,loadAnm:services.loadMessageAnm});};}
  this.audioRequests=[];this.achievementRequests=[];
  this.messageServices={publishText:services.publishMessageText,localization:services.localization,musicTracks:services.musicTracks,playMusic:services.playMusic??(request=>this.audioRequests.push({kind:'playMusic',...request})),stopMusic:services.stopMusic??(request=>this.audioRequests.push({kind:'stopMusic',...request})),releaseMusic:services.releaseMusic??(request=>this.audioRequests.push({kind:'releaseMusic',...request})),awardAchievement:services.awardAchievement??(key=>this.achievementRequests.push({kind:'award',key})),commitAchievements:services.commitAchievements??(()=>this.achievementRequests.push({kind:'commit'})),getExtraCaptures:()=>this.enemies.spellState.extraCaptures};
  services.bulletPool??=this.bullets;
  services.writePlayerPosition??=(axis,value)=>{if(this.player?.v)this.player.v.setFloat32(0x7730+axis*4,value,true);};
  this.enemies=new EnemyWorld(program,{anmBank,environment,...services,bodyCollision:services.bodyCollision??(this.player?(entry,size)=>collidePlayerWithBullet({position:position(entry),size,circle:false},{player:this.player,environment,queryCancel:services.queryBulletCancel,spawnEffect,soundSlots:services.soundSlots,soundDisabled:services.soundDisabled}):null),damageQuery:services.damageQuery??(this.player?.bytes?entry=>queryPlayerDamage(this.player,{position:position(entry),size:Array.from({length:3},(_,i)=>entry.v.getFloat32(0x2c0+i*4,true))},{spawnEffect}):null),cancelTimeoutProjectiles:cancelTimeout,fireBullets:services.fireBullets??((enemy,descriptor)=>{services.observeBullet?.(enemy,descriptor);return this.bullets.spawn(descriptor);}),spawnLaser:descriptor=>this.lasers.spawn(descriptor),cancelBossProjectiles:()=>{if(!services.cancelBossProjectiles)throw Error('TH06nc: boss projectile cancellation service missing');return services.cancelBossProjectiles({bullets:this.bullets?.storage,lasers:this.lasers.storage.subarray(0,64*0x298)});},spawnEffect});
  this.playerServices={bounds:services.playerBounds,dropItem:this.items?request=>{services.observeItem?.(request);return this.items.spawn({...request,mode:2});}:dropItem,cancelProjectiles:cancelTimeout,soundSlots:services.soundSlots,soundDisabled:services.soundDisabled,sin:services.sin??Math.sin,cos:services.cos??Math.cos};
  Object.assign(this.playerServices,{spawnEffect,itemPool:this.items,publishBombName:services.publishBombName??(request=>{this.bombCaption={...request,text:services.localization?.[request.key]??request.key};}),finishBombName:services.finishBombName??(()=>{if(this.message)this.message.v.setUint16(0x7a2,1,true);this.bombCaption=null;}),screenEffect:services.screenEffect??(request=>this.screenShake.spawn(request)),awardAchievement:this.messageServices.awardAchievement,commitAchievements:this.messageServices.commitAchievements});
  this.itemServices={player:this.player,popups:this.popups,cancelBullets:services.cancelBullets,soundSlots:services.soundSlots,soundDisabled:services.soundDisabled,sin:services.sin??Math.sin,cos:services.cos??Math.cos,atan2:services.atan2??Math.atan2};
 }
 tick(input=0){
  const previousInput=this.previousInput;
  advanceScorePopups(this.popups,{suspended:this.popupSuspended()});
  const background=this.background?advanceStd(this.background,{paused:Boolean(this.environment.timeStop)||this.backgroundPaused(),...this.backgroundServices}):null;
  if(this.player?.tick){this.player.tick(input,{...this.playerServices,previousInput:this.previousInput,freeze:Boolean(this.environment.timeStop),messageField:this.environment.messageField36b0??-1});this.environment.aimTarget=Array.from({length:3},(_,i)=>this.player.v.getFloat32(0x7740+i*4,true));}this.previousInput=input;
  if(this.player)this.environment.playerPosition=this.player.position;
  const enemies=this.enemies.tick();if(this.player?.bytes&&this.environment.aimTarget)this.environment.aimTarget.forEach((x,i)=>this.player.v.setFloat32(0x7740+i*4,x,true));
  const effects=this.effects.tick(),frozen=Boolean(this.environment.timeStop),items=frozen?null:this.items?.tick(this.itemServices)??0,bullets=frozen?null:this.bullets?.tick(this.bulletOptions)??0,lasers=frozen?null:this.lasers.tick({collision:this.laserCollision});
  if(!this.environment.timeStop)this.advanceHud?.();
  const message=this.message&&!this.environment.messageTaskSuspended&&!this.environment.timeStop?this.message.tick(input,{previousInput,...this.messageServices}):null;this.screenShake.tick();return {background,enemies,effects,items,bullets,lasers,message};
 }
 drawBackground(pass,services={}){return this.background?drawStdPass(this.background,pass,{hideBase:Boolean(this.message&&this.message.v.getInt16(0x34,true)>=0&&(this.message.v.getUint32(0xc4,true)&0x4000)),...services}):0;}
}
