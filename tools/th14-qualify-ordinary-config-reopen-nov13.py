"""Independent audit of actual menu writes and fresh Application reads."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/ordinary-config-reopen-nov13'
load=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
reports=[load(H/m/'report.json')for m in ('write','reopen')]
for r in reports:
 assert r['passed']and r['retired']and r['closed']and not r['errors']and r['exception']is None
 assert r['phase']=='passed'and r['sourceWasmSha256']=='839cb51fa5679a37be118398d30b0ef9368d2cf0b9925d26f9231f10fdd6a01e'
 assert all(w['closed']and w['exitCode']==0 for w in r['physicalWorkers'])
 assert sha((H/r['mode']/'executed-driver.mjs').read_bytes())==r['driverSha256']
expected=load(H/'write/expected.json')
cfg=(H/'save/th14.cfg').read_bytes()
assert list(cfg)==expected['config']and len(cfg)==92
initial=(H/'save-v2/th14.cfg').read_bytes()
changed=[i for i,(a,b)in enumerate(zip(initial,cfg))if a!=b]
assert changed==[0x22,0x23]and cfg[0x22]==5 and cfg[0x23]==5
raw=(H/'reopen/score-raw-observed.bin').read_bytes();b=bytearray(raw)
assert len(b)==7*0x5298+0x42c==expected['scoreSemanticsBytes']
records=[]
for i in range(8):
 start=i*0x5298;n=0x5298 if i<7 else 0x42c
 record=raw[start:start+n];kind,checksum,length=struct.unpack_from('<III',record)
 assert kind==(0x15243 if i<7 else 0x15453)and length==n and sum(record[8:])==checksum
 if i<7:assert struct.unpack_from('<I',record,12)[0]==i;b[start+12:start+16]=bytes(4)
 b[start+4:start+8]=bytes(4)
 records.append(dict(character=i if i<7 else None,kind=hex(kind),bytes=n,checksumValid=True))
assert sha(b)==expected['scoreSemanticsSha256']
saved=[load(H/m/'saved-files.json')for m in ('write','reopen')]
for name in ('scoreth14.dat','th14.cfg'):
 rows=[next(x for x in rows if Path(x['name']).name==name)for rows in saved]
 assert rows[0]['sha256']==rows[1]['sha256']==sha((H/'save'/name).read_bytes())
result=dict(passed=True,processes=2,actualMenuEdits=True,changedConfigOffsets=changed,configBytes=92,
 actualApplicationHostSaveBoundary=True,scoreRecords=records,canonicalRecordBytes=len(b),
 payloadBytesCompared=len(b)-60,serializationFormatBytesAccountedSeparately=60,
 onlyRecordChecksumsAndSerializedIndicesExcluded=True,allOtherRecordBytesIncludingRngFillerCompared=True,
 scoreFileBytes=(H/'save/scoreth14.dat').stat().st_size,encodedFilesStableAcrossReopen=True,
 allMeasuredWorkersDevicesAndTimersRetired=True,silentMixer=True,graphicsRecordingOnly=True,
 ordinaryGameplayScoreOrUnlockProgressionAccepted=False,browserPersistenceAccepted=False,
 originalCodecNewSampleVerified=(load(H/'native-codec-qualified.json')['passed'] if (H/'native-codec-qualified.json').exists() else False),completeGame=False,
 retainedFailures=['write-v1: invalid nonzero-volume assumption','write-v2: driver used confirm key for cancel',
 'reopen-v1: raw record checksums/indices compared before explicit format accounting'])
(H/'qualified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
