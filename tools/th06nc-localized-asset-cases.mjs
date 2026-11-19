import {resolveLocalizedAsset} from '../shared/th06nc/localized-asset.mjs';
const cases=[];
for(const language of ['ja','en','zh-CN','zh-TW','de','es-419','es-ES','fr','it','ko','pt-BR','ru',''])
 for(const path of ['data/title/title01.dds','C:\\game/title00_4k.dds','no-extension','.hidden','A/B\\C/name.multi.dds','data/制作.png'])
  for(const first of [0,3,15,16])for(const last of [0,7,15,16])for(const bypass of [false,true]){
   const basename=path.slice(Math.max(path.lastIndexOf('/'),path.lastIndexOf('\\'))+1);
   const dot=basename.lastIndexOf('.');
   const localized=dot<0?basename+'_'+language:basename.slice(0,dot)+'_'+language+basename.slice(dot);
   const archives=Array.from({length:17},()=>null);
   archives[first]={entries:[{name:'unrelated'},{name:basename}]};
   archives[last]??={entries:[]};
   archives[last].entries.push({name:localized},{name:localized});
   cases.push({path,language,archives,bypass,expected:resolveLocalizedAsset(path,archives,language,{bypass})});
  }
console.log(JSON.stringify(cases));
