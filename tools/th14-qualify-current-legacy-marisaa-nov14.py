from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/current-concurrent-mixer-nov14';O=H/'legacy-marisaa-current'
load=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=H/'replay-settings-gate/legacy-marisaa-easy-current-v1';report=load(run/'report.json');description=load(run/'description.json')
reference_path=R/'artifacts/th14/behavior-application-nov13/marisaa-easy-existing-native-comparison.json';reference=load(reference_path)
source=load(O/'source-qualified.json');native=reference['nativeFinalPlayerRow'];out=report['outcome'];state=out['state'];economy=out['outcome'];viewer=out['viewer']
assert report['finished'] and report['retired'] and report['exception'] is None and not report['errors']
assert report['enabled']==0 and not any(report['opened'][:11])
assert report['wasmSha256']==source['moduleSha256'] and report['inputSha256']==source['inputSha256']==reference['inputSha256']
assert reference['nativeSelectedHashVerified'] and reference['nativeAlsoEndedEarly']
assert description['character']==1 and description['shot']==0 and description['difficulty']==0
fields={
 'scoreUnits':(native[12],economy[0]),'graze':(native[13],economy[7]),
 'power':(native[15],economy[6]),'livesUnsigned':(native[16],economy[2]),
 'lifeFragments':(native[17],economy[3]),'bombs':(native[18],economy[4]),
 'bombFragments':(native[19],economy[5]),'playerXBits':(native[3],state[6]),
 'playerYBits':(native[4],state[7]),'lifeState':(native[5],state[8]),
}
assert all(a==b for a,b in fields.values()),fields
assert viewer[0]==state[1]==3 and viewer[1]==state[5]==native[0]==13734 and viewer[3]==1
prior_frames=sum(s['frames'] for s in description['stages'] if s['id']<viewer[0]);cumulative=prior_frames+viewer[1]
assert cumulative==34783 and economy[0]*10==82434130
headers=(O/'public-headers.txt').read_text();assert '200 OK' in headers.splitlines()[0]
manifest=load(O/'production-runtime-manifest.json');generation=next(g['current']['generation'] for g in manifest['groups'] if g['root']=='runtime/th14/')
assert generation=='34f6e4b183b57e273555cae385ad12338484102a3a4517600662fb0784dc909c'
q={'schema':'th14/current-legacy-marisaa-replay/1','qualified':True,'acceptanceStandard':'observable-behavior-alignment','inputSha256':report['inputSha256'],'moduleSha256':report['wasmSha256'],'normalizedGameSessionMatchesProduction098f':source['productionGameSessionNormalizedSourceMatches'],'sharedBindingsMatch':source['sharedBindingsMatch'],'declaredSdkBrowserWrapperDifferences':source['sdkVsBrowserDeclaredWrapperDifferences'],'nativeReferenceSha256':sha(reference_path),'reportSha256':sha(run/'report.json'),'descriptionSha256':sha(run/'description.json'),'startStage':description['stages'][0]['id'],'endStage':viewer[0],'localEndFrame':viewer[1],'cumulativeEndFrame':cumulative,'score':economy[0]*10,'matchedTerminalFields':{name:{'original':a,'current':b} for name,(a,b) in fields.items()},'earlierGuardedBrowser':{'cumulativeFrame':32637,'score':73218790,'source':'85a60542'},'naturalEarlyEndMatchesPriorOriginalReference':True,'entireReplayCompleted':False,'allIntermediateStatesAccepted':False,'differentObservationBoundariesNotCompared':['player shot count','enemy count','RNG and callback timing'],'retired':True,'silentMemoryAudio':True,'graphicsRecordingOnly':True,'currentBrowserAccepted':False,'publicBrowserReadAttemptsTimedOut':True,'publicHttpStatus':200,'productionRuntimeGenerationObserved':'34f6e4b183b57e273555cae385ad12338484102a3a4517600662fb0784dc909c','productionChanged':False,'completeGame':False}
q.update(productionRuntimeGenerationObserved=generation,publicHeadersSha256=sha(O/'public-headers.txt'),productionManifestSha256=sha(O/'production-runtime-manifest.json'))
for p in [O/'qualified.json',R/'docs/porting/th14-current-legacy-marisaa-nov14.json']:p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'qualified':True,'score':q['score'],'cumulativeFrame':cumulative,'matchedTerminalFields':len(fields),'currentBrowserAccepted':False,'completeGame':False}))
