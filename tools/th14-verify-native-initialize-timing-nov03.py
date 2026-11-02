"""Validate reported Initialize host-time inputs against original event bytes."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();native=a.native.resolve();model=a.model.resolve();output=a.output.resolve();assert native.is_relative_to(R/'artifacts/th14') and model.is_relative_to(R/'artifacts/th14') and output.is_relative_to(R/'artifacts/th14')
report_raw=(native/'report.json').read_bytes();report=json.loads(report_raw);model_raw=(model/'report.json').read_bytes();m=json.loads(model_raw);assert m['schedulerPhases']=='observed' and m['completed'] and not m['completeGame'] and not m['nativeEquivalent']
eventfile=native/'transition-events.jsonl';events=[json.loads(line) for line in eventfile.read_bytes().splitlines()] if eventfile.exists() else []
assert events==report['transitionEvents'] and report['hardwareBreakpointsOnly'] and not report['rngOrCounterWrites'] and not report['instructionBytesPatched']
entries=[x for x in m['observedPhaseInputs'] if x['phase']=='Initialize'];assert len({x['stage'] for x in entries})==len(entries)
for x in entries:
 candidates=[e for e in events if e['event']=='replay-seeds-restored-before-globals-copy' and e['stage']==x['stage']]
 assert len(candidates)==1;event=candidates[0];assert event['pc']==0x456133 and event['originalInstructionBytes'].startswith('f3a5')
 assert x['readyNs']==event['hostMonotonicNs'] and x['completionSource']=='original456133AfterSeedsRestoredBeforeGlobalsCopy',f"unverified Initialize timestamp for stage {x['stage']}"
 assert x['globalCopyAlreadyCompletedNotAsserted']
result={'passed':True,'scope':'Only binds each reported Initialize scheduler timestamp to the retained original event; other scheduler phases and gameplay require their own checks.','initializeInputs':len(entries),'nativeReportSha256':sha(report_raw),'nativeEventsSha256':sha(eventfile.read_bytes()) if eventfile.exists() else None,'modelReportSha256':sha(model_raw),'completeGame':False,'nativeEquivalent':False,'verifierSha256':sha(Path(__file__).read_bytes())};output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
