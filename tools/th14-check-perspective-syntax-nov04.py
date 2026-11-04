"""Compile changed camera and Session implementations for all shared title variants."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();H=a.candidate.resolve(strict=True);O=H/'perspective-syntax';O.mkdir();B=json.loads((H/'build/ordinary/observer-build.json').read_bytes());S=Path(B['sourceSnapshotRoot'])
compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert SHA(compiler.read_bytes())==B['compilerSha256'];rows=[]
for title in [12,13,14,16]:
 for name in ['SceneCamera.cpp','GameSession.cpp']:
  source=S/'th12_web/cpp/game'/name;flags=[x for x in B['flags']if not x.startswith('-DPORT_TITLE=')];argv=[str(compiler),*flags,'-DPORT_TITLE='+str(title),'-fsyntax-only',str(source)]
  r=subprocess.run(argv,cwd=R,capture_output=True,timeout=90,env={**os.environ,'TEMP':str(O),'TMP':str(O)});(O/f'th{title}-{name}.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace')[-1500:]
  rows.append(dict(title=title,source=name,sourceSha256=SHA(source.read_bytes()),exitCode=0,argv=argv))
(O/'report.json').write_bytes((json.dumps(dict(passed=True,cases=rows,toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False),indent=2)+'\n').encode());print('PASS eight shared-title camera/Session syntax cases')
