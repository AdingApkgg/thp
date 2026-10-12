// Aggregate resource evidence only. This gate never sets completeGame or claims
// that an archive reader implements a game's interpreter or hardware platform.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const json=p=>JSON.parse(readFileSync(resolve(root,p),'utf8'));
const sha=p=>createHash('sha256').update(readFileSync(resolve(root,p))).digest('hex');
const coreSha=sha('runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
const coverage=json('docs/porting/reference-coverage.json'),rows=[];
for(const game of coverage.missing){
 const target=json(`runtimes/${game}/${game==='th12'?'th12_web/':''}target.json`),title=game.slice(2);
 let files=0,evidence='未找到本地原作',resourceReady=false;
 if(title==='06nc'){
  const proof=json('artifacts/th06nc/pkgl-comparison.json');
  assert.equal(proof.passed,true);
  assert.equal(proof.executableSha256,target.sha256);
  assert.equal(sha(target.executable),target.sha256);
  assert.equal(proof.readerSha256,sha('shared/th06nc/pkgl.mjs'));
  assert.equal(proof.zstdSha256,sha('shared/vendor/fzstd/index.mjs'));
  assert.equal(proof.archives.length,Object.keys(target.dataArchives).length);
  for(const archive of proof.archives)assert.equal(archive.entries,target.dataArchives[archive.file].entries);
  files=proof.archives.reduce((n,a)=>n+a.entries,0);
  evidence='PKGL 全条目解码与独立 Python/libzstd 逐文件 SHA-256 比对';resourceReady=true;
 }else if(['01','02','03','04','05'].includes(title)){
  const pc=json('artifacts/pc98/resources.json'),seven=json('artifacts/pc98/sevenzip-comparison.json');
  assert.equal(pc.readerSha256,sha('shared/pc98/hdi.mjs'));assert.equal(seven.passed,true);
  assert.equal(seven.diskSha256,pc.diskSha256);assert.equal(seven.compared,pc.files.length);
  assert.equal(target.diskImage.sha256,pc.diskSha256);
  files=pc.games.find(g=>g.game===game).files;evidence='HDI/FAT 全文件与 7-Zip 比对';resourceReady=true;
 }else if(['135','145','155','175'].includes(title)){
  const lateSha=sha('shared/tasofro/archives.mjs'),late=json('artifacts/tasofro/python-comparison.json');
  assert.equal(late.passed,true);assert.equal(late.readerSha256,lateSha);assert.equal(late.entries,late.decodedPrefixes);
  const proof=json(`artifacts/tasofro/${game}.json`);assert.equal(proof.readerSha256,lateSha);
  for(const a of proof.archives)assert.equal(a.entries.length,a.decoded.length);
  files=proof.archives.reduce((n,a)=>n+a.entries.length,0);
  evidence='全条目解码；全目录及解码前缀与 Python 比对';resourceReady=true;
 }else if(target.executable){
  evidence='本地原作已找到，资源读取验收待完成';
  if(existsSync(resolve(root,`artifacts/archive-differential/${game}.json`))){
   const proof=json(`artifacts/archive-differential/${game}.json`);assert.equal(proof.passed,true);assert.equal(proof.coreSha256,coreSha);
   files=proof.entries??proof.archives.reduce((n,a)=>n+a.entries,0);
   evidence=title==='075'?'独立目录公式与原始明文逐字节比对':'全条目与 thtk 逐字节比对';resourceReady=true;
  }
 }
 rows.push({game,resourceReady,resourceEntries:files,evidence,completeGame:false});
}
const report={scope:'Resource access only; no complete gameplay assertion.',titles:rows};
writeFileSync(resolve(root,'docs/porting/resource-progress.json'),JSON.stringify(report,null,2)+'\n');
console.log(`Resource gates passed for ${rows.filter(r=>r.resourceReady).length}/${rows.length} titles.`);
for(const row of rows)console.log(`${row.game}: ${row.resourceEntries} ${row.evidence}`);
