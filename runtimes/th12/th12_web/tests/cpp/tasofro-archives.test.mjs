// The runtime parses only the directory and one entry at a time. Large original
// archives never enter WASM memory in their entirety.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,openSync,readSync,closeSync,mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {core,memory,sha} from './helpers.mjs';

const repo=resolve(dirname(fileURLToPath(import.meta.url)),'../../../../..');
const output=resolve(repo,'artifacts/archive-differential');
mkdirSync(output,{recursive:true});
const thdat=resolve(repo,'tools/thtk/extracted/thtk-bin-12/thdat.exe');
const readAt=(fd,size,offset)=>{
 const data=Buffer.alloc(size);let done=0;
 while(done<size){const n=readSync(fd,data,done,size-done,offset+done);assert.ok(n>0,'unexpected end of archive');done+=n;}
 return data;
};
function name(c,a,i){const p=c.archive_name(a,i),b=memory(c,p,1025),end=b.indexOf(0);assert.ok(end>=0);return Buffer.from(b.subarray(0,end)).toString('latin1');}
// thtk 12 uses narrow fopen on Windows. Match the host ACP explicitly while
// comparing original name bytes losslessly; UTF-8 replacement loses SJIS names.
const extractionEncoding=process.env.THTK_FILENAME_ENCODING??(process.platform==='win32'?'gbk':'utf-8');
const diskName=raw=>new TextDecoder(extractionEncoding).decode(Buffer.from(raw,'latin1'));

// thtk release 12 lacks TH75. An independent directory calculation uses the
// closed-form key sequence k(n)=100+100*n+77*n*(n-1)/2, not the C++ recurrence.
function th75Reference(prefix){
 const plain=Buffer.from(prefix.subarray(2));
 for(let i=0;i<plain.length;i++)plain[i]^=(100+100*i+77*i*(i-1)/2)&255;
 return Array.from({length:prefix.readUInt16LE()},(_,i)=>{
  const p=i*108,end=plain.indexOf(0,p);
  assert.ok(end>=p&&end<p+100);
  return {name:plain.subarray(p,end).toString('latin1').replaceAll('\\','/'),
   size:plain.readUInt32LE(p+100),offset:plain.readUInt32LE(p+104)};
 });
}

for(const title of ['075','105','123'])test(`TH${title}: all DAT entries, streamed from original archives`,async()=>{
 const target=JSON.parse(readFileSync(resolve(repo,`runtimes/th${title}/target.json`),'utf8'));
 const c=await core(),a=c.archive_create(),archives=[];
 try{for(const [file,record] of Object.entries(target.dataArchives)){
  const fd=openSync(record.path,'r');
  try{
   const prefix=readAt(fd,record.directoryBytes,0),p=c.allocate(prefix.length);
   let rows,extraction=null;
   if(title==='075')rows=th75Reference(prefix);
   else{
    const listing=execFileSync(thdat,['-l',String(record.pbgVersion),record.path],
     {encoding:'latin1',windowsHide:true,stdio:['ignore','pipe','pipe'],maxBuffer:16*1024*1024});
    rows=[...listing.matchAll(/^([^\r\n]+?)\s+(\d+)\s*$/gm)].map(m=>({name:m[1],size:Number(m[2])}));
    assert.equal(rows.length,record.entries,'thtk directory count');
    extraction=mkdtempSync(resolve(output,`th${title}-${file}-`));
    for(const row of rows)assert.ok(resolve(extraction,diskName(row.name)).startsWith(extraction+sep),'entry stays inside extraction');
    execFileSync(thdat,['-x',String(record.pbgVersion),record.path],
     {cwd:extraction,windowsHide:true,stdio:'pipe',maxBuffer:16*1024*1024});
   }
   try{
    memory(c,p,prefix.length).set(prefix);
    assert.equal(c.archive_open_directory(a,p,prefix.length,record.bytes,record.pbgVersion),1,file);
   }finally{c.release(p);}
   assert.equal(c.archive_count(a),rows.length);
   const decoded=[];
   for(let i=0;i<rows.length;i++){
    const row=rows[i],offset=c.archive_field(a,i,0),size=c.archive_field(a,i,1);
    assert.equal(name(c,a,i),row.name);assert.equal(size,row.size);
    if(row.offset!==undefined)assert.equal(offset,row.offset);
    const raw=readAt(fd,size,offset),input=c.allocate(Math.max(size,1)),out=c.allocate(Math.max(size,1));
    try{
     memory(c,input,size).set(raw);
     assert.equal(c.archive_decode_entry(a,i,input,size,out,size),size,row.name);
     const actual=Buffer.from(memory(c,out,size));
     const expected=extraction?readFileSync(resolve(extraction,diskName(row.name))):raw;
     assert.ok(actual.equals(expected),`${file}/${row.name}: decoded bytes`);
     decoded.push({name:row.name,bytes:size,sha256:sha(actual)});
    }finally{c.release(input);c.release(out);}
   }
   archives.push({file,entries:decoded.length,reference:extraction?'thtk release 12':'closed-form TH75 directory and unencrypted source bytes',extraction,decoded});
  }finally{closeSync(fd);}
 }}finally{c.archive_delete(a);}
 writeFileSync(resolve(output,`th${title}.json`),JSON.stringify({game:`th${title}`,passed:true,
  coreSha256:sha(readFileSync(resolve(repo,'runtimes/th12/th12_web/artifacts/cpp/game-core-test.wasm'))),archives},null,2)+'\n');
});

test('Tasofro directory rejects truncation and impossible ranges, and clears stale entries',async()=>{
 const c=await core(),a=c.archive_create(),payload=Buffer.from('example'),raw=Buffer.alloc(110+payload.length);
 raw.writeUInt16LE(1);raw.write('data\\a.txt',2);raw.writeUInt32LE(payload.length,102);raw.writeUInt32LE(110,106);payload.copy(raw,110);
 for(let i=0;i<108;i++)raw[2+i]^=(100+100*i+77*i*(i-1)/2)&255;
 const p=c.allocate(raw.length),out=c.allocate(payload.length);
 try{
  memory(c,p,raw.length).set(raw);
  assert.equal(c.archive_open(a,p,raw.length,75),1);
  assert.equal(name(c,a,0),'data/a.txt');
  assert.equal(c.archive_read(a,0,out,payload.length),payload.length);
  assert.deepEqual(Buffer.from(memory(c,out,payload.length)),payload);
  for(const [prefix,total,version] of [[109,raw.length,75],[110,109,75],[110,raw.length-1,75],[110,raw.length,135]]){
   assert.equal(c.archive_open_directory(a,p,prefix,total,version),0);
   assert.equal(c.archive_count(a),0);assert.equal(c.archive_read(a,0,out,payload.length),-1);
  }
  assert.equal(c.archive_open_directory(a,p,110,raw.length,75),1);
  assert.equal(c.archive_read(a,0,out,payload.length),-1,'directory-only reader retains no input pointer');
  assert.equal(c.archive_decode_entry(a,0,p,1,out,payload.length),-1,'wrong entry length');
 }finally{c.archive_delete(a);c.release(p);c.release(out);}
});
