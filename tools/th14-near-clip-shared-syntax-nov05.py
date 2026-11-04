"""Compile the changed shared renderer for other titles and the WebGPU switch."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/gles-clip-portable-nov04';B=H/'production-build-nov05';D=H/'production-shared-syntax-nov05';assert not D.exists();D.mkdir()
sha=lambda raw:hashlib.sha256(raw).hexdigest();build=json.loads((B/'build.json').read_bytes());compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';rows=[]
for title,webgpu in [(12,False),(13,False),(14,False),(16,False),(14,True)]:
    flags=[('-DPORT_TITLE='+str(title))if v=='-DPORT_TITLE=14'else v for v in build['flags']if not v.startswith('-Wl,') and v!='-mexec-model=reactor']
    if webgpu:flags.append('-DTH14_WEBGPU_BACKEND=1')
    command=[str(compiler),*flags,'-fsyntax-only',str(B/'src/Renderer.cpp')];label=str(title)+('-webgpu'if webgpu else '')
    (D/(label+'-argv.json')).write_text(json.dumps(command,indent=2)+'\n');p=subprocess.run(command,cwd=R,capture_output=True,env={**os.environ,'TMP':str(D),'TEMP':str(D),'TMPDIR':str(D)},timeout=90)
    (D/(label+'.log')).write_bytes(p.stdout+p.stderr);rows.append(dict(title=title,webgpu=webgpu,returncode=p.returncode));assert p.returncode==0,p.stderr.decode(errors='replace')
result=dict(rows=rows,sourceBindings=build['sourceBindings'],buildSha256=sha((B/'build.json').read_bytes()),compilerSha256=sha(compiler.read_bytes()),syntaxOnly=True,otherTitleRuntimeAccepted=False)
(D/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows))
