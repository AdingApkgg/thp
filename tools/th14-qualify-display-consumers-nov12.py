"""Adopt only measured size-consumer changes, retaining the independent wave mismatch."""
from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/display-consumers-nov12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
P=load(H/'prepared.json');S=Path(P['sourceRoot']);B=load(H/'component/build.json');C=load(H/'component/checked.json');L=load(H/'legacy/checked.json')
assert C['passed'] and C['controlRejected'] and B['normalAccess'] and B['freshlyCompiledUnits']==2 and B['unchangedVerifiedProviders']==139
assert C['checkerSha256']==sha(R/'tools/th14-check-display-consumers-nov12.mjs')
assert C['nativeReportSha256']==sha(H/'deformation-native.json') and C['fadeReportSha256']==sha(H/'fade-native/native.json')
assert C['results']['candidate']['updateConsumerDifferences']==0
assert C['results']['candidate']['wavePositionDifferences']==178 and not C['fullWavePositionsAccepted']
assert L['allByteIdentical'] and len(L['objectPairs'])==6
for row in L['objectPairs']:
    for obj in row['objects']:assert sha(R/obj['object'])==obj['objectSha256']
for row in B['currentProviders']:assert sha(R/row['object'])==row['objectSha256'] and sha(S/row['source'])==row['sourceSha256']
for label,digest in B['modules'].items():assert sha(H/f'component/{label}.wasm')==digest
for name,digest in P['sourceBindings'].items():assert sha(S/name)==digest,name
assert len(P['changes'])==2
for row in P['changes']:assert sha(R/row['path'])==row['beforeSha256'] and sha(S/row['path'])==row['afterSha256']
assert sha(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
assert not (H/'qualified.json').exists()
for row in P['changes']:
    p=R/row['path'];tmp=p.with_suffix(p.suffix+'.display-consumers-tmp');tmp.write_bytes((S/row['path']).read_bytes());os.replace(tmp,p)
for name,digest in P['sourceBindings'].items():assert sha(R/name)==digest,name
provider=load(R/P['baseManifest']);provider['currentProviders']=B['currentProviders'];provider['sourceBindings']=P['sourceBindings']
provider['sourceSnapshotPrefix']=str(S);provider['providerActualFlags']=B['flags'];provider['all141FreshForCurrentSource']=False
provider['changedConsumerUnitsFresh']=2;provider['unchangedProviderUnitsHashVerified']=139;provider['completeGame']=False
(H/'current-provider-bindings.json').write_text(json.dumps(provider,indent=2)+'\n')
report=dict(schema='thp/th14-display-consumers/1',sourceAdopted=True,changedFiles=P['changes'],currentSourceBindings=P['sourceBindings'],
    fadeCases=288,fadeWords=7488,rectangleCases=12,rectangleWords=34680,updateTimelines=48,updateFrames=96,
    updateConsumerWords=194496,consumerDifferences=0,oldCodeControlRejected=True,
    wavePositionDifferences=178,fullWavePositionsAccepted=False,legacyObjectPairs=6,allLegacyObjectPairsByteIdentical=True,
    realD3dxDllUnderUnicorn=True,originalGameFloatingPointEnvironmentUnmeasured=True,
    nativeGameStarted=False,gpuStarted=False,wholePixelsAccepted=False,completeGame=False,
    proofBindings={p.relative_to(R).as_posix():sha(p) for p in [H/'component/build.json',H/'component/checked.json',H/'deformation-native.json',H/'fade-native/native.json',H/'legacy/checked.json']},
    qualifierSha256=sha(Path(__file__)))
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('currentSourceBindings','proofBindings','changedFiles')}))
