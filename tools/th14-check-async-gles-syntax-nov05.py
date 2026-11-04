"""Check the Application callback guards for shared titles and WebGPU."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
R=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
home=a.build.resolve();out=a.output.resolve();assert home.is_relative_to(R/'artifacts/th14')and out.is_relative_to(R/'artifacts/th14')and not out.exists();out.mkdir()
raw=(home/'build.json').read_bytes();build=json.loads(raw);source=home/'source';sdk=R/'runtimes/th12/tools/emsdk'
for name,row in build['sourceBindings'].items():assert SHA((source/name).read_bytes())==row['sha256'],name
rows=[]
for title,gpu in [(11,False),(12,False),(13,False),(16,False),(14,True)]:
    label=str(title)+('-webgpu'if gpu else '-gles');flags=[('-DPORT_TITLE='+str(title))if x=='-DPORT_TITLE=14'else x for x in build['flags']]
    if gpu:flags+=['-DTH14_WEBGPU_BACKEND=1','-DTH14_ARCHIVE_WORKER=1']
    argv=[sys.executable,str(sdk/'upstream/emscripten/emcc.py'),*flags,'-fsyntax-only',str(source/'th12_web/cpp/sdl/Application.cpp')]
    env={**os.environ,'EM_CONFIG':str(sdk/'.emscripten'),'EMSDK':str(sdk),'EMSDK_PYTHON':sys.executable,'TEMP':str(out),'TMP':str(out),'TMPDIR':str(out)}
    result=subprocess.run(argv,cwd=source/'th12_web',env=env,capture_output=True,timeout=90)
    (out/(label+'.log')).write_bytes(result.stdout+result.stderr);rows.append(dict(title=title,webgpu=gpu,returncode=result.returncode))
    assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
report=dict(passed=True,rows=rows,syntaxOnly=True,buildReportSha256=SHA(raw),applicationSha256=build['sourceBindings']['th12_web/cpp/sdl/Application.cpp']['sha256'],completeGame=False)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
