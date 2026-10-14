// Preparation copies frozen source bytes. Execution requires a fresh original report and its explicit SHA.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const old=resolve(root,'artifacts/th14/startup-camera-screen-correction-prepared-oct14');
const out=resolve(root,'artifacts/th14/startup-camera-resolution-control-prepared-oct15');
const expectedOriginal=resolve(root,'artifacts/th14/screen-camera-resolution-original-prepared-oct15/run-oct15/report.json');
const cameraSha='6fc589bd7c47f0757f22ebb33ee2d6647a5b53543c189d802b6781d6dbe3a391';
const mathSha='b159b3d617a522977c795351b5ff56338d5058b899ab984a590c8b50f8a9fd6e';
const fixtureSha='23cb8060c6320a06d5c4d933f99a2d8204d52ad4d00906c7426bf0f2425beaba';
const sha=b=>createHash('sha256').update(b).digest('hex');
const pin=path=>{const b=readFileSync(path);return {path,bytes:b.length,sha256:sha(b)};};
function verify(binding){const b=readFileSync(binding.path);assert.equal(b.length,binding.bytes,binding.path);assert.equal(sha(b),binding.sha256,binding.path);return b;}
function save(path,value){writeFileSync(path,JSON.stringify(value,null,2)+'\n',{flag:'wx'});return pin(path);}
const pack=words=>{const b=Buffer.alloc(words.length*4);words.forEach((v,i)=>b.writeUInt32LE(v,i*4));return b;};
const rawWords=(value,count)=>{assert.ok(Array.isArray(value)&&value.length===count);assert.ok(value.every(v=>Number.isInteger(v)&&v>=0&&v<=0xffffffff));return [...value];};

