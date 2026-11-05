"""Prepare a bounded original replay observer for the intact browser slot02.

Only filesystem staging and read-only terminal sampling change. The original
instruction watches, warm-case write and exception handling remain in place.
"""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/browser-recording-native-nov05'
parent=R/'artifacts/th14/shot-lifetime-native-nov05/observer-slots-v2/observer.py'
raw=parent.read_bytes();SHA=lambda b:hashlib.sha256(b).hexdigest()
assert SHA(raw)=='27bfd47328d76359b6ff3bfae5791960dfa987e3f41b420ffa55fba9c8b428c7'
assets=R/'artifacts/th14/native-campaign-assets/57d84a5cbe82-ec04b9bea043'
manifest=json.loads((assets/'manifest.json').read_bytes())
assert manifest['passed']and manifest['replaySha256']=='ec04b9bea043c092e4f7b2fd18f379cb38419c5597ed7d640193fbefc344434a'
s=raw.decode()


def replace(before,after):
    global s
    assert s.count(before)==1,(before[:90],s.count(before));s=s.replace(before,after)


replace('    target=work/name;digest=storage.clone_immutable(source,target)', '''    target=work/name
    if name=='th14.dat':
        assert source.resolve()==asset/'th14.dat' and not target.exists()
        assert source.resolve().is_relative_to(root/'artifacts/th14/native-campaign-assets')
        assert not source.is_symlink() and not(source.stat().st_mode&0o222)
        digest=storage.sha256_file(source);assert digest==asset_report['referenceArchiveSha256']
        os.link(source,target);assert os.path.samefile(source,target)
    else:digest=storage.clone_immutable(source,target)''')
replace("    return dict(hostMonotonicNs=observation_clock_ns(),stage=u32(0x4f58a4),pauseWords=list(words),disabledEntries=disabled,",
        "    sample=dict(hostMonotonicNs=observation_clock_ns(),stage=u32(0x4f58a4),pauseWords=list(words),disabledEntries=disabled,")
end="        lifeState=u32(u32(0x4db67c)+0x684),callbacks=callback_count,hudPointer=u32(0x4db550),hudDisplayedScoreUnits=u32(u32(0x4db550)+0x140))"
replace(end,end+'''
    sample['economyWords']=list(struct.unpack('<28I',read(0x4f5828,28*4)))
    sample['replayCursorWords']=list(struct.unpack('<14I',snapshot(read)))
    return sample

terminal_probe_rows=[]
def retain_terminal_probe(reason):
    global last_terminal_check,complete
    if callback_count<=1000 or time.monotonic()-last_player_time<=3 or time.monotonic()-last_terminal_check<=.25:return
    last_terminal_check=time.monotonic();sample=terminal_menu_sample()
    if sample is None:return
    sample['probeReason']=reason;terminal_menu_samples.append(sample)
    terminal_probe_rows.append(dict(callbacks=callback_count,stage=sample['stage'],controlFrame=sample['controlFrame'],reason=reason))
    if len(terminal_menu_samples)>=3 and len({r['callbacks']for r in terminal_menu_samples[-3:]})==1:complete=True
''')
old='''                if callback_count>1000 and time.monotonic()-last_player_time>3 and time.monotonic()-last_terminal_check>.25:
                    last_terminal_check=time.monotonic();sample=terminal_menu_sample()
                    if sample:
                        terminal_menu_samples.append(sample)
                        if len(terminal_menu_samples)>=3 and len({r['callbacks']for r in terminal_menu_samples[-3:]})==1:complete=True'''
replace(old,"                retain_terminal_probe('debug-event-timeout')")
replace('''        finally:
            debug_event_clock_active=False''','''        finally:
            # Fixed Supervisor/pump watches continue after Player stops. Read
            # the same full native menu predicate while the process is paused.
            import sys
            if not exited and not debug_errors and sys.exc_info()[0]is None:retain_terminal_probe('paused-debug-event')
            debug_event_clock_active=False''')
anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
replace(anchor,"    report.update(browserAuthoredIntactReplay=True,generatedArchiveAliasReused=True,terminalProbeRows=terminal_probe_rows,terminalPausePredicateUnchanged=True)\n"+anchor)
critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext','TerminateProcess'}
calls=lambda text:sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
assert calls(raw.decode())==calls(s)
out=H/'observer';assert not out.exists();out.mkdir()
(out/'observer.py').write_text(s,encoding='utf8',newline='\n');(out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
report=dict(prepared=True,parentObserverSha256=SHA(raw),observerSha256=SHA((out/'observer.py').read_bytes()),
 criticalMutationCallAstUnchanged=True,additionalGameMemoryWrites=0,additionalSuspendsOrResumes=0,
 terminalPausePredicateUnchanged=True,readOnlyTerminalProbeAtPausedEventsAdded=True,
 filesystemGeneratedArchiveAliasOnly=True,originalGameFilesStillNeverHardlinked=True,
 assetManifestSha256=SHA((assets/'manifest.json').read_bytes()),replaySha256=manifest['replaySha256'],
 originalProcessNotYetRun=True,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
(out/'prepared.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
