"""Adopt the measured supported-display world-strip translation fix."""
from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/world-strip-origin-nov12'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_bytes())
B=load(H/'component/build.json');C=load(H/'component/checked.json');L=load(H/'legacy/checked.json');S=Path(B['sourceRoot'])
assert C['passed'] and C['oldCodeControlRejected'] and C['results']['candidate']['words']==3456 and C['results']['baseline']['differentWords']==54
assert C['checkerSha256']==sha(R/'tools/th14-check-world-strip-origin-nov12.mjs') and C['nativeReportSha256']==sha(H/'native.json')
assert B['normalAccess'] and B['freshlyCompiledUnits']==1 and B['unchangedVerifiedProviders']==140
assert L['allByteIdentical'] and len(L['objectPairs'])==3
for row in L['objectPairs']:
    for obj in row['objects']:assert sha(R/obj['object'])==obj['objectSha256']
for row in B['currentProviders']:assert sha(R/row['object'])==row['objectSha256'] and sha(S/row['source'])==row['sourceSha256']
for name,digest in B['sourceBindings'].items():assert sha(S/name)==digest,name
for label,digest in B['modules'].items():assert sha(H/f'component/{label}.wasm')==digest
assert len(B['changes'])==1 and not (H/'qualified.json').exists()
for row in B['changes']:assert sha(R/row['path'])==row['beforeSha256'] and sha(S/row['path'])==row['afterSha256']
assert sha(R/'runtimes/th12/th12_web/cpp/game/ResourceCrypt.cpp')=='a291010053963e25dadef2be15ddb3c217110cd2377fc495402ef375150f8c45'
for row in B['changes']:
    p=R/row['path'];tmp=p.with_suffix(p.suffix+'.world-strip-tmp');tmp.write_bytes((S/row['path']).read_bytes());os.replace(tmp,p)
for name,digest in B['sourceBindings'].items():assert sha(R/name)==digest,name
provider=load(R/'artifacts/th14/display-consumers-nov12/current-provider-bindings.json');provider.update(currentProviders=B['currentProviders'],sourceBindings=B['sourceBindings'],sourceSnapshotPrefix=str(S),providerActualFlags=B['flags'],changedWorldStripUnitFresh=1,unchangedProviderUnitsHashVerified=140,completeGame=False)
(H/'current-provider-bindings.json').write_text(json.dumps(provider,indent=2)+'\n')
report=dict(sourceAdopted=True,changedFiles=B['changes'],currentSourceBindings=B['sourceBindings'],cases=216,comparedMatrixWords=3456,differentMatrixWords=0,oldCodeDifferentMatrixWords=54,
    normalProviders=141,fixtureNormalAccess=True,legacyObjectPairs=3,allLegacyObjectPairsByteIdentical=True,wholeNativeCallback=False,upstreamNativeScaleAndRotationProducerNotCompared=True,
    scope=C['scope'],gpuOrPixelsAccepted=False,completeGame=False,proofBindings={p.relative_to(R).as_posix():sha(p) for p in [H/'native.json',H/'component/build.json',H/'component/checked.json',H/'legacy/checked.json']},qualifierSha256=sha(Path(__file__)))
(H/'qualified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('currentSourceBindings','proofBindings','changedFiles')}))
