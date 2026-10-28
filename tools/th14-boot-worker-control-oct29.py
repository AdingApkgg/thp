"""Prepare a test-only boot/player ANM rejection overlay; keep production intact."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launcher-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--resource',choices=['front.anm','sig.anm','ascii.anm','text.anm','pl00.anm','pl00b.anm','pl01.anm','pl01b.anm','pl02.anm','pl02b.anm'],default='front.anm');a=p.parse_args()
    source=a.launcher_report.resolve(strict=True);out=a.output.resolve();assert source.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('boot_control_storage',R/'tools/th14-test-storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out,100*1024**3,128*1024**2)
    original=source.read_bytes();report=json.loads(original);assert report['candidateOnly']and report['prepared']and not report['browserAcceptance'];files=report['files']
    def read(name):
        row=files[name];raw=(R/row['path']).read_bytes();assert len(raw)==row['bytes']and SHA(raw)==row['sha256'];return raw
    def put(name,raw):
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);files[name]=dict(path=target.relative_to(R).as_posix(),bytes=len(raw),sha256=SHA(raw))
    name='runtime/th14/Th14ArchiveDecodeEndpoint.mjs';endpoint=read(name);marker=b"    if (command === 'decode') {\n";assert endpoint.count(marker)==1
    rejection='TH14_TEST_ONLY_BOOT_FRONT_REJECTION'if a.resource=='front.anm'else'TH14_TEST_ONLY_BOOTSTRAP_REJECTION'if a.resource in ('sig.anm','ascii.anm','text.anm')else'TH14_TEST_ONLY_SELECTED_PLAYER_REJECTION'
    failure=f"      if (Array.isArray(message.names) && message.names.includes('{a.resource}')) throw new Error('{rejection}');\n".encode()
    put(name,endpoint.replace(marker,marker+failure,1))
    managed=json.loads(read('runtime/th14/runtime-files.json'));managed['files']['Th14ArchiveDecodeEndpoint.mjs']={k:files[name][k]for k in ('bytes','sha256')}
    put('runtime/th14/runtime-files.json',(json.dumps(managed,indent=2)+'\n').encode());put('files.json',(json.dumps({n:r['sha256']for n,r in sorted(files.items())if n!='files.json'},indent=2)+'\n').encode())
    report['roots'].append(out.relative_to(R).as_posix());report.update(testOnlyFaultInjection=True,productionFilesModified=False,sourceReport=source.relative_to(R).as_posix(),sourceReportSha256=SHA(original),faultResource=a.resource,faultMarker=rejection,controlToolSha256=SHA(Path(__file__).read_bytes()),scope='Test-only worker response rejection for one selected resource; unchanged main Wasm and all original production files. Not a playable release.')
    (out/'launcher-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(testOnly=True,modifiedProduction=False,mainWasmSha256=report['wasmSha256'],resource=a.resource)))
if __name__=='__main__':main()