export function prepareResolutionControl(){
 assert.ok(!existsSync(resolve(out,'plan.json')),'never replace frozen preparation');
 const oldPlanPath=resolve(old,'plan.json'),oldPlan=JSON.parse(readFileSync(oldPlanPath,'utf8'));
 assert.equal(oldPlan.schema,'th14-screen-correction-control-plan-v1');assert.equal(oldPlan.frozenSources.length,15);
 const copied=[];
 for(const source of oldPlan.frozenSources){
  const bytes=verify(source.after),name=relative(resolve(old,'after'),source.after.path);
  assert.ok(name&&!name.startsWith('..')&&!isAbsolute(name));
  const destination=resolve(out,'source',name);mkdirSync(dirname(destination),{recursive:true});writeFileSync(destination,bytes,{flag:'wx'});copied.push(pin(destination));
 }
 const fixturePath=resolve(old,'fixture.cpp'),fixture=readFileSync(fixturePath);assert.equal(fixture.length,2632);assert.equal(sha(fixture),fixtureSha);
 const newFixture=resolve(out,'fixture.cpp');writeFileSync(newFixture,fixture,{flag:'wx'});
 assert.equal(pin(resolve(out,'source/cpp/game/SceneCamera.cpp')).sha256,cameraSha);
 assert.equal(pin(resolve(out,'source/cpp/game/GraphicsMath.cpp')).sha256,mathSha);
 const source=resolve(out,'source/cpp/game'),runDirectory=resolve(out,'run-oct15'),wasmPath=resolve(runDirectory,'screen.wasm');
 const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14','-Wl,--wrap=_ZN4th1112GraphicsMath7look_atENS_4Vec3ES1_S1_','-Wl,--wrap=_ZN4th1112GraphicsMath11perspectiveEffff'];
 const args=[...flags,'-I'+source,resolve(source,'SceneCamera.cpp'),resolve(source,'GraphicsMath.cpp'),newFixture,'-o',wasmPath];
 const tool=pin(fileURLToPath(import.meta.url));verify(oldPlan.compiler);
 const plan=save(resolve(out,'plan.json'),{schema:'th14-supported-resolution-screen-control-plan-v1',prepared:true,oracleStatus:'pending-original-execution',originalReportPath:expectedOriginal,requireExplicitOriginalSha256:true,
  originalProfileCompletionRequired:true,profileContract:[{label:'960',configWord:16,width:960,height:720,scaleWord:0x3fc00000},{label:'1280',configWord:20,width:1280,height:960,scaleWord:0x40000000}],
  compiler:oldPlan.compiler,compilerArguments:args,runDirectory,wasmPath,fixture:pin(newFixture),sourceFiles:copied,requiredBindings:[tool,pin(oldPlanPath),pin(fixturePath),pin(newFixture),oldPlan.compiler,...copied],
  exports:['memory','_initialize','input_buffer','parameter_buffer','matrix_buffer','run_screen'],inputWordsPerProfile:32,parameterWordsPerProfile:52,matrixWordsPerProfile:128,totalCameras:8,totalParameterWords:104,totalMatrixWords:256,
  reuseScope:'Byte-identical corrected SceneCamera6fc589, unchanged GraphicsMathb159,15 frozen dependencies and2632-byte forwarding observer fixture from the completed640 control. That640 result is not inherited as supported-resolution evidence.',
  executionCounts:{compiles:0,wasiInstances:0,originalX86:0,nativeProcesses:0,browser:0,audio:0},
  futureCommand:'C:/nvm4w/nodejs/node.exe tools/th14-startup-camera-resolution-control.mjs --execute --original-report '+expectedOriginal+' --original-sha256 <actual SHA approved by root>',
  scope:'Prepare one tiny frozen portable screen reactor and two original-report-driven runs only. No synthetic oracle, corrected source modification, production object rebuild, inventory rescan, Native execution, browser or audio.'});
 const receipt=save(resolve(out,'preparation-receipt.json'),{prepared:true,executed:false,oracleStatus:'pending-original-execution',originalReportExpectedPath:expectedOriginal,plan,tool,fixture:pin(newFixture),cameraSource:pin(resolve(source,'SceneCamera.cpp')),mathSource:pin(resolve(source,'GraphicsMath.cpp')),dependencyFiles:15,productionChanged:false,productionObjectsLinked:0,productionObjectsRebuilt:0,executionCounts:{compiles:0,wasiInstances:0,originalX86:0,nativeProcesses:0,browser:0,audio:0},scope:'Source bytes and a pending-oracle execution plan only. A supplied actual original report and its explicit verified SHA are mandatory before any compile or WASI use. No960/1280 arithmetic verdict exists at preparation.'});
 console.log(JSON.stringify({plan,receipt}));return receipt;
}

