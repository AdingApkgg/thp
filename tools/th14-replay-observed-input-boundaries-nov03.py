"""Bind optional observed original replay-input boundaries to the decoded source file."""
from pathlib import Path
import argparse,hashlib,json,struct
R=Path(__file__).resolve().parents[1];sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser(description=__doc__)
for x in ['native','metadata','decoded','replay','output']:p.add_argument('--'+x,type=Path,required=True)
a=p.parse_args();n=a.native.resolve();meta=a.metadata.resolve();decoded=a.decoded.resolve();replay=a.replay.resolve();out=a.output.resolve()
for path in [n,meta,decoded,replay,out]:assert path.is_relative_to(R/'artifacts/th14')
assert not out.exists();report_raw=(n/'report.json').read_bytes();report=json.loads(report_raw);m=json.loads(meta.read_bytes());data=decoded.read_bytes();source=replay.read_bytes();assert m['actualNativeCodecVerified'] and sha(data)==m['decodedSha256'] and sha(source)==m['sha256']==report['sourceFullReplaySha256']
codec_raw=(meta.parent/'native-codec-verified.json').read_bytes();codec=json.loads(codec_raw);assert codec['passed'];candidates=[x for x in codec['rows'] if x['sha256']==m['sha256']];assert len(candidates)==1 and candidates[0]['decodedSha256']==m['decodedSha256'] and candidates[0]['nativeCodecObserverSha256']==codec['toolSha256']
count,character,subtype,difficulty=struct.unpack_from('<4I',data,0x78);assert [character,subtype,difficulty]==m['expectedSelection'] and count==len(m['stages']);offset=0x94;stages={}
for entry in m['stages']:
 stage,seed=struct.unpack_from('<HH',data,offset);frames,payload=struct.unpack_from('<II',data,offset+4);assert stage==entry['stage'] and frames==entry['frames'] and payload==entry['payloadBytes'] and frames*6<=payload and stage not in stages
 start=offset+0xdc;assert start+payload<=len(data);stages[stage]=dict(start=start,frames=frames);offset=start+payload
assert offset==len(data)
assert report['childExited'] and not report['error'] and report['hardwareBreakpointsOnly'] and not report['instructionBytesPatched'] and not report['rngOrCounterWrites'] and not report['inputInjected'] and report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
observer=(n/'observer-source.py').read_bytes();assert sha(observer)==report['sourceSha256']
implemented=report.get('replayTerminalMarkerObservationImplemented') is True
if implemented:assert sha(observer) in {sha((R/'tools/th14-native-terminal-marker-observer-nov03.py').read_bytes()),sha((R/'tools/th14-native-terminal-exception-observer-nov03.py').read_bytes())}
markers=report.get('replayTerminalMarkerEvents',[]);exhaustions=report.get('replayStageInputExhaustionEvents',[]);assert implemented or not(markers or exhaustions)
if implemented:assert bool(markers)==(report.get('observedReplayTerminalMarker') is True)
assert len({e['stage'] for e in exhaustions})==len(exhaustions)
for filename,events in [('replay-terminal-marker-events.jsonl',markers),('replay-stage-input-exhaustion-events.jsonl',exhaustions)]:
 path=n/filename;lines=[json.loads(x) for x in path.read_bytes().splitlines()] if path.exists() else [];assert lines==events
results=[]
for e in markers:
 stage=e['recordedStage'];cursor=e['stageInputCursor'];item=stages[stage];assert e['stageIndex']==stage and e['pc']==0x45521b and e['readOnly'] and not e['nativeValuesProvidedToEngine'] and e['sixMarkerBytesVerified'] and 0<=cursor<item['frames'] and e['declaredStageFrameCount']==item['frames']
 start=item['start']+cursor*6;assert data[start:start+6]==b'\xff'*6 and e['markerAtLastRecordedInput']==(cursor+1==item['frames']);results.append(dict(kind='terminal-marker',recordedStage=stage,cursor=cursor,frameCount=item['frames'],lastRecordedInput=cursor+1==item['frames'],originalStage=e['stage']))
for e in exhaustions:
 stage=e['recordedStage'];cursor=e['stageInputCursor'];item=stages[stage];assert e['stageIndex']==stage and e['pc']==0x4552cd and e['readOnly'] and not e['nativeValuesProvidedToEngine'] and cursor>=item['frames'] and e['declaredStageFrameCount']==item['frames'] and e['exactFirstExhaustedCursor']==(cursor==item['frames'])
 results.append(dict(kind='stage-input-exhausted',recordedStage=stage,cursor=cursor,frameCount=item['frames'],exactBoundary=cursor==item['frames'],originalStage=e['stage']))
last=m['stages'][-1]['stage'];result=dict(verifiedReportAndSourceBindings=True,verifiedObservedInputBoundaries=bool(results),observationImplemented=implemented,observationWindowLimited=True,observedEvents=results,finalRecordedStage=last,finalStageInputAtOrBeyondDeclaredFramesObserved=any(x['kind']=='stage-input-exhausted' and x['recordedStage']==last for x in results),finalStageTerminalMarkerAtLastInputObserved=any(x['kind']=='terminal-marker' and x['recordedStage']==last and x['lastRecordedInput'] for x in results),absenceDoesNotProveNoEvent=True,debugExceptions=len(report['debugErrors']),exceptionsRequireSeparateEvaluation=bool(report['debugErrors']),sourceFileByteEofProved=False,gameClearProved=False,completeGame=False,nativeEquivalent=False,nativeReportSha256=sha(report_raw),codecEvidenceSha256=sha(codec_raw),sourceReplaySha256=sha(source),decodedSha256=sha(data),verifierSha256=sha(Path(__file__).read_bytes()))
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
