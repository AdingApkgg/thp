"""Summarize observed first-chance exception provenance without waiving any gate."""
from pathlib import Path,PureWindowsPath
import argparse,hashlib,json

R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();N=a.native.resolve();out=a.output.resolve();assert N.is_relative_to(R/'artifacts/th14') and (out.is_relative_to(R/'artifacts/th14') or out.is_relative_to(R/'docs/porting')) and not out.exists()
sha=lambda b:hashlib.sha256(b).hexdigest();report_raw=(N/'report.json').read_bytes();report=json.loads(report_raw);assert report['childExited'] and not report['error'] and isinstance(report['debugErrors'],list)
observer=(N/'observer-source.py').read_bytes();assert sha(observer)==report['sourceSha256']==sha((R/'tools/th14-native-terminal-exception-observer-nov03.py').read_bytes())
path=N/'replay-exception-details.jsonl';raw=path.read_bytes() if path.exists() else b'';details=[json.loads(line) for line in raw.splitlines() if line];assert len(details)<=64
unmatched=list(report['debugErrors']);rows=[]
for event in details:
 keys=['code','address','firstChance','callbacks','hostMonotonicNs'];matches=[i for i,row in enumerate(unmatched) if all(row.get(k)==event.get(k) for k in keys)];assert len(matches)==1;unmatched.pop(matches[0])
 assert event['readOnly'] and not event['providedToEngine'] and event['debuggerPausesAffectTiming'];typ=event.get('msvc32Type',{})
 if typ:assert typ['readOnly'] and not typ['providedToEngine']
 module=event.get('mappedMetadataModulePath');name=PureWindowsPath(module).name if module else None;rows.append(dict(code=hex(event['code']),firstChance=bool(event['firstChance']),callbacks=event['callbacks'],mappedModuleBasename=name,mappedAddressKind='typeDescriptor' if typ.get('typeDescriptor') else 'exceptionAddress',decodedMsvcType=typ.get('typeName'),metadataDecodeSucceeded=bool(typ.get('typeName')),continuedOriginalCallbacksObserved=report['callbacks']>event['callbacks']))
result=dict(verifiedRetainedEventBindings=True,originalCallbackCount=report['callbacks'],reportedDebugExceptions=len(report['debugErrors']),detailedEvents=len(rows),unmatchedDebugExceptions=len(unmatched),detailCaptureLimitedToFirst64=True,events=rows,exceptionFree=len(report['debugErrors'])==0,exceptionGateWaived=False,gameStateUnaffectedNotProved=True,sourceReplayEofProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha(report_raw),eventLogSha256=sha(raw) if raw else None,observerSha256=sha(observer),verifierSha256=sha(Path(__file__).read_bytes()),scope='The reported MSVC type metadata and mapped module are observations, not proof of the original exception cause, handler, or gameplay equivalence. A first-chance event alone does not prove a crash. No raw pointers or stack bytes are included.')
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
