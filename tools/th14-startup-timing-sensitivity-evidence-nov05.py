"""Recompute finite input sensitivities without publishing seeds, cookies or raw states."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/original-pair-audit-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest();bindings={}

def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data

def read(path):return json.loads(raw(path))

pair=read(H/'report.json');assert pair['uniqueStageFramePairs']==34429
assert pair['fieldDifferenceCounts']=={'21':34428,'22':34429,'26':9}
assert pair['allOtherSelectedFieldsEqual']and pair['gameplayRngSeedAndCallsEqualAtEveryUniquePair']
assert not pair['initialTimeInputsEqual']and not pair['initialSecurityCookiesEqual']
assert pair['observerProfilesDiffer']and not pair['ordinaryGuiNondeterminismProven']
for name,row in pair['evidenceBindings'].items():assert SHA(raw(R/name))==row['sha256']
base=R/'artifacts/th14/supervisor-pass-rng-nov05/comparison-pump-enabled/model/selected-state.u32'
baseline=raw(base);assert len(baseline)==35000*128 and SHA(baseline)=='851f64d43758ed80962e6ea7d8f58270482c24f5be0a3696414651d8cb2ab8a7'
parent=R/'artifacts/th14/supervisor-pass-rng-nov05/comparison-driver-v6/driver.mjs'
assert SHA(raw(parent))=='d9247f1c8889063065dfd3c8a895b9ea2e504f29902fe58f364e23e5970ce67c'
def unique_shots(data):
    groups={}
    for row in struct.iter_unpack('<32I',data):groups.setdefault((row[30],row[0]),[]).append(row[26])
    return {key:values[0]for key,values in groups.items()if len(values)==1}
original_a=unique_shots(raw(R/'artifacts/th14/script-rng-read-generation-nov05/prefix-player-pump/native/selected-state.u32'))
baseline_shots=unique_shots(baseline)
pair_keys=sorted(original_a.keys()&baseline_shots.keys());assert len(pair_keys)==34429
baseline_differences={key for key in pair_keys if original_a[key]!=baseline_shots[key]};assert len(baseline_differences)==9
old_failure=read(H/'controls/baseline/result.json');assert old_failure['exitCode']==1
assert b"Identifier 'raw' has already been declared"in raw(H/'controls/baseline/run.log')
groups=[]
for folder,cases in [('controls-retry1',['baseline','time-only','cookie-only','both']),
    ('initialize-controls',['baseline','stage2-late','stage3-late','stage2-player-late','stage3-player-late'])]:
    rows=[];hashes=set()
    for case in cases:
        home=H/folder/case;result=read(home/'result.json');assert result['exitCode']==0 and result['callbacks']==35000
        assert result['diagnosticOnly']and not result['ordinaryIndependentTimingAccepted']and not result['productionOrFixtureRecompiled']
        data=raw(home/'model/diagnostic-state.u32');assert len(data)==len(baseline)and SHA(data)==result['selectedSha256']
        counts={};first={}
        for index,(a,b)in enumerate(zip(struct.iter_unpack('<32I',baseline),struct.iter_unpack('<32I',data))):
            for field,(x,y)in enumerate(zip(a,b)):
                if x!=y:
                    counts[str(field)]=counts.get(str(field),0)+1
                    first.setdefault(str(field),dict(callback=index+1,stage=b[30],stageFrame=b[0]))
        assert counts==result['differencesFromSameClockBaseline']and first==result['firstDifferences']
        source=raw(home/'driver.mjs');assert SHA(source)==result['diagnosticDriverSha256'];hashes.add(SHA(source))
        assert b'c.cold_begin(startupInputs.timeGetTime)'in source
        assert b'c.reference_environment(startupInputs.cookie,0x1aec84)'in source
        assert b'c.observed_first_script_read_window('not in source
        inputs=read(home/'startup-inputs.json');assert sorted(inputs)==['cookie','timeGetTime']
        if case=='baseline':assert data==baseline
        row=dict(case=case,callbacks=35000,selectedSha256=SHA(data),differences=counts,firstDifferences=first,
            byteIdenticalToBaseline=data==baseline)
        shots=unique_shots(data);assert all(key in shots for key in pair_keys)
        differing={key for key in pair_keys if original_a[key]!=shots[key]}
        row['alignedShotCountersAgainstOtherOriginal']=dict(pairs=len(pair_keys),differenceCount=len(differing),
            correctedPriorDifferenceFrames=[dict(stage=key[0],stageFrame=key[1])for key in sorted(baseline_differences-differing)],
            introducedDifferenceFrames=[dict(stage=key[0],stageFrame=key[1])for key in sorted(differing-baseline_differences)])
        if folder=='controls-retry1':
            row.update(timeInputChanged=result['timeInputDiffersFromBaseline'],cookieInputChanged=result['cookieInputDiffersFromBaseline'])
        else:
            assert raw(home/'startup-inputs.json')==raw(H/'controls-retry1/baseline/startup-inputs.json')
            deltas=read(home/'initialize-deltas.json');assert all(int(key)in [2,3]and value>0 for key,value in deltas.items())
            assert all(item['stillBeforeAllLaterPhaseReadiness']for item in result['controlledInitializeReadiness'])
            row['controlledReadiness']=result['controlledInitializeReadiness']
        rows.append(row)
    assert len(hashes)==1
    groups.append(dict(kind=folder,sameGeneratedDriverHashWithinGroup=True,driverSha256=hashes.pop(),cases=rows))
startup=groups[0]['cases'];assert startup[1]['differences']==startup[3]['differences']=={'21':14130,'22':216}
assert startup[2]['byteIdenticalToBaseline']and all('26'not in row['differences']for row in startup)
for name in ['th14-retained-original-pair-audit-nov05','th14-startup-input-controls-nov05','th14-initialize-timing-controls-nov05']:raw(R/'tools'/(name+'.py'))
out=dict(schema='th14/startup-timing-sensitivity-public-evidence/1',verifiedFiniteInputSensitivityControls=True,
    originalPair=dict(uniqueStageFramePairs=34429,duplicateKeyRowsExcluded=pair['duplicateKeyRowsExcluded'],
        differences=pair['fieldDifferenceCounts'],activeShotDifferences=pair['activeShotDifferences'],
        timeAndCookieBothDiffer=True,observerProfilesDiffer=True,ordinaryGuiNondeterminismProven=False),
    controls=groups,sourceReplaySha256=pair['sourceReplaySha256'],
    allSelectedWordsPerControl=1120000,baselineCollectorByteIdenticalToPreviouslyAcceptedTrajectory=True,
    onlyDeclaredExternalInputsVaried=True,generatedDiagnosticDriversAreNotAcceptanceDrivers=True,
    originalStrictDriverAndGatesChanged=False,productionSourcesChanged=False,
    originalPairActiveShotDifferencesFullyExplained=False,oldDefaultFailureClosed=False,
    ordinaryIndependentTimingAccepted=False,wholePixelsOrPcmCompared=False,allModesAccepted=False,
    completeGame=False,nativeEquivalent=False,rawSeedsCookiesStatesOrBinariesUploaded=False,
    retainedInitialCollectorSyntaxFailure=True,evidenceBindings=bindings,toolSha256=SHA(Path(__file__).read_bytes()))
(R/'docs/porting/th14-startup-timing-sensitivity-nov05.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(verifiedFiniteInputSensitivityControls=True,originalPairs=34429,controls=sum(len(x['cases'])for x in groups),callbacksPerControl=35000,productionChanged=False,completeGame=False)))
