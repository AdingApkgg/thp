import {readFileSync,mkdtempSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {WASI} from 'node:wasi';
const repo=process.cwd();
const core=readFileSync('runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm');
const thdat=repo+'/tools/thtk/extracted/thtk-bin-12/thdat.exe';
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const t of [16,17,18,19]){
  const rec=JSON.parse(readFileSync(`runtimes/th${t}/target.json`,'utf8')).dataArchives[`th${t}.dat`];
  const bytes=readFileSync(rec.path);
  const dir=mkdtempSync(resolve('tools/tmp/tharc'+t+'-'));
  const skip=(t===18||t===19)?17:t;
  execFileSync(thdat,['-x',String(skip),rec.path],{cwd:dir,stdio:'pipe',windowsHide:true});
  const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
  const {instance}=await WebAssembly.instantiate(core,{wasi_snapshot_preview1:wasi.wasiImport});
  wasi.initialize(instance);
  const c=instance.exports;
  const line=[];
  for(const v of [10,12,13,14]){
    const p=c.allocate(bytes.length),a=c.archive_create();
    new Uint8Array(c.memory.buffer,p,bytes.length).set(bytes);
    if(c.archive_open(a,p,bytes.length,v)!==1){ line.push(`v${v}:refused`); continue; }
    let ok=0,total=0,firstBad='';
    for(let n=0;n<Math.min(4,c.archive_count(a));n++){
      const q=c.archive_name(a,n); let name=''; for(let k=0;k<128;k++){const ch=new Uint8Array(c.memory.buffer,q+k);if(ch[0]===0)break;name+=String.fromCharCode(ch[0]);}
      const want=readFileSync(join(dir,name));
      const out=c.allocate(want.length);
      const got=c.archive_read(a,n,out,want.length);
      const mine=Buffer.from(new Uint8Array(c.memory.buffer,out,want.length));
      total++;
      if(got===want.length&&sha(mine)===sha(want)) ok++; else if(!firstBad) firstBad=name;
    }
    line.push(`v${v}:${ok}/${total}${firstBad?' (first bad '+firstBad+')':''}`);
  }
  console.log(`  th${t} skip=${skip} ${line.join('  ')}`);
}
