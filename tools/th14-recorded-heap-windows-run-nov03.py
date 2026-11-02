"""Run synthetic-lifetime inputs on isolated x86 Windows process heaps."""
from pathlib import Path
import hashlib,json,shutil,struct,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/replay-candidates-second-nov03/recorded-heap-windows-msvc';H.mkdir(exist_ok=False);sha=lambda b:hashlib.sha256(b).hexdigest();proof=json.loads((R/'docs/porting/th14-combined-heap-trace-nov03.json').read_bytes());raw=(R/'artifacts/th14/replay-candidates-second-nov03/combined-heap-original/main/native/crt-heap-events.jsonl').read_bytes();assert sha(raw)==proof['eventLogSha256'] and proof['debugExceptions']==0 and not proof['originalFullHeapHistoryProved']
active={};actions=[];allocations=0;frees=0;nulls=0
for line in raw.splitlines():
 row=json.loads(line);addr=row['address']
 if row['event'] in ('crt-heap-allocation-return','zeroed-allocation-return'):
  assert addr and addr not in active and row['requestedBytes']>0;token=allocations;allocations+=1;active[addr]=token;flags=8 if row['event']=='zeroed-allocation-return' else 0;actions.append((1,token,row['requestedBytes'],flags))
 elif row['event']=='crt-free-entry':
  if not addr:nulls+=1;continue
  assert addr in active;actions.append((2,active.pop(addr),0,0));frees+=1
 else:raise AssertionError('unknown event')
assert allocations==838 and frees==273 and nulls==8 and len(active)==565
header='#define HEAP_ALLOCATION_COUNT '+str(allocations)+'\n#define HEAP_ACTION_COUNT '+str(len(actions))+'\nstatic const struct Action heap_actions[HEAP_ACTION_COUNT]={\n'+''.join('{%d,%d,%d,%d},\n'%x for x in actions)+'};\n';(H/'heap-actions.h').write_text(header,encoding='ascii')
source=R/'tools/th14-recorded-heap-windows-helper-nov03.c';sdk=Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x86');clang=sdk/'cl.exe';link=sdk/'link.exe';kernel=Path('C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0/um/x86/kernel32.lib');obj=H/'helper.obj';exe=H/'helper.exe';assert shutil.disk_usage(R).free>=100*1024**3
commands=[[str(clang),'/nologo','/c','/O2','/GS-','/Zl','/TC','/I'+str(H),'/Fo'+str(obj),str(source)],[str(link),'/machine:x86','/subsystem:console','/entry:mainCRTStartup','/nodefaultlib','/out:'+str(exe),str(obj),str(kernel)]]
with (H/'build.log').open('wb') as log:
 for cmd in commands:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120,check=True)
assert exe.stat().st_size<1024*1024;cases=[]
for i in range(6):
 assert shutil.disk_usage(R).free>=100*1024**3
 p=subprocess.run([str(exe)],cwd=R,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and not p.stderr and len(p.stdout)==8+4*allocations and struct.unpack_from('<2I',p.stdout)==(0x54485048,allocations);path=H/f'process-{i}.bin';path.write_bytes(p.stdout);cases.append(dict(index=i,exitCode=p.returncode,bytes=len(p.stdout),sha256=sha(p.stdout)))
result=dict(sourceSha256=sha(source.read_bytes()),compilerSha256=sha(clang.read_bytes()),linkerSha256=sha(link.read_bytes()),executableSha256=sha(exe.read_bytes()),syntheticActionHeaderSha256=sha((H/'heap-actions.h').read_bytes()),eventLogSha256=sha(raw),allocations=allocations,freeEntriesAssumedSuccessful=frees,nullFreeEntriesOmitted=nulls,processes=len(cases),cases=cases,architecture='x86',helperReceivesOriginalAddresses=False,debugDeliveryOrderAssumedForExperiment=True,originalGameLaunched=False,actualWindowsProcessHeap=True,rawPointersPrivate=True,completeGame=False,nativeEquivalent=False);(H/'process-end.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
