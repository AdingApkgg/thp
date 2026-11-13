"""Compare source-generated host code with the actual browser-tested shell."""
from pathlib import Path
import importlib.util,json,re,hashlib,difflib
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/source-delivery-nov13'
spec=importlib.util.spec_from_file_location('th14build',R/'tools/th14-build-gles.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=R/'artifacts/th14/native-viewer-application-nov13/browser-v2'
identity=dict(version='source-host-check',completeGame=False,nativeEquivalent=False,sha256=json.loads((B/'build.json').read_bytes())['sha256'])
s=m.prepare_host_shell((R/'runtimes/th12/th12_web/sdl-runtime/shell.mjs').read_text(encoding='utf8'),identity)
(H/'source-shell.mjs').write_text(s,encoding='utf8',newline='\n')
def normalize(s):
 s=re.sub(r'const runtimeBuild=/\*TH14_BUILD_INFO\*/[^\n]+;', 'const runtimeBuild=IDENTITY;',s)
 return [line.strip()for line in s.splitlines()if line.strip()and not line.lstrip().startswith('//')]
a=normalize(s);b=normalize((B/'shell.mjs').read_text(encoding='utf8'))
assert a==b,'\n'.join(difflib.unified_diff(a,b))
profile=json.loads((R/'tools/th14-gles-profile.json').read_bytes())
exports=next(f for f in profile['linkFlags']if f.startswith('-sEXPORTED_FUNCTIONS=')).split('=')[1].split(',')
required=['th14_replay_description','th14_replay_open_ready','th14_open_replay','th14_replay_status','th14_replay_seek_step','th14_replay_rate','th14_replay_close']
assert all('_'+n in exports for n in required)
j=dict(sourceGeneratedShellExecutableLinesMatchBrowserTestedShell=True,versionIdentityExcluded=True,
 commentsAndBlankLinesExcluded=True,explicitViewerExports=required,sourceSha256=hashlib.sha256(s.encode()).hexdigest(),wholeGameAccepted=False)
(H/'source-shell-qualified.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j))
