"""Overlay the new TH14 runtime while retaining the tested hidden-sidebar UI."""
from pathlib import Path
import argparse,hashlib,json,shutil
R=Path(__file__).resolve().parents[1]
P=R/'artifacts/th14/sidebar-visibility-nov05/launcher/launcher-report.json'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def main(runtime,out):
 runtime=runtime.resolve();out=out.resolve()
 assert runtime.is_relative_to(R/'artifacts/th14') and out.is_relative_to(R/'artifacts/th14') and not out.exists()
 assert shutil.disk_usage(R).free>=100*1024**3
 parent_raw=P.read_bytes();parent=json.loads(parent_raw)
 assert parent['sidebarVisibilityCandidate'] and parent['wasmSha256']=='7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325'
 raw=(runtime/'package-report.json').read_bytes();package=json.loads(raw)
 assert package['prepared'] and package['backend']=='gles' and not package['browserRun']
 files={name:row for name,row in parent['files'].items()if not name.startswith('runtime/')}
 for name,row in package['files'].items():files['runtime/th14/'+name]=dict(path=(runtime/name).relative_to(R).as_posix(),**row)
 for name,row in files.items():
  path=(R/row['path']).resolve();assert path.is_relative_to(R) and path.stat().st_size==row['bytes']
  with path.open('rb')as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256'],name
 out.mkdir(parents=True);changes={}
 def put(name,data):
  path=out/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  files[name]=dict(path=path.relative_to(R).as_posix(),bytes=len(data),sha256=SHA(data));changes[name]=files[name]
 managed=json.loads((runtime/'manifest.json').read_bytes())
 put('manifest.json',(json.dumps(dict(game='th14',version='1.00b-gles-stage-restore-candidate',completeGame=False,
  nativeEquivalent=False,execution=dict(managed['execution'],bytes=files['runtime/th14/th14-sdl.wasm']['bytes'])),indent=2)+'\n').encode())
 for name in ['Th14StageRestoreDelivery.mjs','Th14StageRestoreProtocol.mjs','Th14StageRestoreWorker.mjs']:
  assert 'runtime/th14/'+name in files
 entries=[dict(url='./',revision=files['index.html']['sha256'])]
 entries +=[dict(url=name,revision=row['sha256'])for name,row in sorted(files.items())
  if name not in ['files.json','app-shell-sw.js'] and not name.startswith(('packages/','runtime/th14/fonts/','runtime/th14/music/'))]
 build_id=SHA(json.dumps(entries,separators=(',',':')).encode())[:20]
 sw=R/'runtimes/th12/th12_web/launcher/src/app-shell-sw.js';worker=sw.read_bytes()
 assert b'__APP_SHELL_BUILD_ID__'in worker and b'self.__WB_MANIFEST'in worker
 put('app-shell-sw.js',worker.replace(b'__APP_SHELL_BUILD_ID__',build_id.encode()).replace(b'self.__WB_MANIFEST',json.dumps(entries,separators=(',',':')).encode()))
 put('files.json',(json.dumps({name:row['sha256']for name,row in sorted(files.items())if name!='files.json'},indent=2)+'\n').encode())
 for name,row in parent['files'].items():
  if not name.startswith('runtime/') and name not in changes:assert files[name]==row
 report=dict(parent);report.update(files=files,buildId=build_id,wasmSha256=package['wasmSha256'],
  parentReport=P.relative_to(R).as_posix(),parentReportSha256=SHA(parent_raw),
  runtimeReport=(runtime/'package-report.json').relative_to(R).as_posix(),runtimeReportSha256=SHA(raw),
  stageRestoreDeliveryCandidate=True,roots=[*parent['roots'],runtime.relative_to(R).as_posix(),out.relative_to(R).as_posix()],
  physicalBytesWritten=sum(path.stat().st_size for path in out.rglob('*')if path.is_file()),
  payloadFilesCopied=False,defaultPreviewChanged=False,browserRun=False,browserAcceptance=False,completeGame=False,
  sourceBindings={sw.relative_to(R).as_posix():dict(bytes=len(worker),sha256=SHA(worker))},
  toolSha256=SHA(Path(__file__).read_bytes()),scope='Full TH14 independent restore GLES candidate; existing hidden-sidebar UI retained byte-for-byte. Browser and original scheduling acceptance remain open.')
 (out/'launcher-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(prepared=True,buildId=build_id,physicalBytesWritten=report['physicalBytesWritten'],payloadFilesCopied=False,browserAcceptance=False)))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.runtime,a.output)
