import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const origin=process.argv.find(x=>x.startsWith('--origin='))?.slice(9)??'https://wth.saop.cc/';
const local=process.argv.find(x=>x.startsWith('--manifest='))?.slice(11)??'tools/tmp/th06nc-production-20261120/runtime-manifest.json';
const expected=readFileSync(local),manifest=JSON.parse(expected),sha=b=>createHash('sha256').update(b).digest('hex');
const response=await fetch(new URL('th06nc/runtime-manifest.json',origin),{signal:AbortSignal.timeout(60000)});
assert.equal(response.status,200);assert.equal(sha(Buffer.from(await response.arrayBuffer())),sha(expected));
const rows=[...manifest.files,{path:'th06nc/runtime-manifest.json',bytes:expected.length,sha256:sha(expected)}],verified=[],failures=[];
let cursor=0;
async function worker(){
 while(cursor<rows.length){
  const row=rows[cursor++];let success=false;
  for(let attempt=1;attempt<=3;attempt++){
   try{
    const result=await fetch(new URL(row.path,origin),{signal:AbortSignal.timeout(90000)});assert.equal(result.status,200,row.path);
    const hash=createHash('sha256');let bytes=0;for await(const chunk of result.body){bytes+=chunk.length;hash.update(chunk);}
    assert.equal(bytes,row.bytes,row.path);assert.equal(hash.digest('hex'),row.sha256,row.path);
    assert.equal(result.headers.get('cross-origin-opener-policy'),'same-origin',row.path);assert.equal(result.headers.get('cross-origin-embedder-policy'),'require-corp',row.path);
    verified.push({path:row.path,bytes,sha256:row.sha256});success=true;
    if(verified.length%100===0)console.log(JSON.stringify({verified:verified.length,total:rows.length}));break;
   }catch(error){failures.push({path:row.path,attempt,error:String(error)});if(attempt<3)await new Promise(r=>setTimeout(r,attempt*500));}
  }
  assert.ok(success,'Public response failed: '+row.path);
 }
}
await Promise.all(Array.from({length:4},worker));
assert.equal(verified.length,rows.length);
const report={scope:'Complete public HTTPS response bodies streamed through SHA-256, matching the exact deployed standalone manifest. Content length and COOP/COEP checked for every response. No source assets or response bodies retained in the report. This proves publication identity, not a public full natural gameplay clear.',origin,sourceCommit:manifest.sourceCommit,manifestSha256:sha(expected),verified,failures,bytes:verified.reduce((n,r)=>n+r.bytes,0),passed:true};
writeFileSync('docs/porting/th06nc-production-public-http-verified.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,files:verified.length,bytes:report.bytes,retriedRequests:failures.length}));