function originalProfiles(report,plan){
 assert.ok(Array.isArray(report.profiles)&&report.profiles.length===2,'two completed original profiles required');
 return plan.profileContract.map(spec=>{
  const matches=report.profiles.filter(p=>String(p.label)===spec.label);assert.equal(matches.length,1,'profile '+spec.label);const p=matches[0];
  assert.equal(p.completed,true,'original profile must complete naturally');
  assert.equal(p.declaredConfigWord,spec.configWord);assert.deepEqual(p.generatedDimensions,{width:spec.width,height:spec.height,scaleWord:spec.scaleWord});
  assert.deepEqual(p.declaredFpuState,{fpcw:0x37f,mxcsr:0x1f80,nativeMeasured:false});
  assert.ok(Array.isArray(p.originalD3dxMathCalls)&&p.originalD3dxMathCalls.length===8);assert.ok(Array.isArray(p.cameras)&&p.cameras.length===4);
  const inputWords=[],parameterWords=[],matrixWords=[],cameraOwners=[];
  for(let i=0;i<4;++i){
   const look=p.originalD3dxMathCalls[i*2],projection=p.originalD3dxMathCalls[i*2+1];
   assert.equal(look.function,'D3DXMatrixLookAtLH');assert.equal(projection.function,'D3DXMatrixPerspectiveFovLH');
   assert.equal(look.returnVerified,true);assert.equal(projection.returnVerified,true);
   assert.equal(look.originalReturnVerified,true);assert.equal(projection.originalReturnVerified,true);
   assert.equal(look.hostMathResultWrites,0);assert.equal(projection.hostMathResultWrites,0);
   assert.equal(look.returnedRegisters.eax,look.arguments[0]);assert.equal(projection.returnedRegisters.eax,projection.arguments[0]);
   assert.equal(look.returnedRegisters.esp,look.expectedEsp);assert.equal(projection.returnedRegisters.esp,projection.expectedEsp);
   assert.equal(look.outputPointer,look.arguments[0]);assert.equal(projection.outputPointer,projection.arguments[0]);
   const owner=look.arguments[0]-0x60;assert.equal(projection.arguments[0],owner+0xa0);
   const cameras=p.cameras.filter(c=>c.owner===owner);assert.equal(cameras.length,1,'matching actual camera owner');const camera=cameras[0];
   const viewport=rawWords(camera.viewportWords,6),projectionArgs=rawWords(projection.arguments.slice(1),4);
   assert.deepEqual(rawWords(camera.viewWords,16),rawWords(look.afterWords,16));assert.deepEqual(rawWords(camera.projectionWords,16),rawWords(projection.afterWords,16));
   assert.equal(camera.fovWord,projectionArgs[0]);assert.ok(Number.isInteger(camera.modeWord));assert.ok(Array.isArray(look.inputVectorWords)&&look.inputVectorWords.length===3);
   const vectors=look.inputVectorWords.flatMap(v=>rawWords(v,3));inputWords.push(...viewport,camera.fovWord,camera.modeWord);parameterWords.push(...vectors,...projectionArgs);matrixWords.push(...rawWords(look.afterWords,16),...rawWords(projection.afterWords,16));cameraOwners.push(owner);
  }
  assert.equal(inputWords.length,32);assert.equal(parameterWords.length,52);assert.equal(matrixWords.length,128);
  return {label:spec.label,configWord:spec.configWord,generatedDimensions:p.generatedDimensions,declaredFpuState:p.declaredFpuState,cameraOwners,inputWords,parameterWords,matrixWords};
 });
}

