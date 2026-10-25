// Original effect149 family versus frozen production animation objects.
import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync as mkdir,existsSync as exists} from 'node:fs';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {resolve,relative,isAbsolute} from 'node:path';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),runtime=resolve(root,'runtimes/th12'),sha=x=>createHash('sha256').update(x).digest('hex');
const options=new Map();let check=false;
for(let i=2;i<process.argv.length;i++){const key=process.argv[i];if(key==='--check'){assert(!check);check=true;continue;}assert(['--output','--build'].includes(key)&&process.argv[i+1]&&!options.has(key));options.set(key,process.argv[++i]);}
assert(options.has('--output'),'Declare a new private --output directory');
const home=resolve(root,options.get('--output')),scope=relative(resolve(root,'artifacts/th14'),home);assert(scope&&!scope.startsWith('..')&&!isAbsolute(scope)&&!exists(home));mkdir(home,{recursive:true});
const buildPath=resolve(root,options.get('--build')??'artifacts/th14/stage-item-retirement-oct25/curve-origin-observer-oct26/observer-build.json'),buildBytes=read(buildPath),base=JSON.parse(buildBytes);
for(const row of base.objectBindings)assert.equal(sha(read(row.path)),row.sha256);
for(const[name,digest]of Object.entries({...base.sourceHashes,...base.headerHashes})){
 const actual=sha(read(resolve(runtime,name)));
 if(name.endsWith('/ResourceCrypt.cpp'))assert.equal(actual,'a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45');
 else assert.equal(actual,digest,'Production source changed: '+name);
}
const fixture=resolve(runtime,'th12_web/tests/cpp/th14-effect149-retirement-fixture.cpp'),fixtureSha=sha(read(fixture)),toolSha=sha(read(import.meta.filename));
const nativeTool=resolve(root,'tools/th14-effect149-retirement-evidence-oct26.py');
const python=process.env.TH_NATIVE_PYTHON??'py';execFileSync(python,[...(process.env.TH_NATIVE_PYTHON?[]:['-3']),nativeTool,'--check','--native-words',resolve(home,'native-words.json')],{cwd:root,env:{...process.env,PYTHONUTF8:'1'},stdio:'inherit',windowsHide:true});
const nativeReportPath=resolve(root,'docs/porting/th14-effect149-retirement-component-oct26.json'),nativeReport=JSON.parse(read(nativeReportPath));assert.equal(nativeReport.toolSha256,sha(read(nativeTool)));assert.equal(nativeReport.selectedNativeWordsSha256,sha(read(resolve(home,'native-words.json'))));
const wasmPath=resolve(home,'observer.wasm');execFileSync(resolve(runtime,'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...base.objectBindings.map(row=>row.path),'-o',wasmPath],{cwd:root,env:{...process.env,TEMP:home,TMP:home},stdio:'inherit',windowsHide:true});
assert.equal(sha(read(fixture)),fixtureSha);assert.equal(sha(read(import.meta.filename)),toolSha);
const archive=JSON.parse(read(resolve(root,'artifacts/archive-differential/th14.json'))),source=name=>read(resolve(archive.extraction,name));
const wasm=read(wasmPath),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(wasm,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const put=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const ascii=source('ascii.anm'),effect=source('effect.anm');for(const[name,bytes]of[['ascii.anm',ascii],['effect.anm',effect]])assert.equal(sha(bytes),nativeReport.resources.find(row=>row.name===name).sha256);assert.equal(c.open(put(ascii),ascii.length,put(effect),effect.length),1);
const cases=JSON.parse(read(resolve(home,'native-words.json')));
const linkFields=[240,291,292,293,294];
const differences=[];let frames=0,vmRows=0,geometryRows=0;
for(const [index,profile]of cases.entries()){
 assert.equal(c.begin(profile.rate,profile.seed,profile.z,profile.xDelta),1);let freed=[];
 for(const expected of profile.frames){
  if(expected.frame)assert.equal(c.step(),1);assert.equal(c.capture(),1);
  const mapping=new Map(Array.from({length:c.created()},(_,i)=>[c.creation_id(i)>>>0,i+1]));mapping.set(0,0);
  const rows=Array.from({length:c.count()},(_,i)=>Array.from({length:303},(_,k)=>c.field(i,k)>>>0));
  for(const row of rows){row[0]=mapping.get(row[0]);for(const k of linkFields)row[k]=mapping.get(row[k]);}
  if(rows.length!==expected.rows.length)differences.push({index,frame:expected.frame,kind:'count',native:expected.rows.length,portable:rows.length});
  for(let r=0;r<Math.min(rows.length,expected.rows.length);r++)for(let k=0;k<303;k++)if(rows[r][k]!==expected.rows[r][k]){
   if(differences.length<100)differences.push({index,frame:expected.frame,row:r,script:rows[r][2],fieldIndex:k,native:expected.rows[r][k],portable:rows[r][k]});
  }
  const geometry=[];for(let at=0;at<c.geometry_count();at+=13){const row=Array.from({length:13},(_,k)=>c.geometry_field(at+k)>>>0);row[0]=mapping.get(row[0]);geometry.push(row);}
  if(JSON.stringify(geometry)!==JSON.stringify(expected.geometry)&&differences.length<100)differences.push({index,frame:expected.frame,kind:'geometry',native:expected.geometry,portable:geometry});
  const rng=Array.from({length:4},(_,k)=>c.rng(k)>>>0);if(JSON.stringify(rng)!==JSON.stringify(expected.rng)&&differences.length<100)differences.push({index,frame:expected.frame,kind:'rng',native:expected.rng,portable:rng});
  if(expected.frame){const alive=new Set(rows.map(r=>r[0]));const retired=Array.from(mapping.values()).filter(n=>n&&!alive.has(n)&&!freed.includes(n));assert(retired.length<=1);freed.push(...retired);}
  if(JSON.stringify(freed)!==JSON.stringify(expected.freed)&&differences.length<100)differences.push({index,frame:expected.frame,kind:'freed',native:expected.freed,portable:freed});
  // At creation no draw traversal has run. Subsequent heads come directly
  // from the production manager; all VM link fields are compared above.
  const layers=Array.from({length:36},(_,i)=>mapping.get(c.layer_head(i)>>>0));if(JSON.stringify(layers)!==JSON.stringify(expected.layers)&&differences.length<100)differences.push({index,frame:expected.frame,kind:'layers'});
  ++frames;vmRows+=rows.length;geometryRows+=geometry.length;
 }
}
const diagnostics={comparedProfiles:cases.length,frames,vmRows,wordsPerVm:303,geometryRows,wasmSha256:sha(wasm),differences,allComparedValuesEqual:differences.length===0,completeGame:false,nativeEquivalent:false};
write(resolve(home,'comparison.json'),JSON.stringify(diagnostics,null,2)+'\n');
assert.equal(differences.length,0,'Retained native component differs; see private comparison.json');
assert.equal(frames,5808);assert.equal(vmRows,5632);assert.equal(geometryRows,2944);
const report={schema:'th14/effect149-retirement-portable/1',passed:true,finiteComponentOnly:true,profiles:cases.length,observations:frames,vmRows,selectedWordsPerVm:303,geometryRows,positionBytesPerGeometry:48,allSelectedVmAndGeometryWordsEqual:true,allObservedRngReleaseOrderAndLayerHeadsEqual:true,handleComparison:'Allocation ordinals normalize declared external Native allocations versus portable pooled slots; handles and linked IDs use the same mapping. Raw handle equality is not asserted.',wasmSha256:sha(wasm),fixtureSha256:fixtureSha,toolSha256:toolSha,nativeReportSha256:sha(read(nativeReportPath)),nativeSelectedWordsSha256:nativeReport.selectedNativeWordsSha256,productionObjectBuildSha256:sha(buildBytes),productionObjectCount:base.objectBindings.length,productionObjectsReused:true,productionChanged:false,strictFullCampaignGateUnchanged:true,limitations:[...nativeReport.limitations.filter(s=>!s.includes('portable implementation comparison')),'This portable component compares 303 selected VM words and geometry, not complete native VM/pool bytes. Registry links and layer heads compare; native and portable allocator addresses differ.','Only the declared isolated family and initial position/rotation, rate and seeds are inputs. No native computed VM, geometry, RNG or lifecycle output is supplied to the portable runtime.','No full campaign pass, actual scene GPU/PCM, ordinary browser/persistence or whole-game equivalence is proved.'],completeGame:false,nativeEquivalent:false};
write(resolve(home,'verified.json'),JSON.stringify(report,null,2)+'\n');
const target=resolve(root,'docs/porting/th14-effect149-retirement-verified-oct26.json');if(check)assert.deepEqual(report,JSON.parse(read(target)));else write(target,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,profiles:cases.length,frames,vmRows,geometryRows,wasmSha256:sha(wasm)}));
