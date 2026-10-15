// Freeze current sources, compile all 141 core units, preserve every prior build.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/third-reward-core-build-oct16');
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex');
assert.deepEqual(process.argv.slice(2),['--execute']);assert(!existsSync(out));mkdirSync(out);
const priorBytes=read(resolve(root,'artifacts/th14/constructor-hit-core-build-v2-oct15/build-result.json')),prior=JSON.parse(priorBytes);
assert.equal(sha(priorBytes),'f65f1560a7aa24088d312b710469e3f4138bdc6a5ca1b3da9002395da521d91d');
const sourceHashes=Object.fromEntries(Object.keys(prior.sourceHashes).map(n=>[n,sha(read(resolve(rt,n)))]));
const changes=Object.keys(sourceHashes).filter(n=>sourceHashes[n]!==prior.sourceHashes[n]).sort();
assert.deepEqual(changes,['cpp/game/ShotTh14.cpp']);
for(const n of Object.keys(sourceHashes)){const dest=resolve(out,'source',n);mkdirSync(dirname(dest),{recursive:true});copyFileSync(resolve(rt,n),dest,1);}
const portable=resolve(root,'runtimes/th12/portable/sdl/GraphicsState.hpp'),portableCopy=resolve(out,'portable/sdl/GraphicsState.hpp');
mkdirSync(dirname(portableCopy),{recursive:true});copyFileSync(portable,portableCopy,1);
const portableSha256=sha(read(portable));
const engineBytes=read(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')),engine=JSON.parse(engineBytes);
assert.equal(engine.sources.length,141);
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const objects=resolve(out,'engine/objects');mkdirSync(objects,{recursive:true});
const env={...process.env,TEMP:objects,TMP:objects,TMPDIR:objects};
const run=(args,log)=>new Promise((accept,reject)=>{const child=spawn(compiler,args,{cwd:resolve(out,'source'),env,windowsHide:true,stdio:['ignore','pipe','pipe']});let output='';for(const s of [child.stdout,child.stderr])s.on('data',b=>{output+=b;});child.on('error',reject);child.on('close',code=>{writeFileSync(log,output,{flag:'wx'});code?reject(Error(output)):accept();});});
let cursor=0,completed=0;
await Promise.all(Array.from({length:3},async()=>{while(cursor<engine.sources.length){const n=engine.sources[cursor++],name=n.replaceAll('/','_')+'.o';await run([...engine.compileFlags,n,'-o',resolve(objects,name)],resolve(objects,name+'.log'));if(++completed%30===0)console.log(JSON.stringify({compiled:completed,total:engine.sources.length}));}}));
const paths=engine.sources.map(n=>resolve(objects,n.replaceAll('/','_')+'.o'));
const wasm=resolve(out,'engine/engine-th14.wasm');await run([...engine.linkFlags,...paths,'-o',wasm],resolve(out,'engine/link.log'));
for(const[n,value]of Object.entries(sourceHashes))assert.equal(sha(read(resolve(rt,n))),value,n);
const result={compiled:true,engineOnly:true,sourceFiles:267,engineObjects:141,sourceHashes,productionSourceChanges:changes,
 priorBuildSha256:sha(priorBytes),engineConfigurationSha256:sha(engineBytes),compileFlags:engine.compileFlags,linkFlags:engine.linkFlags,
 compilerSha256:sha(read(compiler)),portableDependency:{path:portable,sha256:portableSha256},toolSha256:sha(read(import.meta.filename)),outputs:[...paths,wasm].map(path=>({path,bytes:read(path).length,sha256:sha(read(path))})),
 runtimeExecuted:false,audioPlayed:false,nativeEquivalent:false,completeGame:false};
writeFileSync(resolve(out,'build-result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({compiled:true,sourceFiles:267,engineObjects:141,resultSha256:sha(read(resolve(out,'build-result.json')))}));
