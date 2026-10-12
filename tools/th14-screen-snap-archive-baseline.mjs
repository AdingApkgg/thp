import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/screen-snap-baseline'),sha=b=>createHash('sha256').update(b).digest('hex');
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'].map(n=>'runtimes/th12/portable/sdl/'+n);
files.push(...['build.json','th11.mjs','th11.wasm'].map(n=>'runtimes/th14/th14_web/artifacts/sdl3-release/'+n));
files.push(...readdirSync(resolve(root,'docs/porting')).filter(n=>/^th14-(gpu-|launcher-alpha-browser|render-verified)/.test(n)&&n.endsWith('.json')).map(n=>'docs/porting/'+n));
const record={archived:true,purpose:'Immutable physical sources, release and reports before the TH14 screen-space subpixel correction; previous report paths retain their original source hashes.',files:{}};
for(const p of files){const b=readFileSync(resolve(root,p)),dest=resolve(out,p);mkdirSync(dirname(dest),{recursive:true});if(existsSync(dest))assert.equal(sha(readFileSync(dest)),sha(b),'refusing to replace historical baseline '+p);else writeFileSync(dest,b);record.files[p]={bytes:b.length,sha256:sha(b)};}
const manifest=resolve(out,'manifest.json');if(!existsSync(manifest))writeFileSync(manifest,JSON.stringify(record,null,2)+'\n');else assert.deepEqual(JSON.parse(readFileSync(manifest)),record);
console.log('Archived '+files.length+' pre-correction source, release and report files');
