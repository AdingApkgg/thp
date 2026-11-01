import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync,existsSync,statfsSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),options=new Map();
for(let i=2;i<process.argv.length;i+=2){const key=process.argv[i]?.replace(/^--/,'');assert(['build','native','output','require-pass'].includes(key)&&process.argv[i+1]&&!options.has(key));options.set(key,process.argv[i+1]);}
for(const key of ['build','native','output','require-pass'])assert(options.has(key),`Missing --${key}`);
assert(['true','false'].includes(options.get('require-pass')));
const output=resolve(root,options.get('output')),scope=relative(resolve(root,'artifacts/th14'),output);
assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope)&&!existsSync(output));
const disk=statfsSync(root);assert(disk.bavail*disk.bsize>=100*1024**3);
mkdirSync(output);
const sha=b=>createHash('sha256').update(b).digest('hex');
const buildPath=resolve(root,options.get('build')),build=JSON.parse(read(buildPath));
for(const [name,digest]of Object.entries({...build.sourceHashes,...build.headerHashes}))assert.equal(sha(read(resolve(build.sourceSnapshotRoot,name))),digest,name);
for(const binding of build.objectBindings)assert.equal(sha(read(binding.path)),binding.sha256,binding.path);
const nativePath=resolve(root,options.get('native')),native=JSON.parse(read(nativePath));
assert(native.actualOriginalDriverAndBeamExecuted&&native.syntheticCallFramesDeclared&&native.originalInstructionsPatched===0);
const mixed=!!native.mixedInterpolationCases;
assert.equal(native.rows.length,mixed?768:8448);
assert.equal(sha(read(resolve(nativePath,'../observer-source.py'))),native.toolSha256);
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
assert.equal(sha(read(compiler)),build.compilerSha256);
const fixture=resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-interpolator-stack-fixture-nov02.cpp'),wasmPath=resolve(output,'fixture.wasm');
const env={...process.env,TEMP:output,TMP:output};
execFileSync(compiler,[...build.flags,...build.linkFlags,fixture,...build.objectBindings.map(x=>x.path),'-o',wasmPath],{cwd:root,env,windowsHide:true,stdio:'pipe',timeout:120000});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),wasm=read(wasmPath);
const {instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
const fields=['position','color','alpha','scale','extraScale','textureScale','rotation','color2','alpha2','scrollX','scrollY'];
const asBits=v=>{const b=new ArrayBuffer(4);new DataView(b).setFloat32(0,v,true);return new DataView(b).getUint32(0,true);};
let count=0,failures=0;const firstDifferences=[],failureCounts={},firstDifferenceByField={};
for(const row of native.rows){
    const status=mixed?c.run_mask(row.mask,row.vectorMode,row.rgbMode,row.vec2Mode,row.duration,asBits(row.rate),+(row.x87ControlWord===0x037f)):
        c.run(fields.indexOf(row.field),row.mode,row.duration,asBits(row.rate),+(row.x87ControlWord===0x037f));
    assert.equal(status,0,JSON.stringify(row));
    const expected=[+(row.writeMask===0xffffffff),row.retainedWord,row.retainedWord,row.beamLengthWord,row.beamLengthWord];
    const actual=Array.from({length:5},(_,i)=>c.word(i)>>>0);
    const different=actual.some((x,i)=>x!==expected[i]);
    if(different){failures++;failureCounts[row.field]=(failureCounts[row.field]||0)+1;
        const difference={field:row.field,mode:row.mode,mask:row.mask,vectorMode:row.vectorMode,rgbMode:row.rgbMode,vec2Mode:row.vec2Mode,duration:row.duration,rate:row.rate,x87ControlWord:row.x87ControlWord,expected,actual};
        firstDifferenceByField[row.field]??=difference;
        if(firstDifferences.length<32)firstDifferences.push(difference);
    }
    count++;
}
const proof={passed:failures===0,cases:count,failures,failureCounts,firstDifferences,firstDifferenceByField,
    actualCppEcl308FactoryInterpreterAndBeamExecuted:true,actualOriginalAnimationDriverAndBeamExecuted:true,
    all32ModesAnd11InterpolatorFields:!mixed,mixedInterpolationOrderCases:mixed,syntheticVmAndStackInputsDeclared:true,
    originalEclAllocationAndWholeGameNotExecuted:true,nativeExecutableSha256:native.originalExecutableSha256,
    nativeProofSha256:sha(read(nativePath)),fixtureSha256:sha(read(fixture)),checkerSha256:sha(read(new URL(import.meta.url))),
    wasmSha256:sha(wasm),engineBuildSha256:sha(read(buildPath)),engineObjectCount:build.objectBindings.length,
    sourceHashes:build.sourceHashes,headerHashes:build.headerHashes,nativeValuesProvidedToPortableEngine:false,
    productionIntegrated:false,completeGame:false,nativeEquivalent:false};
write(resolve(output,'verified.json'),JSON.stringify(proof,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:proof.passed,cases:count,failures,failureCounts,firstDifferenceByField}));
if(options.get('require-pass')==='true')assert(proof.passed,'Actual C++/original component mismatch; retained report records differences');
