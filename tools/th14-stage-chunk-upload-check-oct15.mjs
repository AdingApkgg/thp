// Actual queue and exact GraphicsDevice methods, with a recording backend.
// Real TextureImage conversion runs; no graphics device or audio is opened.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/stage-chunk-upload-check-oct15');
const sha=b=>createHash('sha256').update(b).digest('hex');
const args=process.argv.slice(2);assert(args.length===1&&args[0]==='--execute');
mkdirSync(out,{recursive:false});
const graphics=readFileSync(resolve(rt,'cpp/sdl/GraphicsDevice.cpp'),'utf8');
function block(text,needle){const start=text.indexOf(needle);assert(start>=0);let at=text.indexOf('{',start),depth=1,end=at+1;for(;depth&&end<text.length;++end){if(text[end]==='{')++depth;if(text[end]==='}')--depth;}assert.equal(depth,0);return text.slice(start,end);}
const methods=['bool GraphicsDevice::prepare_texture(','bool GraphicsDevice::preload(','bool GraphicsDevice::preload_chunk(','void GraphicsDevice::unload(','u32 GraphicsDevice::texture('].map(n=>block(graphics,n));
const application=readFileSync(resolve(rt,'cpp/sdl/Application.cpp'),'utf8');
const tick=block(application,'if(stage_uploads.pending())');
assert(tick.includes('graphics.preload_chunk(*job.resource,job.chunk)'));
assert(!tick.includes('animations.update')&&!tick.includes('return true;'));
const fixture=`#include "StageUploadsTh14.hpp"
#include "../game/TextureImage.hpp"
#include <map>
using namespace th11;using namespace th11::sdl;
struct Backend {u32 prepared=0,released=0,flushed=0;void prepare(u32){++prepared;}void release(u32){++released;}void flush(){++flushed;}};
struct Graphics {
 struct Texture {TextureImage image;u32 revision=0;};
 std::map<u32,Texture> textures;std::map<const AnmResource*,std::vector<u32>> resources;
 u32 next_handle=3;Backend backend;std::string error;const bool* texture_high_precision=nullptr;
 ${methods.map(m=>m.replaceAll('GraphicsDevice::','')).join('\n')}
};
static u32 words[4]{},checks=0,failed=0,first=0;
static void check(bool value,u32 code){++checks;if(!value){++failed;if(!first)first=code;}}
static AnmTexture page(u16 width=4){AnmTexture t;t.kind=AnmTexture::Kind::Blank;t.name="@test";t.width=width;t.height=4;t.format=5;return t;}
extern "C" __attribute__((export_name("run"))) const u32* run(){
 Graphics g;StageUploadsTh14 queue;StageResources a,b;
 a.logo.textures={page(),page(8)};a.background.textures={page(),page(),page()};
 a.enemies.textures={page()};a.ecl_animation_names[0]="one";a.ecl_animations[0].textures={page(),page()};
 const auto hud=StageResourceEffects::Phase::Hud,scene=StageResourceEffects::Phase::Scene,timeline=StageResourceEffects::Phase::Timeline;
 check(queue.begin(a,hud),1);check(queue.pending_count()==1&&!queue.ready(hud),2);
 u32 calls=0,last_chunk=99;auto upload=[&](const auto& job){++calls;last_chunk=job.chunk;return g.preload_chunk(*job.resource,job.chunk,false);};
 check(queue.advance(upload),3);check(calls==1&&last_chunk==0&&g.backend.prepared==1,4);
 check(queue.pending()&&!queue.ready(hud)&&queue.pending_count()==1,5);
 check(g.texture(a.logo,0)!=0&&g.texture(a.logo,1)==0,6);
 check(!queue.begin(b,hud)&&!queue.begin(a,scene),7);
 check(queue.begin(a,hud),8);check(queue.advance(upload),9);
 check(calls==2&&last_chunk==1&&g.backend.prepared==2,10);
 check(queue.ready(hud)&&!queue.pending(),11);queue.finish(a);check(queue.owner()==nullptr,12);
 check(queue.begin(a,scene),20);check(queue.advance(upload),21);
 check(queue.pending()&&last_chunk==0&&g.resources.at(&a.background).size()==1,22);
 queue.cancel(b);check(queue.owner()==&a&&queue.pending(),23);
 check(queue.advance(upload)&&last_chunk==1,24);check(queue.pending(),25);
 check(queue.advance(upload)&&last_chunk==2&&queue.ready(scene),26);queue.finish(a);
 check(queue.begin(a,timeline),30);check(queue.pending_count()==2,31);
 check(queue.advance(upload)&&last_chunk==0,32);check(queue.pending_count()==1,33);
 check(queue.advance(upload)&&last_chunk==0,34);check(queue.pending_count()==1,35);
 a.ecl_animations[0].textures[1].format=65535;
 check(!queue.advance(upload)&&last_chunk==1,36);
 check(queue.failed()&&queue.pending()&&queue.pending_count()==1,37);
 check(g.resources.at(&a.ecl_animations[0]).size()==1,38);
 const auto failed_calls=calls;check(!queue.advance(upload)&&calls==failed_calls,39);
 queue.cancel(a);check(queue.owner()==nullptr&&!queue.pending(),40);
 auto released=g.backend.released;g.unload(a.ecl_animations[0]);
 check(g.backend.released==released+1&&!g.resources.count(&a.ecl_animations[0]),41);
 AnmResource c;c.textures={page(),page(8),page(16)};
 check(!g.preload_chunk(c,1,false)&&g.backend.prepared==7,50);
 check(g.preload_chunk(c,0,false),51);const auto prepared=g.backend.prepared;
 check(g.preload_chunk(c,0,false)&&g.backend.prepared==prepared,52);
 check(g.preload(c,false)&&g.resources.at(&c).size()==3&&g.backend.prepared==prepared+2,53);
 check(g.preload(c,false)&&g.backend.prepared==prepared+2,54);
 check(g.textures.at(g.texture(c,2)).image.width==16,55);
 released=g.backend.released;g.unload(c);check(g.backend.released==released+3,56);
 AnmResource d;d.textures={page(),page()};d.textures[1].format=65535;
 check(g.preload_chunk(d,0,false),60);released=g.backend.released;
 check(!g.preload(d,false)&&g.backend.released==released+1&&!g.resources.count(&d),61);
 AnmResource empty;check(g.preload_chunk(empty,0,false)&&g.preload(empty,false),70);g.unload(empty);
 words[0]=failed;words[1]=checks;words[2]=first;words[3]=calls;return words;
}
`;
const source=resolve(out,'fixture.cpp'),wasm=resolve(out,'check.wasm');writeFileSync(source,fixture,{flag:'wx'});
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const realSources=['cpp/game/TextureImage.cpp','cpp/game/ImageResample.cpp'];
const flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-O2','-std=c++17','-ffp-contract=off','-fno-exceptions','-fno-rtti','-I',resolve(rt,'cpp/sdl'),'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory'];
execFileSync(compiler,[...flags,source,...realSources.map(n=>resolve(rt,n)),'-o',wasm],{cwd:out,windowsHide:true,stdio:'inherit',env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(readFileSync(wasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const pointer=instance.exports.run(),result=Array.from(new Uint32Array(instance.exports.memory.buffer,pointer,4));
const report={passed:result[0]===0,resultWords:result,checks:result[1],failures:result[0],firstFailure:result[2],
 completeGame:false,nativeEquivalent:false,actualGpuInvoked:false,actualAudioPlayed:false,
 exactGraphicsMethods:methods.map(source=>({source,sha256:sha(Buffer.from(source))})),exactStageTick:tick,
 sourceHashes:Object.fromEntries(['cpp/sdl/StageUploadsTh14.hpp','cpp/sdl/GraphicsDevice.cpp','cpp/sdl/GraphicsDevice.hpp','cpp/sdl/Application.cpp','cpp/game/TextureImage.hpp',...realSources].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),
 toolSha256:sha(readFileSync(import.meta.filename)),fixtureSha256:sha(readFileSync(source)),wasmSha256:sha(readFileSync(wasm)),
 scope:'Actual production StageUploads queue and exact extracted GraphicsDevice methods compile with real TextureImage/ImageResample. Only backend upload/flush/release are recording dependencies. Verifies one chunk per advance, delayed resource readiness, unchanged successful normal-tick continuation, repeated same phase, wrong-owner and mid-resource cancellation, retained partial failure, no retry after failed queue, ordered/idempotent chunks, synchronous completion of partial textures, cleanup, and empty resources. No whole-game or physical GPU timing claim.'};
writeFileSync(resolve(out,'receipt.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:report.passed,resultWords:result}));assert.equal(result[0],0,JSON.stringify(result));
