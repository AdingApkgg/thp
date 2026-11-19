import {drawHudNotifications} from '../../shared/th06nc/hud-notifications.mjs';
import {drawReplayIndicator} from '../../shared/th06nc/replay-indicator.mjs';
import {drawSpellNameText} from '../../shared/th06nc/hud-spell-name.mjs';
import {drawEnemyLifeHud} from '../../shared/th06nc/hud-enemy-life-draw.mjs';
import {drawHudPower} from '../../shared/th06nc/hud-power.mjs';
import {createAsciiTextState,enqueueAsciiText,drawAsciiText} from '../../shared/th06nc/ascii-text.mjs';
import {drawHudLabels} from '../../shared/th06nc/hud-labels.mjs';
import {drawHudNumbers} from '../../shared/th06nc/hud-numbers.mjs';
import {drawHudStock} from '../../shared/th06nc/hud-stock.mjs';
import {drawHudBackground} from '../../shared/th06nc/hud-background.mjs';
import {AnmRendererGl} from '../../shared/th06nc/anm-renderer-gl.mjs';
import {StdRendererGl} from '../../shared/th06nc/std-renderer-gl.mjs';
import {createStdCamera} from '../../shared/th06nc/std-camera.mjs';
import {drawStdLayer} from '../../shared/th06nc/std-draw.mjs';
import {anmWorldQuad} from '../../shared/th06nc/anm-world-quad.mjs';
import {multiplyMatrix,transformCoordinate} from '../../shared/th06nc/matrix.mjs';
import {drawPlayer} from '../../shared/th06nc/player-draw.mjs';
import {drawPlayerBomb} from '../../shared/th06nc/player-bomb.mjs';
import {drawEffects} from '../../shared/th06nc/effect-draw.mjs';
import {drawBullets} from '../../shared/th06nc/bullet-draw.mjs';
import {drawLasers} from '../../shared/th06nc/laser-draw.mjs';
import {drawItems} from '../../shared/th06nc/item-draw.mjs';
import {drawMessage} from '../../shared/th06nc/message-draw.mjs';
import {drawHudPortraits,drawBombNameText} from '../../shared/th06nc/hud-bomb-name.mjs';
import {createScorePopupFont,drawScorePopups} from '../../shared/th06nc/score-popup-draw.mjs';
const F=Math.fround;
export class GameRenderer {
 constructor(gl,assets){
  this.gl=gl;this.assets=assets;this.screen=new AnmRendererGl(gl);this.world=new StdRendererGl(gl);this.viewport={x:236,y:16,width:384,height:448,minZ:.5,maxZ:1};this.drawCalls=0;
  this.white=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.white);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
  this.fullQuad=new Float32Array([0,0,0,0,gl.canvas.width,0,1,0,0,gl.canvas.height,0,1,gl.canvas.width,gl.canvas.height,1,1]);
 }
 clear(color=[0,0,0]){const gl=this.gl;gl.viewport(0,0,gl.canvas.width,gl.canvas.height);gl.disable(gl.SCISSOR_TEST);gl.depthMask(true);gl.clearDepth(1);gl.clearColor(...color.map(n=>n/255),1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);this.drawCalls=0;}
 flat(vm,options){if((vm.v.getUint32(0xc4,true)&3)!==3||!vm.v.getUint32(0xec,true)||!vm.pointer(0x100)||vm.boundBinding?.active===false)return;this.gl.viewport(0,0,this.gl.canvas.width,this.gl.canvas.height);this.gl.disable(this.gl.DEPTH_TEST);const texture=this.assets.vmTexture(vm);if(!texture)throw Error('TH06nc: drawable texture missing: '+(vm.boundResource??vm.resource)?.textureName);this.drawCalls+=Number(this.screen.draw(vm,texture,options));}
 cover(color){this.gl.disable(this.gl.DEPTH_TEST);this.screen.drawQuad(this.fullQuad,this.white,color);}
 replayIndicator(playback){drawReplayIndicator(playback,(vm,options)=>this.flat(vm,options),{setupCamera:r=>this.gl.depthRange(r.minZ,r.maxZ)});}
 title(scene){this.clear(scene.state.backgroundEnabled!==false?[255,255,255]:[0,0,0]);let fade=null;scene.draw((vm,options)=>this.flat(vm,options),name=>this.screen.drawQuad(this.fullQuad,this.assets.textures.get(name)),color=>{fade=color;},{width:this.gl.canvas.width,height:this.gl.canvas.height});if(scene.ascii)drawAsciiText(scene.ascii,(vm,options)=>this.flat(vm,options));if(fade!==null)this.cover(fade);}
 credits(scene){this.clear();scene.draw((vm,options)=>this.flat(vm,options),({color})=>this.screen.drawQuad(this.fullQuad,this.assets.textures.get('credit'),color));drawAsciiText(scene.ascii,(vm,options)=>this.flat(vm,options));if(scene.fade.mode)this.cover(((scene.fade.alpha&255)<<24)|scene.fade.color);}
 result(scene){this.clear();scene.draw((vm,options)=>this.flat(vm,options));scene.textRequests=scene.ascii.v.getInt32(0x7bb0,true);drawAsciiText(scene.ascii,(vm,options)=>this.flat(vm,options));if(scene.fade.mode)this.cover(((scene.fade.alpha&255)<<24)|scene.fade.color);}
 ending(scene){
  this.clear();const gl=this.gl,viewport={x:0,y:0,width:gl.canvas.width,height:gl.canvas.height};scene.draw({primary:scene.backgroundName?1:-1,alternate:-1,useAlternate:false,viewport},{textureSize:()=>this.assets.endingTextures.get(scene.backgroundName),drawBackground:r=>{const metadata=this.assets.endingTextures.get(scene.backgroundName),[x,y,w,h]=r.source,u0=x/metadata.width,v0=y/metadata.height,u1=(x+w)/metadata.width,v1=(y+h)/metadata.height,quad=new Float32Array([r.left,r.top,u0,v0,r.right,r.top,u1,v0,r.left,r.bottom,u0,v1,r.right,r.bottom,u1,v1]);this.screen.drawQuad(quad,this.assets.textures.get(scene.backgroundName));this.drawCalls++;},drawVm:(vm,options)=>this.flat(vm,options),drawFade:r=>this.cover(r.color)});
 }
 pause(menu){
  const gl=this.gl,v=this.viewport,scale=gl.canvas.height/480;gl.enable(gl.SCISSOR_TEST);gl.scissor(Math.round(v.x*scale),Math.round((480-v.y-v.height)*scale),Math.round(v.width*scale),Math.round(v.height*scale));this.pauseDrawRequests=0;
  try{menu.draw((vm,options)=>{const x=vm.v.getFloat32(0xc8,true),y=vm.v.getFloat32(0xcc,true);vm.v.setFloat32(0xc8,F(x+v.x),true);vm.v.setFloat32(0xcc,F(y+v.y),true);try{this.pauseDrawRequests++;this.flat(vm,options);}finally{vm.v.setFloat32(0xc8,x,true);vm.v.setFloat32(0xcc,y,true);}});}finally{gl.disable(gl.SCISSOR_TEST);}
 }
 bindStage(stage){this.popupFont=createScorePopupFont(stage.enemies.pool.anmBank);this.ascii=createAsciiTextState(stage.enemies.pool.anmBank);}
 // Actor world geometry is projected through the gameplay camera, preserving
 // nonzero Z and three-axis rotations. GPU depth/fog equivalence is still open.
 actorWorld(vm){
  const raw=anmWorldQuad(vm);if(!raw)return;const camera=createStdCamera(),matrix=multiplyMatrix(camera.view,camera.projection),quad=new Float32Array(16),scale=this.gl.canvas.height/480,v=this.viewport;
  for(let i=0;i<4;i++){const p=transformCoordinate(Array.from(raw.subarray(i*5,i*5+3)),matrix);quad.set([(v.x+(p[0]+1)*v.width*.5)*scale,(v.y+(1-p[1])*v.height*.5)*scale,raw[i*5+3],raw[i*5+4]],i*4);}
  const texture=this.assets.vmTexture(vm);if(texture){this.gl.viewport(0,0,this.gl.canvas.width,this.gl.canvas.height);this.gl.disable(this.gl.DEPTH_TEST);this.drawCalls+=Number(this.screen.drawQuad(quad,texture,vm.v.getUint32(0xec,true),{additive:Boolean(vm.v.getUint32(0xc4,true)&4)}));}
 }
 stage(stage){
  if(stage.screenShake){const [x,y,width,height]=stage.screenShake.viewport;Object.assign(this.viewport,{x,y,width,height});}
  const gl=this.gl,bg=stage.background,v=bg.v,viewport=this.viewport,scale=gl.canvas.height/480,camera=createStdCamera({direction:bg.direction??[0,0,1]}),fogColor=[v.getUint8(0x42),v.getUint8(0x41),v.getUint8(0x40)],fogRange=[v.getFloat32(0x44,true),v.getFloat32(0x48,true)],clip=()=>{gl.enable(gl.SCISSOR_TEST);gl.scissor(viewport.x*scale,gl.canvas.height-(viewport.y+viewport.height)*scale,viewport.width*scale,viewport.height*scale);};this.clear();
  const services={setupCamera:r=>gl.depthRange(r.minZ,r.maxZ),renderState:r=>{if(r.name==='depthTest')r.value?gl.enable(gl.DEPTH_TEST):gl.disable(gl.DEPTH_TEST);else if(r.name==='depthWrite')gl.depthMask(Boolean(r.value));},drawLayer:layer=>drawStdLayer(bg,layer,(vm,options)=>{if(options.space==='world'){gl.viewport(viewport.x*scale,gl.canvas.height-(viewport.y+viewport.height)*scale,viewport.width*scale,viewport.height*scale);this.drawCalls+=Number(this.world.draw(vm,this.assets.vmTexture(vm),{...camera,fogColor,fogRange}));}else this.flat(vm,options);},{...camera,viewport}),drawCover:({rect,color})=>{gl.viewport(0,0,gl.canvas.width,gl.canvas.height);gl.disable(gl.DEPTH_TEST);const [x0,y0,x1,y1]=rect.map(n=>n*scale);this.screen.drawQuad(new Float32Array([x0,y0,0,0,x1,y0,1,0,x0,y1,0,1,x1,y1,1,1]),this.white,color);},drawOverlay:(vm,options)=>{const x=vm.v.getFloat32(0xc8,true),y=vm.v.getFloat32(0xcc,true);vm.v.setFloat32(0xc8,F(x+viewport.x),true);vm.v.setFloat32(0xcc,F(y+viewport.y),true);clip();try{this.flat(vm,options);}finally{vm.v.setFloat32(0xc8,x,true);vm.v.setFloat32(0xcc,y,true);gl.disable(gl.SCISSOR_TEST);}}};
  if(stage.advanceHud)drawHudBackground(stage.message,(vm,options)=>this.flat(vm,options),{setupCamera:r=>gl.depthRange(r.minZ,r.maxZ),drawCover:services.drawCover,hidden:Boolean(stage.environment?.hudBackgroundHidden),color:stage.environment?.hudBackgroundColor??0});
  stage.drawBackground(0,services);stage.drawBackground(1,services);gl.depthRange(0,.5);clip();const offset={worldOffset:[viewport.x,viewport.y]},draw=(vm,options)=>options?.space==='world'?this.actorWorld(vm):this.flat(vm,options);
  if(stage.advanceHud)drawHudPortraits(stage.message,draw,offset);
  this.playerDrawRequests=0;drawPlayer(stage.player,(vm,options)=>{if(options.part==='player')this.playerDrawRequests++;draw(vm,options);},{...offset,drawBomb:(player,draw)=>drawPlayerBomb(player,(vm,options)=>{const x=vm.v.getFloat32(0xc8,true),y=vm.v.getFloat32(0xcc,true);vm.v.setFloat32(0xc8,F(x+viewport.x),true);vm.v.setFloat32(0xcc,F(y+viewport.y),true);try{draw(vm,options);}finally{vm.v.setFloat32(0xc8,x,true);vm.v.setFloat32(0xcc,y,true);}})});stage.enemies.draw(draw,offset);drawEffects(stage.effects,vm=>this.actorWorld(vm));
  drawLasers(stage.lasers,(vm,options)=>{if(options.space==='world')this.actorWorld(vm);else{const x=vm.v.getFloat32(0xc8,true),y=vm.v.getFloat32(0xcc,true);vm.v.setFloat32(0xc8,F(x+viewport.x),true);vm.v.setFloat32(0xcc,F(y+viewport.y),true);try{this.flat(vm,options);}finally{vm.v.setFloat32(0xc8,x,true);vm.v.setFloat32(0xcc,y,true);}}});drawItems(stage.items,draw,offset);drawBullets(stage.bullets,draw,offset);drawScorePopups(stage.popups,this.popupFont,draw,{anmBank:stage.enemies.pool.anmBank,...offset});gl.disable(gl.SCISSOR_TEST);drawMessage(stage.message,draw,offset);if(stage.advanceHud){drawBombNameText(stage.message,draw,offset);drawSpellNameText(stage.message,draw,offset);this.stockDrawRequests=0;this.labelDrawRequests=0;this.numberDrawRequests=0;this.asciiDrawRequests=0;this.powerDrawRequests=0;this.enemyLifeDrawRequests=0;this.notificationDrawRequests=0;const env=stage.environment,number=request=>{this.numberDrawRequests++;enqueueAsciiText(this.ascii,{...request,text:request.text??String(request.value)});};drawEnemyLifeHud(stage.message,stage.enemies.bossState,(vm,options)=>{this.enemyLifeDrawRequests++;draw(vm,options);},{entry:stage.enemies.bossSlots[0],program:stage.enemies.pool.program,difficulty:env.difficulty,spellCounter:env.spellCounter,chapter:stage.enemies.chapter,drawNumber:number,soundSlots:stage.enemies.services.soundSlots,soundDisabled:stage.enemies.services.soundDisabled});env.inputFlags=drawHudLabels(stage.message,(vm,options)=>{this.labelDrawRequests++;draw(vm,options);},{inputFlags:env.inputFlags??0,hidden:Boolean(env.hudBackgroundHidden)});drawHudStock(stage.message,(vm,options)=>{this.stockDrawRequests++;draw(vm,options);},{...env,drawNumber:number,force:Boolean(env.hudBackgroundHidden)});drawHudPower(stage.message,(vm,options)=>{this.powerDrawRequests++;draw(vm,options);},{...env,drawNumber:number,force:Boolean(env.hudBackgroundHidden)});env.inputFlags=drawHudNumbers(number,{...env,force:Boolean(env.hudBackgroundHidden)});drawHudNotifications(stage.message,request=>{this.notificationDrawRequests++;enqueueAsciiText(this.ascii,request);});drawAsciiText(this.ascii,(vm,options)=>{this.asciiDrawRequests++;if(options.camera)clip();try{draw(vm,options);}finally{if(options.camera)gl.disable(gl.SCISSOR_TEST);}},{setupCamera:r=>gl.depthRange(r.minZ,r.maxZ)});}gl.depthRange(0,1);
 }
}
