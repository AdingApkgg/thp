"""Build the exported TH143 V154 C++ core with WASI SDK34 (no original assets)."""
from pathlib import Path
import concurrent.futures,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
source=ROOT/'source-tree';manifest=json.loads((ROOT/'source-manifest.json').read_text())
sdk=Path(os.environ['WASI_SDK_PATH']);compiler=sdk/'bin'/('clang++.exe'if os.name=='nt'else 'clang++')
out=Path(sys.argv[1]).resolve()if len(sys.argv)>1 else ROOT/'build';out.mkdir(parents=True,exist_ok=True)
if os.name=='nt':os.environ.update(TEMP=str(out),TMP=str(out))
for row in manifest['files']:
 assert hashlib.sha256((source/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=143','-I',str(source/'runtimes/th12/th12_web/cpp/game')]
def compile_one(name):
 obj=out/(hashlib.sha256(name.encode()).hexdigest()[:24]+'.o')
 subprocess.run([str(compiler),*flags,'-c',name,'-o',str(obj)],cwd=source,check=True)
 return obj
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:objects=list(pool.map(compile_one,manifest['sources']))
args=[*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',*[str(p)for p in objects],'-o',str(out/'play.wasm')]
rsp=out/'link.rsp';rsp.write_text('\n'.join('"'+a.replace('\\','/').replace('"','\\"')+'"'for a in args)+'\n')
subprocess.run([str(compiler),'@'+str(rsp)],cwd=source,check=True)
print(json.dumps(dict(passed=True,objects=len(objects),wasmSha256=hashlib.sha256((out/'play.wasm').read_bytes()).hexdigest(),adoptedWasmSha256=manifest['adoptedWasmSha256'])))
