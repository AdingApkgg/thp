"""Audit actual optimized provider stores and unchanged shared-title controls."""
from pathlib import Path
import hashlib,importlib,json,os,re,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/camera-right-pair-nov12';O=H/'object-audit';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes());prep=load(H/'prepared.json');S=Path(prep['sourceRoot'])
base=load(R/'artifacts/th14/ascii-queue-layout-nov12/current-provider-bindings.json');candidate=load(H/'candidate/build.json');cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';dump=cc.with_name('llvm-objdump.exe')
trace_path=R/'artifacts/th14/camera-store-order-nov07/verified.json';trace=load(trace_path)
roles=load(R/'artifacts/th14/camera-roles-nov12-v3/checked.json');assert roles['roles']['world_camera']['address']=='0x4d9514' and not roles['originalWorldRightQwordNaturallyAligned'] and roles['originalWorldRightQwordWithinMeasuredCacheLine']
assert not trace['unicornArithmeticAccepted'] and not trace['simdHardwareAtomicityOrWholeThreadSchedulingAccepted']
sys.path.insert(0,str(R/'tools'));Image=importlib.import_module('th12-pe').Image;exe=Image('H:/Games/th/14/th14.exe');dll=Image('C:/Windows/SysWOW64/d3dx9_43.dll')
assert hashlib.sha256(exe.data).hexdigest()==trace['executableSha256'] and hashlib.sha256(dll.data).hexdigest()==trace['dllSha256']
decoder=importlib.import_module('capstone').Cs(3,4);native=[]
for case in trace['cases']:
 if case['entry']!='0x446400':continue
 rows=[w for w in case['writes'] if w['offset']<96];assert [(w['offset'],w['bytes']) for w in rows]==[(48,8),(56,4),(48,4),(52,4),(56,4)]
 for row in rows:
  pc=int(row['pc'],16);pe=exe if pc<0x10000000 else dll;ins=next(decoder.disasm(pe.read(pc,15),pc));assert hashlib.sha256(bytes(ins.bytes)).hexdigest()==row['instructionSha256']
 native.append(rows)
assert len(native)==2
def run(cmd,path):
 with path.open('wb') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env={**os.environ,'TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)})
def inspect(path,backend,mode):
 text=subprocess.check_output([str(dump),'-dr','--demangle',str(path)],text=True,timeout=30);out=O/f'{backend}-{mode}.txt';out.write_text(text)
 symbols=list(re.finditer(r'^\s*[0-9a-f]+ <(.+)>:\s*$',text,re.M));methods={}
 for i,m in enumerate(symbols):
  if m.group(1) not in ['th11::SceneCamera::perspective()','th11::SceneCamera::screen()']:continue
  body=text[m.end():symbols[i+1].start() if i+1<len(symbols) else len(text)]
  pair=len(re.findall(r'\bi64\.atomic\.store\b',body));words=[int(v) for v in re.findall(r'\bi32\.atomic\.store\s+(\d+)',body)]
  if m.group(1).endswith('perspective()'):
   assert pair==(1 if mode=='candidate' else 0)
   assert words[:32]==[76,92,108,124,80,96,112,128,84,100,116,132,88,104,120,136,140,144,148,152,156,164,168,172,176,160,180,184,188,192,196,200]
   if mode=='candidate':assert words[32:]==[56,56,0,52,56],words[32:]
  else:assert pair==0 and len(words)==32
  methods[m.group(1)]=dict(atomic64Stores=pair,atomic32StoreOffsets=words)
 assert len(methods)==2
 return dict(backend=backend,mode=mode,objectSha256=sha(path),disassemblyPath=out.relative_to(R).as_posix(),disassemblySha256=sha(out),methods=methods)
results=[]
for mode,b in [('baseline',base),('candidate',candidate)]:
 row=next(r for r in b.get('currentProviders',b.get('objects')) if Path(r['source']).name=='SceneCamera.cpp');obj=Path(row['object']);obj=obj if obj.is_absolute() else R/obj;assert sha(obj)==row['objectSha256'];results.append(inspect(obj,'sdk',mode))
browser=load(R/'artifacts/th14/ascii-queue-layout-nov12/browser/build.json');sdk=R/'runtimes/th12/tools/emsdk';emcc=sdk/'upstream/emscripten/emcc.py';config=sdk/'.emscripten'
assert sha(emcc)==browser['compilerSha256'] and sha(config)==browser['configurationSha256']
for mode,root in [('baseline',R),('candidate',S)]:
 flags=[('-I'+str(root/Path(v[2:]).relative_to(R))) if v.startswith('-I') and Path(v[2:]).is_relative_to(R/'runtimes/th12') else v for v in browser['flags']]
 obj=O/f'browser-{mode}.o';env={**os.environ,'EM_CONFIG':str(config),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'EMCC_CORES':'2','TEMP':str(O),'TMP':str(O),'TMPDIR':str(O)}
 with (O/f'browser-{mode}.log').open('wb') as log:subprocess.run([sys.executable,str(emcc),*flags,'-c',str(root/'runtimes/th12/th12_web/cpp/game/SceneCamera.cpp'),'-o',str(obj)],cwd=R/'runtimes/th12',stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120,env=env)
 results.append(inspect(obj,'browser',mode))
controls=[]
for title,worker in [(12,True),(13,True),(16,True),(14,False)]:
 for name in ['SceneCamera.cpp','SceneCompositor.cpp']:
  hashes=[]
  for mode,root in [('baseline',R),('candidate',S)]:
   flags=[v for v in base['flags'] if worker or not v.startswith('-DTH14_')];flags=[f'-DPORT_TITLE={title}' if v=='-DPORT_TITLE=14' else ('-I'+str(root/Path(v[2:]).relative_to(R))) if v.startswith('-I') and Path(v[2:]).is_relative_to(R/'runtimes/th12') else v for v in flags]
   obj=O/f'control-{title}-{name}-{mode}.o';run([str(cc),*flags,'-c',str(root/'runtimes/th12/th12_web/cpp/game'/name),'-o',str(obj)],obj.with_suffix('.log'));hashes.append(sha(obj))
  assert hashes[0]==hashes[1],(title,name,hashes);controls.append(dict(title=title,worker=worker,unit=name,byteIdentical=True,sha256=hashes[0]))
report=dict(originalRightStoreProtocol=native[0],nativeWorldCamera='0x4d9514',nativeRightQwordNaturallyAligned=False,nativeRightQwordAddress='0x4d9544',nativeRightQwordContainedWithinCacheLine=True,nativeCachedImageMappingAssumptionExplicit=True,rawCachedInLinePairAtomicitySupportedByIntelManual=True,roleCorrectionProof='artifacts/th14/camera-roles-nov12-v3/checked.json',cppSharedOwnerAlignmentVerifiedSeparately=True,backends=results,controls=controls,allEightControlPairsByteIdentical=True,nativeTraceSha256=sha(trace_path),noWholeCameraAtomicityClaim=True,oldFullCameraDifferenceCauseNotProved=True,newGameRuns=0,newGpuRuns=0,rootProductionSourcesChanged=False,completeGame=False,toolSha256=sha(Path(__file__)))
(O/'checked.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(backends=len(results),controlPairs=len(controls),rightPairAtomic64=True,normalizedScalarStores=True,rootProductionSourcesChanged=False)))
