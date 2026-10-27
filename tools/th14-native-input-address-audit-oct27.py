"""Audit the native sampler's input addresses without rewriting old observations.

Legacy captures read 90/94/98 and mislabeled the last two words as edges.
Those bytes remain original observations, but only held90 is an accepted held
field. Actual replay instructions and the corrected sampler are separate tests;
neither proves physical key delivery or ordinary native UI acceptance.
"""
from pathlib import Path
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home',type=Path,default=ROOT/'artifacts/th14/native-frame-readback-oct27')
    p.add_argument('--output',type=Path,default=ROOT/'docs/porting/th14-native-input-address-audit-oct27.json')
    p.add_argument('--check',action='store_true');a=p.parse_args();home=a.home.resolve();out=a.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT);bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    producer=read(ROOT/'tools/th14-native-device-observer-oct27.py')
    assert b'normalized_input_samples.append([present_count,u32(0x4d6a90),u32(0x4d6a9c),u32(0x4d6aa0)])'in producer
    legacy=[]
    for name in ('present-0420','present-0420-vms','present-0420-publications','startup-resource-pump','startup-ready-boundaries'):
        r=load(home/name/'report.json');source=read(home/name/'run-tool.py')
        assert r['sourceSha256']==SHA(source)and b"struct.unpack('<3I',read(0x4d6a90,12))"in source
        samples=r['normalizedInputSamplesAtPresent'];assert samples and all(row[1:]==[0,0,0]for row in samples)
        assert len(samples)==r['presentEntriesObserved']
        legacy.append(dict(directory=(home/name).relative_to(ROOT).as_posix(),samples=len(samples),
            actualReadAddresses=[0x4d6a90,0x4d6a94,0x4d6a98],heldAllZero=True,
            pressedAndReleasedObservedAtCorrectAddresses=False,legacyEdgeLabelsRejected=True,rawObservationRetained=True))
    edge=load(home/'input-address-edges/native.json')
    assert edge['passed']and len(edge['cases'])==360
    checker=read(home/'check-input-addresses.py');assert edge['toolSha256']==SHA(checker)
    for row in edge['cases']:
        held,previous=row['held'],row['previous']
        assert row['result']==[held,previous,(held^previous)&held,(held^previous)&(~held&0xffffffff)]
    corrected=load(home/'input-address-sampler-fixed/report.json')
    source=read(home/'input-address-sampler-fixed/run-tool.py')
    assert corrected['sourceSha256']==SHA(source)
    assert b'normalized_input_samples.append([present_count,u32(0x4d6a90),u32(0x4d6a9c),u32(0x4d6aa0)])'in source
    assert corrected['normalizedInputAddresses']==dict(held=0x4d6a90,pressed=0x4d6a9c,released=0x4d6aa0)
    assert corrected['frameReadbackCompleted']and corrected['childExited']and not corrected['error']
    assert len(corrected['normalizedInputSamplesAtPresent'])==20
    assert all(row[1:]==[0,0,0]for row in corrected['normalizedInputSamplesAtPresent'])
    assert corrected['readback']['statusesAtCaptureStop'][:5]==[0]*5 and corrected['readback']['cleanupResults']==[0,0,1]
    result=dict(schema='th14/native-input-address-audit/1',verifiedAddressCorrection=True,
        addresses=dict(held=0x4d6a90,previous=0x4d6a94,pressed=0x4d6a9c,released=0x4d6aa0),
        nativeControlledReplayEdgeCases=360,correctedActualProcessPresentSamples=20,correctedSamplesAllZero=True,
        legacyCaptures=legacy,oldRawBuffersAndReportsUnmodified=True,legacyPressedReleasedClaimWithdrawn=True,
        pixelAndRngComparisonsIndependentOfLegacyEdgeLabels=True,
        nativeReadbackPrivateCodeAndContextRedirectsDeclared=True,nativeChildExited=True,originalCodeGameFieldsAndInputUnwritten=True,
        physicalInputDeliveryAccepted=False,ordinaryNativeUiAccepted=False,completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.check:assert out.read_text()==encoded
    else:out.write_text(encoded)
    print(json.dumps({k:v for k,v in result.items()if k not in ('bindings','legacyCaptures')}))


if __name__=='__main__':main()
