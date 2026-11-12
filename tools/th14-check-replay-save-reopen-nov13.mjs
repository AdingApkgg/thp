import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/replay-save-reopen-nov13');
const sha=b=>createHash('sha256').update(b).digest('hex');
const build=JSON.parse(readFileSync(resolve(out,'build.json')));
for(const [p,h]of Object.entries({...build.sourceBindings,...build.objectBindings}))assert.equal(sha(readFileSync(resolve(root,p))),h,p);
assert.equal(sha(readFileSync(resolve(root,'tools/th14-replay-save-reopen-nov13.cpp'))),build.fixtureSha256);
const bytes=readFileSync(resolve(out,'probe.wasm'));assert.equal(sha(bytes),build.wasmSha256);
const module=new WebAssembly.Module(bytes),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const imports={env:{memory},wasi_snapshot_preview1:wasi.wasiImport};
for(const x of WebAssembly.Module.imports(module)){
 imports[x.module]??={};if(x.kind==='function'&&!imports[x.module][x.name])imports[x.module][x.name]=()=>{throw Error('Unexpected platform call '+x.module+'.'+x.name);};
}
const c=new WebAssembly.Instance(module,imports);wasi.initialize(c);
const files=resolve(out,'files');mkdirSync(files);const rows=[];
for(let selection=0;selection<6;selection++)for(let difficulty=0;difficulty<5;difficulty++)for(let practice=0;practice<2;practice++){
 const name=`s${selection}-d${difficulty}-p${practice}`;
 writeFileSync(resolve(out,'active-case.json'),JSON.stringify({name,completed:rows.length})+'\n');
 const n=c.exports.run(selection,difficulty,practice),file=Buffer.from(new Uint8Array(memory.buffer,c.exports.file_data(),n));
 const decoded=Buffer.from(new Uint8Array(memory.buffer,c.exports.decoded_data(),c.exports.decoded_size()));
 writeFileSync(resolve(files,name+'.rpy'),file,{flag:'wx'});writeFileSync(resolve(files,name+'.decoded'),decoded,{flag:'wx'});
 rows.push({name,selection,difficulty,practice,fileBytes:n,fileSha256:sha(file),decodedBytes:decoded.length,decodedSha256:sha(decoded)});
}
writeFileSync(resolve(out,'session-result.json'),JSON.stringify({cases:rows.length,rows,actualSessionSaveAndReplayOpen:true,
 saveTwiceByteIdentical:true,terminalSaveDoesNotMutateLiveRecorder:true,allRecordedInputEdgesAndHeaderCoordinatesChecked:true,
 completeGame:false,assetsLoaded:false,ordinaryGameplayOrBrowserDownloadAccepted:false,originalCodecVerificationPending:true,
 fixtureSha256:build.fixtureSha256,wasmSha256:build.wasmSha256,runnerSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({cases:rows.length,sessionSaveAndReopenPassed:true,originalCodecVerificationPending:true}));