export async function executeResolutionControl(originalPath,originalSha){
 assert.match(originalSha,/^[a-f0-9]{64}$/,'an explicit actual original-report SHA is required');
 const plan=JSON.parse(readFileSync(resolve(out,'plan.json'),'utf8'));assert.equal(plan.schema,'th14-supported-resolution-screen-control-plan-v1');
 assert.equal(resolve(originalPath),resolve(plan.originalReportPath),'fixed original report path');
 for(const b of plan.requiredBindings)verify(b);
 const original=pin(resolve(originalPath));assert.equal(original.sha256,originalSha,'actual original report SHA');
 const profiles=originalProfiles(JSON.parse(readFileSync(original.path,'utf8')),plan);
 assert.ok(!existsSync(plan.runDirectory),'new run directory required');mkdirSync(plan.runDirectory);
 const inputs=save(resolve(plan.runDirectory,'inputs.json'),{originalReport:original,profiles,scope:'Only actual original-report raw camera fields/arguments and oracle matrices, with no scalar reconstruction or input correction.'});
 const env={...process.env,TEMP:plan.runDirectory,TMP:plan.runDirectory,TMPDIR:plan.runDirectory};execFileSync(plan.compiler.path,plan.compilerArguments,{cwd:root,env,stdio:'inherit',windowsHide:true});
 const bytes=readFileSync(plan.wasmPath),module=await WebAssembly.compile(bytes),imports=WebAssembly.Module.imports(module),exports=WebAssembly.Module.exports(module);
 assert.ok(imports.every(x=>x.module==='wasi_snapshot_preview1'));for(const name of plan.exports)assert.ok(exports.some(x=>x.name===name));assert.ok(exports.every(x=>!/(?:sdl|audio|th11|native|play)/i.test(x.name)));
 const {WASI}=await import('node:wasi'),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),instance=await WebAssembly.instantiate(module,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const core=instance.exports,results=[];
 const read=(pointer,count)=>{pointer>>>=0;assert.equal(pointer%4,0);assert.ok(pointer+count*4<=core.memory.buffer.byteLength);return Array.from({length:count},(_,i)=>new DataView(core.memory.buffer).getUint32(pointer+i*4,true));};
 for(const profile of profiles){
  const p=core.input_buffer()>>>0;assert.equal(p%4,0);assert.ok(p+128<=core.memory.buffer.byteLength);profile.inputWords.forEach((v,i)=>new DataView(core.memory.buffer).setUint32(p+i*4,v,true));assert.equal(core.run_screen(),1);
  const parameters=read(core.parameter_buffer(),52),matrices=read(core.matrix_buffer(),128),parameterDifferences=[],matrixDifferences=[];
  parameters.forEach((v,i)=>{if(v!==profile.parameterWords[i])parameterDifferences.push({camera:i/13|0,word:i%13,portWord:v,originalWord:profile.parameterWords[i]});});matrices.forEach((v,i)=>{if(v!==profile.matrixWords[i])matrixDifferences.push({camera:i/32|0,matrix:i%32<16?'view':'projection',word:i%16,portWord:v,originalWord:profile.matrixWords[i]});});
  const parameterPath=resolve(plan.runDirectory,profile.label+'-parameters.u32'),matrixPath=resolve(plan.runDirectory,profile.label+'-matrices.u32');writeFileSync(parameterPath,pack(parameters),{flag:'wx'});writeFileSync(matrixPath,pack(matrices),{flag:'wx'});
  results.push({label:profile.label,parameters,matrices,parameterDifferenceCount:parameterDifferences.length,matrixDifferenceCount:matrixDifferences.length,parameterDifferences,matrixDifferences,parameterOutput:pin(parameterPath),matrixOutput:pin(matrixPath)});
 }
 const report={controlExecuted:true,comparisonPassed:results.every(r=>r.parameterDifferenceCount===0&&r.matrixDifferenceCount===0),profileCount:2,cameraCount:8,comparedParameterWords:104,comparedMatrixWords:256,results,originalReport:original,inputs,plan:pin(resolve(out,'plan.json')),fixture:plan.fixture,runner:pin(fileURLToPath(import.meta.url)),sourceFiles:plan.sourceFiles,wasm:pin(plan.wasmPath),imports,exports,
  executionCounts:{compiles:1,wasiInstances:1,screenCalls:8,mathCalls:16,originalX86:0,nativeProcesses:0,browser:0,audio:0},productionChanged:false,productionObjectsRebuilt:0,nativeEquivalent:false,completeGame:false,
  scope:'Current corrected production SceneCamera.screen on the actual original960/1280 camera viewport/FOV fields; forwarding observers compare104 raw parameters/256 matrix words. Original pinned D3DX FPCW37f/MXCSR1f80 baseline is controlled, not a measured Native CPU overlay. No inherited640 verdict, original execution by this runner, Renderer/GPU, UI at these resolutions, whole cold startup or whole-game1:1 claim.'};
 save(resolve(plan.runDirectory,'report.json'),report);console.log(JSON.stringify({comparisonPassed:report.comparisonPassed,results:results.map(x=>({label:x.label,parameters:x.parameterDifferenceCount,matrices:x.matrixDifferenceCount})),report:resolve(plan.runDirectory,'report.json')}));return report;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args=process.argv.slice(2);
 if(args.length===1&&args[0]==='--prepare')prepareResolutionControl();
 else if(args.length===5&&args[0]==='--execute'&&args[1]==='--original-report'&&args[3]==='--original-sha256')await executeResolutionControl(args[2],args[4]);
 else if(args.length===0)console.log('Prepare only: --prepare. Execution additionally requires --execute --original-report <fixed actual report path> --original-sha256 <actual SHA>.');
 else throw Error('Only --prepare or explicitly pinned --execute is supported.');
}
