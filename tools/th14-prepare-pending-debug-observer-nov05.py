"""Preserve another thread's pending hardware debug event before reprogramming.

No exception is swallowed. Only a cross-thread context update is deferred when
its own DR6 already reports hardware hits; normal handling of that event installs
the current requested registers. No code/game-memory or suspend writes added.
"""
from pathlib import Path
import argparse, ast, hashlib, json

R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/script-rng-read-generation-nov05'
SHA=lambda b:hashlib.sha256(b).hexdigest()

def prepare(out):
    parent=H/'observer-original-context/observer.py';raw=parent.read_bytes()
    assert SHA(raw)=='1ce20ce869bbdc59f4ff3bc9522cb8c33f02304a0099153da7b2f155f51add6d'
    bad=json.loads((H/'pending-status-negative-retry1/report.json').read_bytes())
    good=json.loads((H/'pending-status-positive-retry1/report.json').read_bytes())
    for proof in [bad,good]:
        assert not proof['error']and proof['toolSha256']==SHA((R/'tools/th14-pending-debug-status-component-nov05.py').read_bytes())
    assert bad['pendingOtherHardwareStatuses']>0 and bad['unknownOrLostStatusEvents']>0 and bad['exitCode']==0x4000001e
    assert good['all256MarkerEventsAccepted']and good['deferredUpdates']>0 and not good['unknownOrLostStatusEvents']and good['exitCode']==0
    source=raw.decode()
    def replace(a,b):
        nonlocal source
        assert source.count(a)==1,(a[:90],source.count(a));source=source.replace(a,b)
    replace('script_rng_access_rows=[];script_rng_post_restore_accesses=0;script_rng_arm=None',
        'script_rng_access_rows=[];script_rng_post_restore_accesses=0;script_rng_arm=None\npending_debug_context_deferrals=[]')
    anchor="    pending=pending_publications.get(tid)\n    trace_publications=first_snapshot is not None and callback_count<opt.publication_cutoff"
    replace(anchor,"""    # Another thread may already have executed its watched instruction while
    # the current thread's event was selected first. Clearing its DR6 or
    # replacing its watch addresses would destroy that queued event's identity.
    if not current and struct.unpack_from('<I',b,20)[0]&15:
        assert len(pending_debug_context_deferrals)<4096
        row=dict(event='defer-cross-thread-debug-context-update',threadId=tid,
            pc=struct.unpack_from('<I',b,184)[0],debugStatus=struct.unpack_from('<I',b,20)[0],
            debugAddresses=list(struct.unpack_from('<4I',b,4)),debugControl=struct.unpack_from('<I',b,24)[0],
            hostMonotonicNs=observation_clock_ns(),precedingPlayerCallbacks=callback_count,
            deferredUntilOwnDebugEvent=True,contextWritten=False,exceptionIgnored=False,
            noAdditionalSuspendOrResume=True,readOnly=True,providedToEngine=False)
        pending_debug_context_deferrals.append(row)
        with(home/'pending-debug-context-deferrals.jsonl').open('a',encoding='utf8')as stream:stream.write(event_json(row)+'\\n')
        return
"""+anchor)
    anchor="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
    replace(anchor,"    report.update(pendingDebugContextDeferrals=len(pending_debug_context_deferrals),pendingDebugContextDeferralsSha256=sha((home/'pending-debug-context-deferrals.jsonl').read_bytes())if pending_debug_context_deferrals else None,pendingCrossThreadHardwareStatePreserved=True,unrecognizedExceptionPolicyUnchanged=True,ordinaryIndependentTimingAccepted=False)\n"+anchor)
    critical={'WriteProcessMemory','SuspendThread','ResumeThread','ContinueDebugEvent','CreateProcessW','Wow64SetThreadContext'}
    def calls(text):return sorted(ast.dump(n,include_attributes=False)for n in ast.walk(ast.parse(text))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in critical)
    assert calls(raw.decode())==calls(source);ast.parse(source)
    assert not out.exists();out.mkdir(parents=True);(out/'observer.py').write_text(source,encoding='utf8',newline='\n');(out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes())
    value=dict(prepared=True,observerSha256=SHA((out/'observer.py').read_bytes()),parentObserverSha256=SHA(raw),
        preservesOtherThreadPendingHardwareStatuses=True,criticalMutationCallAstUnchanged=True,
        negativeOwnFixtureExit=bad['exitCode'],negativeLostStatuses=bad['unknownOrLostStatusEvents'],
        positiveOwnFixtureEvents=256,positiveDeferredUpdates=good['deferredUpdates'],
        originalProcessNotYetRun=True,originalStartupFailureCauseProven=False,
        originalUnrecognizedExceptionPolicyUnchanged=True,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes()))
    (out/'prepared.json').write_text(json.dumps(value,indent=2)+'\n');return value

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')
    value=prepare(out);print(json.dumps({k:value[k]for k in ['prepared','observerSha256','criticalMutationCallAstUnchanged','positiveOwnFixtureEvents']}))
