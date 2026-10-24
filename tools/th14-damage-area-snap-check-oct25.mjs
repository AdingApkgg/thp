import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),wasmPath=resolve(process.argv[2]),nativePath=resolve(process.argv[3]),reportPath=resolve(process.argv[4]);
const bytes=read(wasmPath),nativeBytes=read(nativePath),proof=JSON.parse(nativeBytes),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
assert.equal(proof.originalInstructionsOrMathPatched,false);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const conversion=new DataView(new ArrayBuffer(4));const float=x=>{conversion.setUint32(0,x,true);return conversion.getFloat32(0,true);};
let differences=0,frames=0;const first=[];const counts={};
for(const [caseIndex,row] of proof.rows.entries()){
    c.begin(...row.input.slice(0,3).map(float),row.input[3]);
    for(const [frame,expected] of row.frames.entries()){
        c.tick();++frames;
        for(let field=0;field<expected.length;++field){const actual=c.value(field)>>>0;if(actual!==expected[field]){
            ++differences;counts[field]=(counts[field]??0)+1;
            if(first.length<20)first.push({caseIndex,input:row.input,frame:frame+1,field,native:expected[field],portable:actual});
        }}
    }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:differences===0,cases:proof.rows.length,frames,fields:proof.offsets.length,differences,differenceCounts:counts,firstDifferences:first,wasmSha256:sha(bytes),nativeDataSha256:sha(nativeBytes),executableSha256:proof.executableSha256,originalInstructionsOrMathPatched:false,sourceHashes:Object.fromEntries(['runtimes/th12/th12_web/cpp/game/ShotDamageTh14.cpp','runtimes/th12/th12_web/tests/cpp/th14-damage-area-snap-fixture.cpp','tools/th14-damage-area-snap-native-oct25.py','tools/th14-damage-area-snap-check-oct25.mjs'].map(p=>[p,sha(read(resolve(root,p)))])),scope:'Actual original44e005 loop plus403cd0/403df0/floor with synthetic finite stationary mode0 area positions, active/inactive and four rates, four successive updates. Exact16 scalar fields including raw XYZ, radius, timer, damage counters and stamp. No target instruction or math-service patches. Does not prove moving modes, allocation, actual campaign, all gameplay, GPU or audio.',completeGame:false,nativeEquivalent:false};
write(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:report.passed,cases:report.cases,frames,differences,first:first.slice(0,3)}));
if(!report.passed)process.exitCode=1;
