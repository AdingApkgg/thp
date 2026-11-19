import {controllerIconAssets} from '../shared/th06nc/title-key-options.mjs';
import {musicRoomAssets} from '../shared/th06nc/music-room-state.mjs';
import {resultAssets} from '../shared/th06nc/result-state.mjs';
import {titleReplayResources} from '../shared/th06nc/title-replay-layout.mjs';
import {asciiFontAssets} from '../shared/th06nc/ascii-layout.mjs';
import {pauseAsset} from '../shared/th06nc/pause-menu.mjs';
import {hudFrameAsset} from '../shared/th06nc/hud-background.mjs';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openPkgl} from '../shared/th06nc/pkgl.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {stageAssetPlan} from '../shared/th06nc/stage-layout.mjs';
import {commonProjectileAssetPlan,stageEffectAssetPlan} from '../shared/th06nc/common-layout.mjs';
import {stdAssetPlan} from '../shared/th06nc/std-state.mjs';
import {playerAssetPlan} from '../shared/th06nc/player-init.mjs';
import {messageAssetPlan} from '../shared/th06nc/message-layout.mjs';
import {messageProgressAssetPlan} from '../shared/th06nc/message-progress.mjs';
import {scorePopupAssetPlan} from '../shared/th06nc/score-popup-draw.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'),target=JSON.parse(readFileSync('runtimes/th06nc/target.json')),evidence=JSON.parse(readFileSync('docs/porting/th06nc-dds-verified.json')),refs=[...resultAssets,pauseAsset,hudFrameAsset,{archive:'th06CM.dat',file:'front.anm',slot:13,base:0x620},...commonProjectileAssetPlan(),scorePopupAssetPlan(),playerAssetPlan(0),playerAssetPlan(1)],requests=new Map(),archives=new Map(),files=[];
refs.push(...asciiFontAssets,...musicRoomAssets,...controllerIconAssets);
refs.push(...[...titleReplayResources,{file:'select00d.anm'}].map(ref=>({...ref,archive:'th06TL.dat'})));
if(sha(readFileSync(target.executable))!==target.sha256)throw Error('TH06nc executable changed');
for(let stage=1;stage<=7;stage++){refs.push(...stageAssetPlan(stage).enemyAnimations,stageEffectAssetPlan(stage),stdAssetPlan(stage),...messageProgressAssetPlan(stage));for(const character of [0,1])refs.push(...messageAssetPlan(stage,character));}
refs.push(...['eff06.anm','eff07.anm','face12c.anm'].map(file=>({archive:'th06ST.dat',file})));
for(const ref of refs){const resource=readAnm(readFileSync(`runtimes/th06nc/artifacts/scripts/${ref.archive}/${ref.file}`));if(resource.textureName==='@')continue;const file=resource.textureName.split('/').at(-1).replace(/\.png$/,'.dds'),expected=evidence.files.find(entry=>entry.archive===ref.archive&&entry.name===file);if(!expected)throw Error('Texture lacks native evidence: '+ref.archive+'/'+file);const previous=requests.get(file);if(previous&&previous.expected.sha256!==expected.sha256)throw Error('Texture basename collision: '+file);requests.set(file,{archive:ref.archive,file,expected});}
mkdirSync('runtimes/th06nc/artifacts/textures',{recursive:true});
for(const ref of requests.values()){
 const destination='runtimes/th06nc/artifacts/textures/'+ref.file;let raw=existsSync(destination)?readFileSync(destination):null;
 if(!raw){if(!archives.has(ref.archive)){const bytes=readFileSync(target.dataArchives[ref.archive].path);archives.set(ref.archive,await openPkgl((offset,length)=>bytes.subarray(offset,offset+length),bytes.length,ref.archive));}const archive=archives.get(ref.archive),entry=archive.entries.find(entry=>entry.name===ref.file);if(!entry)throw Error('Texture missing: '+ref.file);raw=await archive.readEntry(entry.index);}
 const hash=sha(raw);if(hash!==ref.expected.sha256)throw Error('Native texture changed: '+ref.file);if(!existsSync(destination))writeFileSync(destination,raw);files.push({archive:ref.archive,file:ref.file,bytes:raw.length,sha256:hash});
}
writeFileSync('runtimes/th06nc/artifacts/textures/game-manifest.json',JSON.stringify(files,null,2)+'\n');console.log(JSON.stringify({scope:'Original textures referenced by stage/player/message/progress ANMs; independent native DDS hashes verified.',files:files.length,bytes:files.reduce((sum,file)=>sum+file.bytes,0)}));
