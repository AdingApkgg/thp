"""Recompute finite original per-slot evidence without publishing raw state."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/shot-lifetime-native-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest();bindings={}


def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data


def read(path):return json.loads(raw(path))


failed=read(H/'prefix-slots/native/report.json')
assert failed['callbacks']==31064 and failed['childExited'] and not failed['debugErrors']
assert failed['error']=="PermissionError(13, '拒绝访问。', None, 5)"
trace=raw(H/'prefix-slots/native/exception.txt').decode()
assert 'install(other)'in trace and 'WinError 5'in trace and 'context_error'in trace
assert failed['shotLifetimeSnapshots']==33
native=H/'prefix-slots-v2/native';n=read(native/'report.json');ended=read(native.parent/'process-end.json')
prep=read(H/'observer-slots-v2/prepared.json')
assert ended['exitCode']==1 and ended['guardStop']is None
assert n['callbacks']==35000 and n['childExited'] and not n['error'] and not n['debugErrors']
assert n['configuredMusicAndSoundVolumeZero'] and n['gameStateWordWrites']==1 and n['rngOrCounterWrites']==0
assert n['sourceSha256']==prep['observerSha256']==SHA(raw(native/'observer-source.py'))
assert prep['moduleSha256']==SHA(raw(R/'tools/th14-shot-lifetime-readonly-nov05.py'))
assert prep['criticalMutationCallAstUnchanged'] and prep['hardwareWatchProfileUnchanged']
assert prep['redundantUnchangedNoncurrentContextWritesSkipped'] and prep['otherContextErrorsStillFatal']
assert not prep['additionalGameMemoryWrites'] and not prep['additionalSuspendsOrResumes']
assert len(n['unchangedCrossThreadContextsNotRewritten'])==1
assert all(x['entireContextUnchanged'] and x['contextApiNotCalled']for x in n['unchangedCrossThreadContextsNotRewritten'])
lookup=read(H/'lookup-component.json');context=read(H/'context-noop-component/report.json')
assert lookup['passed'] and lookup['componentCases']==29
assert context['passed'] and context['fullInstallCases']==16 and context['sourceSha256']==n['sourceSha256']
assert context['otherApiFailuresStillFatal'] and context['pendingHardwareEventsStillDeferred']
for item,name in [(lookup,'th14-shot-lookup-component-nov05.py'),(context,'th14-context-noop-component-nov05.py')]:
    assert item['toolSha256']==SHA(raw(R/'tools'/name))
preflights=[]
for name in ['preflight-slots','preflight-slots-v2']:
    pf=read(H/name/'verified.json')
    assert pf['verifiedNativePreflight'] and pf['callbacks']==1200 and pf['nativeDebugExceptions']==0
    assert all(pf[k]for k in ['all32StateFieldsEqual','all75CameraWordsEqual','all4CursorFieldsEqual','all2HudFieldsEqual','nativeShotSnapshotsVerified'])
    preflights.append(dict(case=name,callbacks=1200,vm303Rows=pf['vm303Rows'],combatCheckpoints=pf['combatCheckpoints'],nativeShotSnapshots=pf['nativeShotSnapshots']))
selected=raw(native/'selected-state.u32');assert len(selected)==35000*128 and SHA(selected)==n['selectedSha256']
camera=raw(native/'world-camera.raw');tail=raw(native/'world-camera-tail.u32')
assert len(camera)==35000*292 and len(tail)==35000*8
full=b''.join(camera[i*292:(i+1)*292]+tail[i*8:(i+1)*8]for i in range(1,35000))
comparisons=[]
for case in ['off','on']:
    home=H/('comparison-'+case);result=read(home/'result.json');gate=read(home/'raw-verified.json')
    assert result['strictDriverExitCode']==result['rawVerifierExitCode']==0
    assert result['allOriginalFinalGatesUnchanged'] and gate['verifiedFiniteEvidence'] and gate['allCapturedCombatWordsEqual']
    assert gate['callbacks']==35000 and gate['vm303Rows']==710 and gate['combatCheckpoints']==584
    assert raw(home/'model/selected-state.u32')==selected
    assert raw(home/'model/full-camera.u32')==full
    model=read(home/'model/report.json');assert model['allRaw32ByteIdentical'] and not model['differenceCounts']
    comparisons.append(dict(case=case,callbacks=35000,all32StateFieldsEqual=True,
        all75CameraWordsEqual=True,cameraWords=34999*75,vm303Rows=710,combatCheckpoints=584,
        strictDriverExitCode=0,rawVerifierExitCode=0))
on=read(H/'comparison-on/result.json')
assert len(on['probeTransparentForCapturedState'])==4
for item in on['probeTransparentForCapturedState']:
    a=raw(H/'comparison-off/model'/item['file']);b=raw(H/'comparison-on/model'/item['file'])
    assert a==b and len(a)==item['bytes'] and SHA(a)==item['sha256']
slot=read(H/'slot-audit.json')
assert slot['toolSha256']==SHA(raw(R/'tools/th14-audit-native-shot-slots-nov05.py'))
assert slot['allComparedFieldsEqual'] and not slot['differenceCounts'] and not slot['uncomparedGeometry']
assert slot['snapshotPairs']==55 and slot['geometryVms']==3114
assert slot['vmAvailability']==dict(bothPresent=3114,bothAbsent=27)
assert slot['comparedFields']==dict(slotState=14080,shotWords=50256,specFields=9423,vmPresent=3141,
    vmWords=96534,vmIdentity=9342,quadWords=37368,quadVisibility=3114)
for name,item in slot['evidenceBindings'].items():assert SHA(raw(R/name))==item['sha256']
assert read(H/'slot-audit-private-differences.json')==[]
index=read(native/'shot-lifetime-index.json');assert len(index['snapshots'])==59
proof=read(H/'native-register-proof.json');assert proof['verifiedFiniteOriginalRegisterReadEvidence']
assert proof['instructionAccesses']==64 and proof['pairedNext32ReadsAndStores']==32
assert proof['verifierSha256']==SHA(raw(R/'tools/th14-shot-lifetime-register-evidence-nov05.py'))
driver=read(H/'comparison-driver-v2/prepared.json')
assert driver['allOriginalComparisonsAndFinalGatesByteIdentical']
assert driver['driverSha256']==SHA(raw(H/'comparison-driver-v2/driver.mjs'))
assert driver['disabledDriverSha256']==SHA(raw(H/'comparison-driver-v2/driver-off.mjs'))
for name in ['th14-prepare-shot-lifetime-native-nov05.py','th14-run-shot-lifetime-native-nov05.py',
    'th14-check-shot-lifetime-preflight-nov05.py','th14-prepare-shot-lifetime-comparison-nov05.py',
    'th14-compare-shot-lifetime-native-nov05.py']:raw(R/'tools'/name)
out=dict(schema='th14/original-shot-slots-public-evidence/1',verifiedFiniteOriginalShotSlots=True,
    failedFirstPrefix=dict(callbacks=31064,error='Win32 access denied during noncurrent Wow64SetThreadContext',
        debugExceptions=0,retainedSnapshots=33,accepted=False,retained=True),
    contextGuard=dict(fullInstallComponentCases=16,retailLookupComponentCases=29,
        onlyEntirelyUnchangedNoncurrentContextsSkipped=True,actualSkippedWrites=1,
        requiredContextWritesAndPendingExceptionGuardPreserved=True,otherApiErrorsFatal=True,
        previousFailureCauseProven=False),preflights=preflights,comparisons=comparisons,
    nativeCallbacks=35000,nativeDebugExceptions=0,nativeSlotSnapshots=59,matchedSlotSnapshots=55,
    extraNativeSnapshotsNotAccepted=4,activeShotObservations=3141,
    comparedFields=slot['comparedFields'],vmAvailability=slot['vmAvailability'],
    quadsBitIdentical=3114,quadWordsBitIdentical=37368,quadVisibilityEqual=3114,
    exactSlotsAndHandlesCompared=True,numericDifferencesNormalized=False,
    quadGeometryReconstructedUsingOriginalMachineCode=True,quadFpuControlWord=895,
    completeVmMemoryCompared=False,observedRngInstructions=64,pairedRngAccesses=32,
    probeTransparentForStateCameraCursorAndHud=True,allOriginalFinalGatesUnchanged=True,
    productionChanged=False,originalNineDifferencesClosed=False,ordinaryIndependentTimingAccepted=False,
    allModesAccepted=False,wholePixelsOrPcmCompared=False,completeGame=False,nativeEquivalent=False,
    rawRegistersSeedsCookiesAssetsOrBinariesUploaded=False,evidenceBindings=bindings,
    toolSha256=SHA(Path(__file__).read_bytes()))
(R/'docs/porting/th14-original-shot-slots-nov05.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(verifiedFiniteOriginalShotSlots=True,callbacks=35000,snapshotPairs=55,
    activeShotObservations=3141,quadsBitIdentical=3114,unchangedContextWritesSkipped=1,
    productionChanged=False,originalNineDifferencesClosed=False,completeGame=False)))
