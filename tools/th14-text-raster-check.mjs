import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/text-raster-check');mkdirSync(out,{recursive:true});
const fixture='tests/cpp/th14-text-raster-fixture.cpp',sources=['cpp/game/TextRaster.cpp','cpp/game/GlyphAtlas.cpp','cpp/game/ImageResample.cpp'],path=resolve(out,'text-raster.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...sources,'-o',path],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/text-raster-native.json'),'utf8')),fonts=resolve(root,'runtimes/th14/th14_web/assets/sdl-native/fonts');
for(const [slot,name]of ['font0.bin','font1.bin','font2.bin','font3.bin','cp932.bin','blend4444.bin','font4.bin','font5.bin','font6.bin','font7.bin'].entries()){
 const data=readFileSync(resolve(fonts,name)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.load(slot,p,data.length),1,name);c.release(p);
}
let copies=0;
const initialization=JSON.parse(readFileSync(resolve(root,'artifacts/th14/font-initialization-native.json'),'utf8'));
const fontManifest=JSON.parse(readFileSync(resolve(fonts,'manifest.json'),'utf8'));
assert.equal(fontManifest.format,'T11G-v2-RGB');assert.equal(fontManifest.quality,2);
const drawOrder=[0,2,4,5,1,3,6,7],faces={'826c827220835383568362834e':'ＭＳ ゴシック','826c82722096be92a9':'ＭＳ 明朝'};
for(const r of initialization.rows)for(const [slot,creation]of drawOrder.entries()){
 const f=r.fonts[creation];assert.deepEqual(fontManifest.fonts[slot],[f.args[0],f.args[4],faces[f.face]]);
 assert.deepEqual(f.args.slice(1,4),[0,0,0]);assert.deepEqual(f.args.slice(5),[0,0,0,128,0,0,fontManifest.quality,17]);
}
for(const f of fontManifest.files){const b=readFileSync(resolve(fonts,f.file));assert.equal(b.length,f.bytes);assert.equal(createHash('sha256').update(b).digest('hex'),f.sha256);}
for(const r of initialization.rows){const p=c.initialize(r.seed,r.calls,+r.firstSuccess);assert.equal(Buffer.from(new Uint8Array(c.memory.buffer,p,256)).toString('hex'),r.noise);assert.equal(c.initial_state(0),r.finalSeed);assert.equal(c.initial_state(1)>>>0,r.finalCalls);assert.equal(c.initial_state(2),r.scratchFormats.at(-1));}
const layouts=JSON.parse(readFileSync(resolve(root,'artifacts/th14/text-layout-native.json'),'utf8'));
for(const r of layouts.rows){const p=c.layout(r.mode,r.height,r.width,r.length,r.flags,r.spacing,r.offset,r.font),words=Array.from(new Uint32Array(c.memory.buffer,p,8));assert.equal(r.finalFlags,0xa5);
 if(!r.delivery){assert.equal(words[7],1);continue;}assert.equal(words[7],0);const d=r.delivery;assert.deepEqual(words.slice(0,7),[d.height,d.color,d.outline,d.font,d.spacing,d.shadow,d.offset],JSON.stringify(r));
}
for(const [i,r]of proof.rows.entries()){
 const text=Buffer.from(r.text,'hex');new Uint8Array(c.memory.buffer,c.text_input(),text.length+1).set(Buffer.concat([text,Buffer.from([0])]));
 assert.equal(c.draw(r.font,r.height,r.offset,r.color,r.outline,r.spacing,+r.plain),1);
 const actual=Buffer.from(new Uint8Array(c.memory.buffer,c.pixels(),1024*128*2)),expected=readFileSync(resolve(root,r.file));
 if(!actual.equals(expected)){let at=0;while(actual[at]===expected[at])++at;const message=`retail case${i} font${r.font} text${r.text} (${(at>>1)%1024},${Math.floor(at/2048)}): cpp=${actual.readUInt16LE(at&~1).toString(16)} native=${expected.readUInt16LE(at&~1).toString(16)}`;if(process.argv.includes('--diagnose')){console.log(message);writeFileSync(resolve(out,`case${i}.bin`),actual);continue;}assert.fail(message);}
 assert.deepEqual(r.upload,{destination:[0,0,512,32],source:[0,0,512,32],format:26,pitch:2048,filter:1,colorKey:0});
 for(const format of [0,1]){const bpp=format?4:2,p=c.write(format),written=new Uint8Array(c.memory.buffer,p,520*40*bpp);assert.notEqual(p,0);
  for(let y=0;y<40;++y)for(let x=0;x<520;++x){const at=(y*520+x)*bpp;if(x<4||x>=516||y<3||y>=35){for(let k=0;k<bpp;++k)assert.equal(written[at+k],0xa5);continue;}
   const v=expected.readUInt16LE((y-3)*2048+(x-4)*2),want=format?[(v&15)*17,((v>>4)&15)*17,((v>>8)&15)*17,(v>>12)*17]:[v&255,v>>8];assert.deepEqual(Array.from(written.subarray(at,at+bpp)),want);
  }++copies;
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
if(process.argv.includes('--diagnose'))process.exit(0);
writeFileSync(resolve(root,'docs/porting/th14-text-raster-verified.json'),JSON.stringify({passed:true,cases:proof.rows.length,copies,layoutCases:layouts.rows.length,initializationCases:initialization.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:proof.scope+' Compares all262144 scratch bytes/case. Native upload descriptors separately match copy dimensions/filter1; copy checks compare ARGB4444/BGRA8 bytes and untouched borders against native scratch data. Actual D3DX/GPU upload excluded. '+layouts.scope+' Thirty retail467940 initialization states compare256 table bytes, visual seed/call rollover and bitmap format selection; DIB creation/font allocation controlled. All eight baked font descriptors match native creation/draw order; every font asset size/hash checked. Browser supports ARGB4444 only. Other552 startup ANM next32 calls and clock seed remain outside this proof; no padding or captured seed override.',sources:Object.fromEntries([fixture,...sources,'cpp/game/GlyphAtlas.hpp','cpp/game/ImageResample.hpp','cpp/game/TextRaster.hpp','cpp/game/TextLayoutTh14.hpp','cpp/game/FontBitmapTh14.hpp','cpp/game/GameSession.cpp','cpp/game/GameSession.hpp','cpp/sdl/FontDevice.cpp','cpp/sdl/FontDevice.hpp','cpp/sdl/Application.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),tools:Object.fromEntries(['tools/th14-text-raster-check.mjs','tools/th14-text-raster-native.py','tools/th14-text-layout-native.py','tools/th14-font-initialization-native.py','runtimes/th12/th12_web/scripts/prepare-fonts.mjs'].map(n=>[n,sha(readFileSync(resolve(root,n)))])),fontManifest},null,2)+'\n');
console.log(`PASS ${proof.rows.length} retail text raster cases, ${copies} copy/format cases, ${layouts.rows.length} wrapper cases, ${initialization.rows.length} font initialization cases`);
