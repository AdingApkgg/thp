import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {openHdi} from '../shared/pc98/hdi.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),sha=b=>createHash('sha256').update(b).digest('hex');
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th01/target.json'),'utf8'));
const raw=readFileSync(target.diskImage.path),disk=openHdi(raw);
if(sha(raw)!==target.diskImage.sha256)throw Error('original HDI digest mismatch');
const files=disk.partitions.flatMap(p=>p.entries.filter(e=>!e.directory).map(e=>({...e,partition:p.index,sha256:sha(p.readFile(e.path))})));
const games=[];
for(const suffix of ['01','02','03','04','05']){
 const config=JSON.parse(readFileSync(resolve(root,`runtimes/th${suffix}/target.json`),'utf8'));
 const entries=files.filter(e=>e.path.toLowerCase().startsWith(config.boot.directory.toLowerCase()+'/'));
 const boot=entries.find(e=>e.name.toLowerCase()==='game.bat');
 if(!boot)throw Error(`th${suffix}: game.bat missing`);
 const partition=disk.partitions.find(p=>p.index===boot.partition);
 const command=new TextDecoder('shift_jis').decode(partition.readFile(boot.path));
 games.push({game:`th${suffix}`,files:entries.length,bootFile:boot.path,bootCommand:command});
 console.log(`th${suffix}: ${entries.length} files, ${boot.path}`);
}
const output=resolve(root,'artifacts/pc98');mkdirSync(output,{recursive:true});
// Exporting the FAT volume only to ignored local artifacts lets an independent
// filesystem reader compare every file. No game data belongs in the repository.
for(const p of disk.partitions)writeFileSync(resolve(output,`partition-${p.index}.img`),raw.subarray(p.offset,p.offset+p.bytes));
writeFileSync(resolve(output,'resources.json'),JSON.stringify({diskSha256:sha(raw),readerSha256:
 sha(readFileSync(resolve(root,'shared/pc98/hdi.mjs'))),games,files},null,2)+'\n');
