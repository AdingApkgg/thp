"""Extend the frozen fixed-watch observer with bounded read-only snapshots."""
from pathlib import Path
import ast, hashlib, importlib.util, json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/shot-lifetime-native-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest()
parent=R/'artifacts/th14/supervisor-pass-rng-nov05/observer-fixed-target/observer.py'
prepared=json.loads((parent.parent/'prepared.json').read_bytes())
original=parent.read_bytes();assert SHA(original)==prepared['observerSha256']
source=original.decode()


def replace(before,after):
    global source
    assert source.count(before)==1,(before,source.count(before))
    source=source.replace(before,after)


replace('combat_snapshots=[]', '''combat_snapshots=[]
lifetime_module=root/'tools/th14-shot-lifetime-readonly-nov05.py'
lifetime_spec=importlib.util.spec_from_file_location('lifetime',lifetime_module)
lifetime=importlib.util.module_from_spec(lifetime_spec);lifetime_spec.loader.exec_module(lifetime)
lifetime_snapshots=[];context_noop_skips=[]
(home/'shot-lifetime-plan.json').write_text(json.dumps(dict(windows=lifetime.WINDOWS,
    extraCallbacks=[1,1000],readOnly=True,predeclaredBeforeLaunch=True))+'\\n')''')
replace("    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)",
    "    original_context=bytes(b)\n    for index,address in enumerate(addresses):struct.pack_into('<I',b,4+4*index,address)")
replace('    if not k.Wow64SetThreadContext(threads[tid],b):', '''    if not current and bytes(b)==original_context:
        assert len(context_noop_skips)<4096
        context_noop_skips.append(dict(threadId=tid,precedingPlayerCallbacks=callback_count,
            hostMonotonicNs=observation_clock_ns(),entireContextUnchanged=True,contextApiNotCalled=True))
        return
    if not k.Wow64SetThreadContext(threads[tid],b):''')
replace('        raise C.WinError(context_error)', '''        (home/'hardware-context-write-failure.json').write_text(json.dumps(dict(
            threadId=tid,current=current,error=context_error,precedingPlayerCallbacks=callback_count,
            hostMonotonicNs=observation_clock_ns(),originalContextHex=original_context.hex(),
            desiredContextHex=bytes(b).hex(),errorNotIgnored=True))+'\\n')
        raise C.WinError(context_error)''')
replace('                            if combat_pool.due(callback_count,words[0]):', '''                            if lifetime.due(callback_count,words[30],words[0]):
                                lifetime_snapshots.append(lifetime.capture(read,callback_count,words,home/'shot-lifetime'))
                                (home/'shot-lifetime-index.json').write_text(json.dumps(dict(readOnly=True,
                                    snapshots=lifetime_snapshots,moduleSha256=sha(lifetime_module.read_bytes())),indent=2)+'\\n')
                            if combat_pool.due(callback_count,words[0]):''')
anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
replace(anchor,"    report.update(shotLifetimeSnapshots=len(lifetime_snapshots),shotLifetimeModuleSha256=sha(lifetime_module.read_bytes()),shotLifetimeReadOnly=True,unchangedCrossThreadContextsNotRewritten=context_noop_skips)\n"+anchor)
critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext','TerminateProcess'}
calls=lambda s:sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(s))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
assert calls(source)==calls(original.decode())
out=H/'observer-slots-v2';assert not out.exists();out.mkdir(parents=True)
(out/'observer.py').write_text(source,encoding='utf8',newline='\n')
(out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
module=R/'tools/th14-shot-lifetime-readonly-nov05.py'
ast.parse(module.read_bytes())
result=dict(prepared=True,parentObserverSha256=SHA(original),observerSha256=SHA((out/'observer.py').read_bytes()),
    moduleSha256=SHA(module.read_bytes()),criticalMutationCallAstUnchanged=True,
    additionalGameMemoryWrites=0,additionalSuspendsOrResumes=0,hardwareWatchProfileUnchanged=True,
    boundedWindowsPredeclared=True,redundantUnchangedNoncurrentContextWritesSkipped=True,
    otherContextErrorsStillFatal=True,originalProcessNotYetRun=True,completeGame=False,
    toolSha256=SHA(Path(__file__).read_bytes()))
(out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
