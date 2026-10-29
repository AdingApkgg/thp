import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,existsSync,mkdirSync,statfsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const options=new Map();for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i];assert(['--wasm','--output'].includes(key)&&process.argv[i+1]&&!options.has(key));options.set(key,process.argv[i+1]);}
assert.equal(options.size,2);const root=resolve(import.meta.dirname,'..'),out=resolve(root,options.get('--output')),scope=relative(resolve(root,'artifacts/th14'),out);
assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope)&&!existsSync(out));mkdirSync(out,{recursive:true});
const disk=statfsSync(out);assert(disk.bavail*disk.bsize>=100*1024**3);
const bytes=readFileSync(resolve(root,options.get('--wasm'))),sha=b=>createHash('sha256').update(b).digest('hex');
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const checks=[];function check(name,run){run();checks.push(name);}
check('Initial load needs no dispatched minimum wait',()=>{const token=c.begin_wait(1);assert.equal(c.wait_ready(0n),1);assert.equal(c.wait_owns(token),0);});
check('Queued work does not expire before actual dispatch',()=>{const token=c.begin_wait(0);assert.equal(c.wait_ready(10000000000n),0);assert.equal(c.deliver_wait(token,10000000000n),0);});
check('A dispatch at clock zero still has the full60ms minimum',()=>{const token=c.begin_wait(0);assert.equal(c.dispatch_wait(token,0n),1);assert.equal(c.wait_ready(59999999n),0);assert.equal(c.deliver_wait(token,59999999n),0);assert.equal(c.wait_remaining(59999999n),1n);assert.equal(c.wait_ready(60000000n),1);assert.equal(c.deliver_wait(token,60000000n),1);});
check('ANM can observe expiry while the completion event is still queued',()=>{const token=c.begin_wait(0);assert.equal(c.dispatch_wait(token,100000000n),1);assert.equal(c.wait_ready(159999999n),0);assert.equal(c.wait_ready(160000000n),1);assert.equal(c.wait_owns(token),1);assert.equal(c.wait_ready(175000000n),1);assert.equal(c.deliver_wait(token,180000000n),1);assert.equal(c.deliver_wait(token,180000000n),0);});
check('Cancellation rejects both stale dispatch and stale completion',()=>{const token=c.begin_wait(0);assert.equal(c.dispatch_wait(token,0n),1);c.cancel_wait();assert.equal(c.wait_ready(1n),1);assert.equal(c.wait_owns(token),0);assert.equal(c.dispatch_wait(token,1n),0);assert.equal(c.deliver_wait(token,60000000n),0);});
check('A new wait owns its own dispatch and minimum interval',()=>{const old=c.begin_wait(0);assert.equal(c.dispatch_wait(old,0n),1);const token=c.begin_wait(0);assert.notEqual(old,token);assert.equal(c.dispatch_wait(old,60000000n),0);assert.equal(c.deliver_wait(old,60000000n),0);assert.equal(c.wait_ready(60000000n),0);assert.equal(c.dispatch_wait(token,100000000n),1);assert.equal(c.wait_ready(159999999n),0);assert.equal(c.wait_ready(160000000n),1);});
check('Duplicate dispatch cannot postpone an already running wait',()=>{const token=c.begin_wait(0);assert.equal(c.dispatch_wait(token,100n),1);assert.equal(c.dispatch_wait(token,50000000n),0);assert.equal(c.wait_ready(60000100n),1);});
check('Clock regression does not underflow into immediate readiness',()=>{const token=c.begin_wait(0);assert.equal(c.dispatch_wait(token,100000000n),1);assert.equal(c.wait_ready(99999999n),0);assert.equal(c.wait_remaining(99999999n),60000000n);assert.equal(c.deliver_wait(token,99999999n),0);});
check('Expiry comparison does not add an overflowing deadline',()=>{const token=c.begin_wait(0),end=(1n<<64n)-1n;assert.equal(c.dispatch_wait(token,end-60000000n),1);assert.equal(c.wait_ready(end-1n),0);assert.equal(c.wait_ready(end),1);assert.equal(c.deliver_wait(token,end),1);});
check('An initial-stage replacement invalidates a queued later-stage token',()=>{const old=c.begin_wait(0);c.begin_wait(1);assert.equal(c.wait_owns(old),0);assert.equal(c.dispatch_wait(old,0n),0);assert.equal(c.deliver_wait(old,60000000n),0);assert.equal(c.wait_ready(0n),1);});
const report={passed:true,checks,wasmSha256:sha(bytes),checkerSha256:sha(readFileSync(new URL(import.meta.url))),actualProductionWaitHelper:true,actualBrowserTiming:false,actualOriginalThreadTiming:false,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'check.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
