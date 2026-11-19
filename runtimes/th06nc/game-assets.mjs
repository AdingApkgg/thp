import {resolveLocalizedAsset} from '../../shared/th06nc/localized-asset.mjs';
import {readAnm} from '../../shared/th06nc/anm.mjs';
import {readDds} from '../../shared/th06nc/dds.mjs';
import {uploadDdsTexture} from '../../shared/th06nc/texture-gl.mjs';
import {readMessagePack} from '../../shared/th06nc/messagepack.mjs';
import {readFontAtlas} from '../../shared/th06nc/font-atlas.mjs';
import {fontKey} from '../../shared/th06nc/font-publish.mjs';
export class GameAssets {
 constructor(gl,painter){this.gl=gl;this.painter=painter;this.bytes=new Map();this.animations=new Map();this.textures=new Map();this.textureRequests=new Map();this.loadQueue=[];this.activeLoads=0;}
 async load(path){
  if(!this.bytes.has(path)){const task=new Promise((resolve,reject)=>{this.loadQueue.push({path,resolve,reject});this.pumpLoads();});this.bytes.set(path,task);task.catch(()=>{if(this.bytes.get(path)===task)this.bytes.delete(path);});}
  return this.bytes.get(path);
 }
 pumpLoads(){while(this.activeLoads<6&&this.loadQueue.length){const task=this.loadQueue.shift();this.activeLoads++;this.fetchBytes(task.path).then(task.resolve,task.reject).finally(()=>{this.activeLoads--;this.pumpLoads();});}}
 async fetchBytes(path){
  for(let attempt=0;attempt<3;attempt++)try{const response=await fetch(path);if(!response.ok)throw Error(`HTTP ${response.status}: ${path}`);return new Uint8Array(await response.arrayBuffer());}
  catch(reason){if(!(reason instanceof TypeError)||attempt===2)throw Error(`TH06nc asset ${path}: ${reason.message}`,{cause:reason});await new Promise(resolve=>setTimeout(resolve,100*(attempt+1)));}
 }
 async texture(name){
  if(this.textures.has(name))return this.textures.get(name);
  if(this.textureRequests.has(name))return this.textureRequests.get(name);
  const pending=(async()=>{
   try{
    if(!this.textureManifest){
     const request=this.load('./artifacts/textures/localized-manifest.json')
      .then(raw=>JSON.parse(new TextDecoder().decode(raw)));
     this.textureManifest=request;
     request.catch(()=>{if(this.textureManifest===request)this.textureManifest=null;});
    }
    const manifest=await this.textureManifest;
    const match=resolveLocalizedAsset(name+'.dds',[manifest],manifest.language);
    if(!match)throw Error('TH06nc texture not prepared: '+name);
    const bytes=await this.load('./artifacts/textures/'+match.name);
    const texture=uploadDdsTexture(this.gl,readDds(bytes));
    this.textures.set(name,texture);
    return texture;
   }finally{
    this.textureRequests.delete(name);
   }
  })();
  this.textureRequests.set(name,pending);
  return pending;
 }
 async animation(ref){const key=ref.archive+'/'+ref.file;if(!this.animations.has(key)){const resource=readAnm(await this.load('./artifacts/scripts/'+key));if(resource.textureName!=='@')await this.texture(resource.textureName.split('/').at(-1).replace(/\.png$/,''));this.animations.set(key,resource);}return this.animations.get(key);}
 bind(bank,ref){const resource=this.animations.get(ref.archive+'/'+ref.file);if(!resource)throw Error('TH06nc: resource not prepared: '+ref.file);bank.load(resource,ref.base,{slot:ref.slot});return resource;}
 vmTexture(vm){const resource=vm.boundResource??vm.resource;if(!resource?.textureName)return null;return resource.textureName==='@'?this.painter.texture(resource):this.textures.get(resource.textureName.split('/').at(-1).replace(/\.png$/,''));}
 async prepareEndingFonts(){
  for(const color of [0x5d9633,0x6346cd,0x646464,0xcd6946]){const key=fontKey(15,[color,0xc0d0d0,0x10101,0x40202],'zh-CN');if(this.painter.atlases.has(key))continue;const metadata=JSON.parse(new TextDecoder().decode(await this.load(`./artifacts/fonts/${key}.json`))),advance=new TextDecoder().decode(await this.load(`./artifacts/fonts/advance_${key}.txt`));this.painter.register(key,readFontAtlas(metadata,advance),readDds(await this.load(`./artifacts/fonts/${key}.dds`)));}
 }
 async prepareEndingTextures(scripts){
  this.endingTextures??=new Map(JSON.parse(new TextDecoder().decode(await this.load('./artifacts/textures/ending-manifest.json'))).map(r=>[r.file.replace(/\.dds$/,''),r]));
  const names=new Set();for(const bytes of scripts)for(const match of new TextDecoder().decode(bytes).matchAll(/(?:^|\n)@b([^\0]+)\0/g))names.add(match[1].split('/').at(-1).replace(/\.png$/,''));for(const name of names)await this.texture(name);
  for(const name of ['staff01','staff03'])this.textures.set(name,await this.texture(name+'_zh-CN'));
 }
 async prepareCreditsFonts(){
  const key=fontKey(15,[0xfffffe,0,0x10101,0x40202],'zh-CN');if(this.painter.atlases.has(key))return;const metadata=JSON.parse(new TextDecoder().decode(await this.load(`./artifacts/fonts/${key}.json`))),advance=new TextDecoder().decode(await this.load(`./artifacts/fonts/advance_${key}.txt`));this.painter.register(key,readFontAtlas(metadata,advance),readDds(await this.load(`./artifacts/fonts/${key}.dds`)));
 }
 async prepareFonts(){
  const raw=readMessagePack(await this.load('./artifacts/scripts/th06IN.dat/localization.msgpack'));this.localization=Object.fromEntries(Object.entries(raw).map(([key,value])=>[key,value['zh-CN']??key]));
  for(const [size,colors]of [[15,[0xffffff,0,0x10101,0x50505]],[15,[0xfff0f0,0,0x10101,0x50505]],[16,[0xe0ffff,0,0x10101,0x40202]],[15,[0xf0f0ff,0,0x10101,0x40202]],[15,[0xfff0f0,0,0x10101,0x40202]],[15,[0xffffff,0,0x10101,0x40202]],[15,[0xe0ffff,0,0x10101,0x40202]],[15,[0xc0e0ff,0x302080,0x10101,0x40202]]]){const key=fontKey(size,colors,'zh-CN'),metadata=JSON.parse(new TextDecoder().decode(await this.load(`./artifacts/fonts/${key}.json`))),advance=new TextDecoder().decode(await this.load(`./artifacts/fonts/advance_${key}.txt`));this.painter.register(key,readFontAtlas(metadata,advance),readDds(await this.load(`./artifacts/fonts/${key}.dds`)));}
 }
}
