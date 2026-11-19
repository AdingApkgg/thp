// Native archive reader387a0: localized basenames across all16 archive slots
// precede every unlocalized candidate. The bypass branch retains the full path.
export function localizedAssetName(path,language){
 const basename=path.slice(Math.max(path.lastIndexOf('/'),path.lastIndexOf('\\'))+1);
 const dot=basename.lastIndexOf('.');
 return dot<0?`${basename}_${language}`:
  `${basename.slice(0,dot)}_${language}${basename.slice(dot)}`;
}

export function resolveLocalizedAsset(path,archives,language,{bypass=false}={}){
 if(bypass)return {kind:'file',path};
 const basename=path.slice(Math.max(path.lastIndexOf('/'),path.lastIndexOf('\\'))+1);
 const localized=localizedAssetName(path,language);
 for(const name of [localized,basename]){
  for(let archiveIndex=0;archiveIndex<Math.min(archives.length,16);archiveIndex++){
   const entries=archives[archiveIndex]?.entries;
   if(!entries)continue;
   const entryIndex=entries.findIndex(entry=>entry.name===name);
   if(entryIndex>=0)return {kind:'archive',archiveIndex,entryIndex,name};
  }
 }
 return null;
}
