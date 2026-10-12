import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/text-raster-legacy');mkdirSync(out,{recursive:true});
const files=['TextRaster.cpp','GlyphAtlas.cpp'],before=files.map(n=>{const p=resolve(out,n);writeFileSync(p,execFileSync('git',['show',`HEAD:runtimes/th12/th12_web/cpp/game/${n}`],{cwd:root,windowsHide:true}));return p;}),compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const sha=b=>createHash('sha256').update(b).digest('hex'),results=[];
async function module(title,baseline){const path=resolve(out,`${title}-${baseline?'head':'current'}.wasm`);
 execFileSync(compiler,['--target=wasm32-wasip1',`-DPORT_TITLE=${title}`,'-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-Icpp/game','tests/cpp/th14-text-raster-fixture.cpp',...(baseline?before:files.map(n=>'cpp/game/'+n)),'cpp/game/ImageResample.cpp','-o',path],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 for(const [slot,name]of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin'].entries()){const data=readFileSync(resolve(rt,'assets/sdl-native/fonts',name)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.load(slot,p,data.length),1);c.release(p);}
 return {c,sha256:sha(bytes)};
}
for(const title of [11,12,13]){const current=await module(title,false),head=await module(title,true);
 for(let i=0;i<160;++i){const text=i%4===0?Buffer.from('Spell 012345: iWjgA /'):i%4===1?Buffer.from('926e97ec9361817596b2917a8176','hex'):i%4===2?Buffer.from('b1b2b3dedf','hex'):Buffer.from(''),args=[(i>>2)%4,i%3===0?16:17,i%5===0?-3:i%19,(i*199969+0x1234)&0xffffff,(i*78901)&0xffffff,i%7===0?12:0,+(i%6===0)];
  for(const {c}of [current,head])new Uint8Array(c.memory.buffer,c.text_input(),text.length+1).set(Buffer.concat([text,Buffer.from([0])]));
  assert.equal(current.c.draw(...args),head.c.draw(...args));assert.deepEqual(Buffer.from(new Uint8Array(current.c.memory.buffer,current.c.pixels(),1024*65*2)),Buffer.from(new Uint8Array(head.c.memory.buffer,head.c.pixels(),1024*65*2)),`title${title} case${i}`);
 }
 results.push({title,cases:160,currentSha256:current.sha256,headSha256:head.sha256});
}
writeFileSync(resolve(root,'docs/porting/text-raster-legacy-regression-verified.json'),JSON.stringify({passed:true,head:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8',windowsHide:true}).trim(),cases:results,scope:'TH11/12/13 shared raster and glyph implementations compared with repository HEAD, all133120 scratch bytes across160 styles/title. Uses their existing shared font assets. Code regression only; not a new native or GPU equivalence proof.',sources:Object.fromEntries(files.map(n=>[n,sha(readFileSync(resolve(rt,'cpp/game',n)))]))},null,2)+'\n');
console.log('PASS TH11/12/13 text raster HEAD regression: 480 complete scratch images');
