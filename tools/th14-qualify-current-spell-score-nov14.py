from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-concurrent-mixer-nov14';O=H/'spell-score-persistence'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=load(O/'inputs.json');reports={k:load(O/k/'report.json') for k in inputs};codecs={k:load(O/k/'native-codec-qualified.json') for k in inputs};buffers={k:(O/k/'native-decoded.bin').read_bytes() for k in inputs}
for key,spec in inputs.items():
 report=reports[key];codec=codecs[key];assert report['finished'] and report['retired'] and report['exception'] is None and not report['errors'] and report['noGameplayStarted']
 assert sha(Path(spec['path']))==spec['sha256']==report['sourceSha256']==codec['encodedSha256']
 assert codec['passed'] and codec['actualRetailDecryptAndLzss'] and codec['originalInstructionBytesPatched']==0
 assert codec['allDecodedBytesEqualToFreshApplicationLoadedRecords']
 assert (O/key/'native-decoded.bin').read_bytes()==(O/key/'score-observed.bin').read_bytes()
 assert len(buffers[key])==149076 and sha(O/key/'native-decoded.bin')==report['loadedSha256']==codec['decodedSha256']
before=buffers['before'];after=buffers['after'];size=0x5298;spell_offset=0x978;stride=0x9c
u32=lambda b,offset:struct.unpack_from('<I',b,offset)[0]
names=['ordinaryCaptures','practiceCaptures','ordinaryAttempts','practiceAttempts'];changed=[]
for selection in range(7):
 for spell in range(120):
  at=selection*size+spell_offset+spell*stride
  a=struct.unpack_from('<4I',before,at+0x80);b=struct.unpack_from('<4I',after,at+0x80)
  assert a[:3]==b[:3],(selection,spell,'existing captures or ordinary attempts changed')
  assert before[at+0x98:at+0x9c]==after[at+0x98:at+0x9c],(selection,spell,'spell high score')
  if a!=b:changed.append({'selection':selection,'spell':spell,'before':dict(zip(names,a)),'after':dict(zip(names,b))})
assert [(r['selection'],r['spell']) for r in changed]==[(1,3),(6,3)]
for row in changed:assert row['before']['practiceAttempts']==0 and row['after']['practiceAttempts']==2 and row['after']['practiceCaptures']==0
writer=load(H/'spell-practice-flow/natural-save-v2/report.json');assert writer['finished'] and writer['retired'] and writer['exception'] is None
final=next(c for c in writer['checkpoints'] if c['label']=='mode-flow-saved');playtime=final['behavior'][15]
play_count_delta=u32(after,size+0x7b8)-u32(before,size+0x7b8);playtime_delta=u32(after,size+0x7bc)-u32(before,size+0x7bc)
assert play_count_delta==3 and playtime_delta==playtime==711
for selection in range(6):assert before[selection*size+0x7c0:selection*size+0x7f0]==after[selection*size+0x7c0:selection*size+0x7f0]
allowed=set()
for selection in [1,6]:
 for start,length in [(4,4),(spell_offset+3*stride+0x8c,4)]:allowed.update(range(selection*size+start,selection*size+start+length))
allowed.update(range(size+0x7b8,size+0x7c0))
diff=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];assert len(diff)==8 and set(diff)<=allowed
unchanged_loadouts=[selection for selection in range(6) if before[selection*size:(selection+1)*size]==after[selection*size:(selection+1)*size]];assert unchanged_loadouts==[0,2,3,4,5]
q={'schema':'th14/current-spell-score-persistence/1','passed':True,'acceptanceStandard':'observable-behavior-alignment','writerReportSha256':sha(H/'spell-practice-flow/natural-save-v2/report.json'),'moduleSha256':reports['before']['moduleSha256'],'sourceFilesUnchanged':True,'freshReadersNeverStartedGameplay':True,'freshReadersRetired':True,'decodedBytesPerFile':149076,'changedSpellRecords':changed,'all840OrdinaryCapturesAndAttemptsPreserved':True,'all840PracticeCapturesPreserved':True,'all840SpellHighScoresPreserved':True,'unchangedSpellRecordCounters':838,'playCountDelta':play_count_delta,'playTimeDelta':playtime_delta,'actualWriterPlayerCallbacks':playtime,'allSixLoadoutClearAndPracticeUnlockFieldsPreserved':True,'otherFiveLoadoutsWholeRecordsUnchanged':unchanged_loadouts,'settingsWholeRecordUnchanged':before[7*size:]==after[7*size:],'decodedChangedBytes':len(diff),'everyChangedByteWithinDeclaredCountersAndChecksums':True,'changedBytes':[{'selection':i//size,'offsetWithinRecord':hex(i%size),'before':before[i],'after':after[i]} for i in diff],'nativeCodecs':codecs,'readers':reports,'silentMemoryAudio':True,'graphicsRecordingOnly':True,'originalWholeSpellFlowAccepted':False,'browserPersistenceAccepted':False,'productionChanged':False,'completeGame':False}
assert q['settingsWholeRecordUnchanged']
for p in [O/'qualified.json',R/'docs/porting/th14-current-spell-score-nov14.json']:p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'practiceAttemptsBefore':0,'practiceAttemptsAfter':2,'changedBytes':len(diff),'freshDecodedBytesPerFile':149076,'productionChanged':False,'completeGame':False}))
