"""Bind finite cold-start worker parsing, rejection and recovery observations."""
from pathlib import Path
import argparse,hashlib,json
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-frame-readback-oct28';SHA=lambda b:hashlib.sha256(b).hexdigest()
def evidence():
    bindings={}
    def raw(path):
        path=path.resolve(strict=True);assert path.is_relative_to(R);b=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(b),sha256=SHA(b));return b
    def load(path):return json.loads(raw(path))
    home=H/'boot-anm-browser-candidate';b=load(home/'build.json');base=load(H/'stage-ecl-browser-candidate-v2/build.json');app='th12_web/cpp/sdl/Application.cpp'
    assert b['basePublishedCommit']=='1c9995853ba9d458810b77e03dca1d3b26ab1678'and b['compiledUnits']==1 and b['reusedObjectCount']==145
    assert [n for n in b['objectHashes']if b['objectHashes'][n]!=base['objectHashes'][n]]==[app]
    assert [n for n in b['sourceBindings']if b['sourceBindings'][n]!=base['sourceBindings'][n]]==[app]
    assert SHA(raw(R/'runtimes/th12'/app))==b['sourceBindings'][app]['sha256']and SHA(raw(home/'source'/app))==b['sourceBindings'][app]['sha256']
    assert SHA(raw(home/'th14-sdl.wasm'))==b['wasmSha256']and b['wasmBytes']==2744264
    assert b['toolSha256']==SHA(raw(R/'tools/th14-build-webgpu-release.py'))and b['rootUnrelatedResourceCryptExcluded']
    assert b['sourceBindings']['th12_web/cpp/game/ResourceCrypt.cpp']['sha256']=='d57118f1114f3909c42a2e99e7df30e625f6563247a8118cd14bb9f68a0f97ef'
    assert b['archiveWorkerFiles']==base['archiveWorkerFiles']
    for name,row in b['archiveWorkerFiles'].items():assert len(raw(home/name))==row['bytes']and SHA(raw(home/name))==row['sha256']
    worker=load(home/'archive-worker/build.json');fixture=load(H/'boot-anm-transfer-component/build.json');p=load(H/'boot-anm-transfer-component/check.json')
    assert p['passed']and p['anmEntries']==57 and p['transferredAnmBytes']==245717904 and p['rejectedPackets']==68
    assert p['workerBuildSha256']==fixture['workerBuildSha256']==SHA(raw(home/'archive-worker/build.json'))
    assert p['fixtureBuildSha256']==SHA(raw(H/'boot-anm-transfer-component/build.json'))and p['checkerSha256']==SHA(raw(R/'tools/th14-anm-transfer-check-oct28.mjs'))
    wanted={'front.anm','bullet.anm','effect.anm','title.anm','title_v.anm'};assert wanted.issubset({x['name']for x in p['rows']if x['allFieldsAndBytesEqual']})
    transport=load(H/'boot-anm-launcher/http-check.json');assert transport['verifiedTransport']and transport['routes']==139 and len(transport['requests'])==27
    served=load(H/'boot-anm-launcher/served-restored.json');assert served['wasmSha256']==b['wasmSha256']and served['quietInjectedIntoParentAndIframe']
    fault=load(H/'boot-anm-fault-front/launcher-report.json');assert fault['testOnlyFaultInjection']and not fault['productionFilesModified']and fault['wasmSha256']==b['wasmSha256']
    assert fault['controlToolSha256']==SHA(raw(R/'tools/th14-boot-worker-control-oct29.py'))
    fault_served=load(H/'boot-anm-fault-front/served.json');assert fault_served['testOnly']and len(fault_served['checks'])==3
    endpoint='runtime/th14/Th14ArchiveDecodeEndpoint.mjs';changed=raw(R/fault['files'][endpoint]['path']);original=raw(home/'Th14ArchiveDecodeEndpoint.mjs')
    injected=b"      if (Array.isArray(message.names) && message.names.includes('front.anm')) throw new Error('TH14_TEST_ONLY_BOOT_FRONT_REJECTION');\n"
    assert changed.count(injected)==1 and changed.replace(injected,b'',1)==original
    ui=H/'boot-anm-browser-ui';flow=load(ui/'flow-receipt.json');assert all(flow[k]for k in ('titleObserved','automaticDemoObserved','frontWorkerRejectionObserved','unmodifiedWorkerRestored','shortReplayNaturalEndObserved','returnedReplayList'))
    assert flow['selectedShortHud']==dict(score=3100,lives=1,powerHundredths=103,graze=2)
    for name in ('title','automatic-demo','front-worker-rejected','restored-title','replay-list','short-natural-end','returned-replay-list'):
        assert raw(ui/(name+'.jpg'))[:3]==b'\xff\xd8\xff';ax=raw(ui/(name+'.ax.txt')).decode();assert '本机测试静音'in ax and 'runtimeEpoch='in ax
        if name=='front-worker-rejected':assert 'TH14 background boot resource decode failed'in ax
        else:assert '音频 0ms'in ax
    raw(ui/'front-worker-rejected.logs.json')
    return dict(verifiedFiniteColdBootWorkerParsing=True,coldBootAnmJobs=['front.anm','bullet.anm','effect.anm','title.anm','title_v.anm'],compiledApplicationUnits=1,validatedReusedObjects=145,mainWasmBytes=b['wasmBytes'],mainWasmSha256=b['wasmSha256'],workerWasmBytes=worker['wasmBytes'],workerWasmSha256=worker['wasmSha256'],workerFilesByteIdenticalToStageEclBuild=True,actualWorkerAnmCases=57,parsedPacketBytesCompared=245717904,malformedPacketsRejected=68,actualBrowserFrontWorkerRejectionObserved=True,unchangedProductionMainWasmDuringRejection=True,unmodifiedWorkerRestoredAndShortNaturalEndObserved=True,selectedShortHud=flow['selectedShortHud'],allLoadingWorkOnCpuWorker=False,originalIndependentThreadSchedulingAccepted=False,completeBrowserAcceptance=False,currentBuildInheritsFrozenFullCampaign=False,completeGame=False,nativeEquivalent=False,verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();proof=evidence();target=R/'docs/porting/th14-boot-worker-verified-oct29.json'
    if a.check:assert json.loads(target.read_bytes())==proof
    else:target.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:proof[k]for k in ('verifiedFiniteColdBootWorkerParsing','compiledApplicationUnits','actualBrowserFrontWorkerRejectionObserved','completeGame')}))
if __name__=='__main__':main()
