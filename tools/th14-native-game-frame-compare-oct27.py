"""Strictly compare an actual automatic-demo Present with production C++.

Writes a diagnostic before returning nonzero for any pixel, VM or registry
difference. Publication-serial pairing is separately labelled exploratory;
it cannot change the strict result or normalize the original FPS pixels.
"""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,struct

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','port','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();n=a.native.resolve();q=a.port.resolve();out=a.output.resolve()
    assert all(x.is_relative_to(ROOT/'artifacts/th14')for x in (n,q,out))and not out.exists()
    bindings={}
    def read(path):
        path=path.resolve();assert path.is_relative_to(ROOT);raw=path.read_bytes()
        bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    nr=load(n/'report.json');pr=load(q/'report.json');nv=load(n/'live-vms-before-readback.json')
    assert nr['childExited']and nr['frameReadbackCompleted']and not nr['error']and pr['completed']and not pr['error']
    assert nr['sourceSha256']==SHA(read(n/'run-tool.py'))and pr['toolSha256']==SHA(read(q/'run-tool.py'))
    assert nr['originalCodeWrites']==nr['gameStateWrites']==0 and not nr['inputInjection']
    assert nr['threadContextRedirects']==2 and nr['readback']['statusesAtCaptureStop'][:5]==[0]*5
    assert nr['readback']['cleanupResults']==[0,0,1]
    trigger=nr['plan'].get('captureStageTriggerObserved',nr['plan'].get('captureTriggerObserved'))
    assert trigger is True and len(pr['captures'])==1
    s=next(r for r in nr['rows']if r['kind']=='native-Present-entry'and r['ordinal']==nr['plan']['capturePresentOrdinal'])
    c=pr['captures'][0];assert nv['presentOrdinal']==s['ordinal']and nv['readOnly']and nv['readBeforeDiagnosticCalls']
    pvraw=read(q/c['liveAnimations']['file']);assert SHA(pvraw)==c['liveAnimations']['sha256'];pv=json.loads(pvraw)
    assert pv['complete']and pv['comparedValues']==303 and len(pv['rows'])==pv['expected']
    state=pr['actions'][-1]['state'];rng=struct.unpack('<HHIHHI',bytes.fromhex(s['rngHex']))
    assert state[0]==1 and state[1]==s['stage']and state[6]==s['stageFrame']
    assert c['referenceState'][:3]==[s['originalInitialTicks'],s['originalProcessCookie'],s['idleCounter']]
    native_rng=[rng[0],rng[2],rng[3],rng[5]]
    port_rng=c['referenceState'][3:7]
    rng_equal=native_rng==port_rng
    globals_=s['selectedGlobalWords'];selected={'character':(globals_[0],state[13]),'subtype':(globals_[1],state[14]),
        'difficulty':(globals_[3],state[15]),'scoreUnits':(globals_[2],state[9]),'power':(globals_[12],state[8]),'lives':(globals_[15],state[7])}
    selected_equal=all(x==y for x,y in selected.values())
    expected=read(n/nr['readback']['file']);actual=read(q/c['file']);assert len(expected)==len(actual)==1228800
    assert SHA(expected)==nr['readback']['pixelSha256']and SHA(actual)==c['sha256']
    differences=[i for i,(x,y)in enumerate(zip(expected,actual))if x!=y];pixels={i//4 for i in differences}
    bounds=[min(x%640 for x in pixels),min(x//640 for x in pixels),max(x%640 for x in pixels),max(x//640 for x in pixels)]if pixels else None
    spec=importlib.util.spec_from_file_location('game_frame_vm_words',ROOT/'tools/th14-native-title-live-compare-oct27.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);read(ROOT/'tools/th14-native-title-live-compare-oct27.py')
    address={struct.unpack_from('<I',bytes.fromhex(r['rawVmHex']),0x570)[0]:r['handle']for r in nv['rows']}
    native_ids={r['handle']for r in nv['rows']};by_id={r[0]:r for r in pv['rows']}
    assert len(native_ids)==len(nv['rows'])and len(by_id)==len(pv['rows'])
    strict=[];native_words={}
    for row in nv['rows']:
        fields,words=m.native_words(row,address);native_words[row['handle']]=words
        if row['handle']not in by_id:strict.append(dict(handle=row['handle'],missingInPort=True));continue
        for field,x,y in zip(fields,words,by_id[row['handle']]):
            if x!=y:strict.append(dict(handle=row['handle'],file=row['file'],script=row['script'],field=field,native=x,port=y))
    extra=sorted(set(by_id)-native_ids)
    order=[r['handle']for r in nv['rows']]==[r[0]for r in pv['rows']]
    native_serial={r['handle']>>13:r for r in nv['rows']};port_serial={r[0]>>13:r for r in pv['rows']}
    assert len(native_serial)==len(nv['rows'])and len(port_serial)==len(pv['rows'])
    diagnostic=[];paired=set(native_serial)==set(port_serial);mapped=0
    if paired:
        remap={r['handle']:port_serial[k][0]for k,r in native_serial.items()}
        mapped=sum(x!=y for x,y in remap.items())
        links={'handle','parentHandle','registryNextHandle','registryPreviousHandle','childNextHandle','childPreviousHandle'}
        for serial,row in native_serial.items():
            for field,x,y in zip(fields,native_words[row['handle']],port_serial[serial]):
                if field in links:x=remap.get(x,x)
                if x!=y:diagnostic.append(dict(serial=serial,file=row['file'],script=row['script'],field=field,native=x,port=y))
    exact=rng_equal and selected_equal and not differences and not strict and not extra and order
    report=dict(strictAllSelectedStateLiveVmsAndPixelsEqual=exact,actualNativeGameFrame=True,
        nativePresent=s['ordinal'],stage=s['stage'],nativeControllerFrame=s['stageFrame'],portBattleFrame=state[6],portApplicationFrame=pr['frames'],
        externalStartupInputsAndBothRngEqual=rng_equal,externalStartupInputsEqual=True,
        bothRngEqual=rng_equal,nativeRngWords=native_rng,portRngWords=port_rng,
        selectedFields=selected,selectedFieldsEqual=selected_equal,
        nativeLiveVms=len(nv['rows']),portLiveVms=len(pv['rows']),wordsPerVm=303,
        strictVmDifferences=strict,strictExtraPortHandles=extra,strictRegistryOrderEqual=order,
        pixelBytesCompared=1228800,pixelDifferentBytes=len(differences),pixelDifferentPixels=len(pixels),pixelDifferenceBounds=bounds,
        pixelDifferentBytesPerChannel=dict(collections.Counter(i%4 for i in differences)),
        pixelFirstDifferences=[dict(x=i//4%640,y=i//2560,channel=i%4,native=expected[i],port=actual[i])for i in differences[:24]],
        noPixelToleranceOrFpsNormalization=True,nativePixelSha256=SHA(expected),portPixelSha256=SHA(actual),
        exploratorySerialSetsEqual=paired,exploratoryExplicitlyMappedDifferentHandles=mapped,
        exploratoryAfterHandleMappingDifferences=diagnostic,exploratoryMappingIsNotStrictAcceptance=True,
        nativeReadbackPrivateCodeAndTwoContextRedirectsDeclared=True,nativeChildExited=True,
        ordinaryNativeUiAccepted=False,completeGame=False,nativeEquivalent=False,browserAcceptance=False,
        sourceSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ('strictAllSelectedStateLiveVmsAndPixelsEqual','nativePresent','stage','nativeControllerFrame',
        'portApplicationFrame','externalStartupInputsAndBothRngEqual','selectedFieldsEqual','nativeLiveVms','portLiveVms','pixelDifferentBytes',
        'pixelDifferentPixels','pixelDifferenceBounds','strictRegistryOrderEqual','exploratoryExplicitlyMappedDifferentHandles')}))
    print(json.dumps(dict(strictDifferenceEntries=len(strict),strictMissingNativeHandles=sum(bool(x.get('missingInPort'))for x in strict),
        strictExtraPortHandles=len(extra),exploratoryDifferenceWords=len(diagnostic))))
    if not exact:raise SystemExit(1)


if __name__=='__main__':main()
