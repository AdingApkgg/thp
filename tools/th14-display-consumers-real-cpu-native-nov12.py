"""Recheck original deformation with the real Windows x86 D3DX normalize service."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12';O=H/'real-cpu-native';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=R/'tools/th14-display-consumers-native-nov12.py';text=parent.read_text(encoding='utf8')
# Keep the original 41f360/424100 execution and inputs. The already accepted
# fade recorder is independent and is not executed again by this check.
a=text.index('# Retain and bind');b=text.index("image=importlib.import_module",a)
text=text[:a]+text[b:]
text=text.replace("H=R/'artifacts/th14/display-consumers-nov12';sha=","H=R/'artifacts/th14/display-consumers-nov12/real-cpu-native';sha=")
text=text.replace("fadeParentSha256=sha(parent.read_bytes()),fadeDerivedSha256=sha(derived.read_bytes()),",'')
assert text.count('put(0x4b12b8,normalize)')==1
service='''put(0x4b12b8,normalize)
normalize_calls=[]
def real_normalize(uc,address,size,user):
    sp=uc.reg_read(UC_X86_REG_ESP);ret,out,source=words(sp,3);values=words(source,3)
    worker.stdin.write(','.join(map(str,values))+'\\n');worker.stdin.flush()
    line=worker.stdout.readline();assert line,'real x86 D3DX worker stopped'
    result=[int(x) for x in line.strip().split(',')];assert len(result)==3
    m.mem_write(out,struct.pack('<3I',*result));normalize_calls.append(dict(input=values,output=result))
    uc.reg_write(UC_X86_REG_EAX,out);uc.reg_write(UC_X86_REG_ESP,sp+12);uc.reg_write(UC_X86_REG_EIP,ret)
m.hook_add(UC_HOOK_CODE,real_normalize,begin=normalize,end=normalize)'''
text=text.replace('put(0x4b12b8,normalize)',service)
worker_source=R/'tools/th14-d3dx-normalize-worker-nov12.cs';worker_exe=O/'normalize-worker.exe'
compiler=Path('C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe')
with (O/'worker-build.log').open('wb') as log:
    subprocess.run([str(compiler),'/nologo','/platform:x86','/optimize+','/out:'+str(worker_exe),str(worker_source)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
derived=O/'derived-native.py';derived.write_text(text,encoding='utf8',newline='')
worker=subprocess.Popen([str(worker_exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
    ns={'__file__':str(parent),'__name__':'real_cpu_native','worker':worker};exec(compile(text,str(derived),'exec'),ns)
finally:
    worker.stdin.close();code=worker.wait(timeout=10);error=worker.stderr.read();assert code==0,error
report_path=O/'deformation-native.json';report=json.loads(report_path.read_bytes())
report.update(realD3dxNormalizeExecuted=False,realD3dxNormalizeExecutedOnCpu=True,normalizationService='actual Windows x86 D3DXVec3Normalize',
    normalizationCalls=len(ns['normalize_calls']),normalizationWorkerExited=True,normalizationWorkerExitCode=code,
    normalizationWorkerSourceSha256=sha(worker_source),normalizationWorkerExeSha256=sha(worker_exe),
    normalizationWorkerCompilerSha256=sha(compiler),normalizationWorkerSource=worker_source.relative_to(R).as_posix(),
    parentToolSha256=sha(parent),derivedToolSha256=sha(derived),toolSha256=sha(Path(__file__)),
    originalDeformationInstructionsUnmodified=True,originalGameInheritedFloatingPointEnvironmentMeasured=False,
    noNormalizationReferenceSuppliedToCpp=True)
report_path.write_text(json.dumps(report,separators=(',',':'))+'\n')
(O/'normalization-calls.json').write_text(json.dumps(ns['normalize_calls'],separators=(',',':'))+'\n')
print(json.dumps(dict(normalizationCalls=report['normalizationCalls'],normalizationWorkerExitCode=code,originalDeformationInstructionsUnmodified=True)))
