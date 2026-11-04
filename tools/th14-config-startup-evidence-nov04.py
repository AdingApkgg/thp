"""Verify the actual startup regression, retail reset branch and current delivery."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess

R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/config-startup-fallback-nov04'
K=R/'artifacts/th14/scene-camera-read-job-nov04';SHA=lambda raw:hashlib.sha256(raw).hexdigest()
PARENT='537a7f6e8e736c23f75bc7bd83c8f39631bfc591'

def evidence():
    bindings={}
    def read(path):
        path=Path(path).resolve(strict=True);assert path.is_relative_to(R)
        raw=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    def load(path):return json.loads(read(path))
    native=load(H/'native/native.json');assert len(native['cases'])==1568
    assert native['verifierSha256']==SHA(read(R/'tools/th14-config-startup-native-nov04.py'))
    assert native['resetIsActualRetailInstructions'] and native['crtMemsetAndLogBoundariesStubbed']
    assert native['controllerInputDeclared'] and not native['fileSystemOrOrdinaryOriginalUiExecuted']
    accepted=sum(row['accepted']for row in native['cases']);assert accepted==21
    default=bytes.fromhex(next(row['outputHex']for row in native['cases']if row['missing']))
    for row in native['cases']:
        assert row['joinedOrdinaryStartup']
        assert bytes.fromhex(row['outputHex'])==(bytes.fromhex(row['inputHex'])if row['accepted']else default)
        assert row['events']==([]if row['accepted']else ['log','memset-92'])
    old_app=subprocess.check_output(['git','-C',str(R/'tools/tmp/github-source-release'),'show',PARENT+':runtimes/th12/th12_web/cpp/sdl/Application.cpp']).decode().replace('\r\n','\n')
    app=read(R/'runtimes/th12/th12_web/cpp/sdl/Application.cpp');text=app.decode().replace('\r\n','\n')
    old_line='        if(SDL_GetPathInfo(config_path,nullptr)){std::vector<u8> saved;if(!read_file(config_path,saved,u32(session.config.bytes.size()))||!session.config.open(saved.data(),u32(saved.size()))){error=std::string("Invalid ")+config_path;return false;}saved_config_state=saved;}\n'
    start=text.index('        if(SDL_GetPathInfo(config_path,nullptr)){')
    stop=text.index('        audio.music_volume=',start)
    assert text[:start]+old_line+text[stop:]==old_app,'Only the startup config caller may change'
    assert '#if PORT_TITLE == 14' in text[start:stop] and 'session.config.reset();' in text[start:stop]
    assert text[text.index('EMSCRIPTEN_KEEPALIVE int th11_validate_file'):]==old_app[old_app.index('EMSCRIPTEN_KEEPALIVE int th11_validate_file'):]
    build_home=H/'build';build=load(build_home/'build.json');assert build['rootApplicationSourceSha256']==SHA(app)
    assert build['applicationObjectsRecompiled']==1 and build['coreObjectsReused']==141
    assert SHA(read(build_home/'application.wasm'))==build['wasmSha256']
    assert build['toolSha256']==SHA(read(R/'tools/th14-build-config-startup-nov04.py'))
    for name,row in build['sourceBindings'].items():assert SHA(read(R/name))==row['sha256']
    for row in build['applicationObjectBindings']+build['coreObjects']:assert SHA(read(row['path']))==row['sha256']
    syntax=load(build_home/'shared-syntax.json');assert syntax['sourceSha256']==SHA(app)
    assert syntax['cases']==[dict(title=title,returncode=0)for title in [12,13,14,16]]
    baseline=load(H/'baseline-invalid-signature/process-end.json');assert baseline['exitCode']!=0
    assert b'Invalid /save/th14.cfg'in read(H/'baseline-invalid-signature/process.log')
    cases_home=H/'application-cases';matrix=load(cases_home/'verified.json')
    assert matrix['toolSha256']==SHA(read(R/'tools/th14-config-startup-application-nov04.py'))
    assert matrix['verifiedActualApplicationConfigStartup'] and matrix['caseCount']==len(matrix['cases'])==13
    assert matrix['buildSha256']==SHA(read(build_home/'build.json'))
    frames=0
    for case in matrix['cases']:
        folder=cases_home/case['case'];run=load(folder/'gles/report.json')
        assert load(folder/'process-end.json')['exitCode']==0
        assert run['completed'] and not run['error'] and run['exitSaveCompleted'] and run['exitSaveRequested']
        assert run['wasmSha256']==build['wasmSha256'] and run['buildReportSha256']==SHA(read(build_home/'build.json'))
        assert run['actions'][-1]['state'][0]==4 and all(row['passed']for row in run['checks'])
        assert run['physicalAudioDevicesOpened']==0 and not run['browserRun']
        assert run['frames']==case['frames']==444;frames+=run['frames']
        config=read(folder/'gles/save/th14.cfg');assert SHA(config)==case['configurationSha256']
        assert SHA(read(folder/'gles/report.json'))==case['reportSha256']
        assert len(config)==92 and not run['completeGame'] and not run['nativeEquivalent']
        for name,row in run['finalSave'].items():assert SHA(read(folder/'gles/save'/name))==row['sha256']
    first=load(cases_home/'valid-user-options/gles/report.json');reload=load(cases_home/'fresh-process-reload/gles/report.json')
    assert reload['initialSave']==first['finalSave']==reload['finalSave']
    browser_home=H/'browser-retry1';browser=load(browser_home/'build.json');before=load(K/'browser/build.json')
    assert browser['compiledUnits']==1 and browser['reusedObjectCount']==145 and browser['sourceUnits']==146
    changed={name for name,row in browser['sourceBindings'].items()if row['sha256']!=before['sourceBindings'][name]['sha256']}
    assert changed=={'th12_web/cpp/sdl/Application.cpp'}
    for name,row in browser['sourceBindings'].items():assert SHA(read(browser_home/'source'/name))==row['sha256']
    assert browser['sourceBindings']['th12_web/cpp/sdl/Application.cpp']['sha256']==SHA(app)
    assert browser['rootUnrelatedResourceCryptExcluded']
    runtime=load(H/'runtime/package-report.json');launcher=load(H/'launcher/launcher-report.json');transport=load(H/'transport.json')
    assert runtime['buildSha256']==SHA(read(browser_home/'build.json'))
    assert runtime['wasmSha256']==browser['wasmSha256']==SHA(read(browser_home/'th14-sdl.wasm'))
    for name,row in runtime['files'].items():assert SHA(read(H/'runtime'/name))==row['sha256']
    for row in runtime['generatedResourceAliases']:assert os.path.samefile(R/row['source'],H/'runtime'/row['path'])
    assert runtime['generatedResourceBytesAliased']==414850582
    assert transport['reportSha256']==SHA(read(H/'launcher/launcher-report.json'))
    assert transport['verifiedTransport'] and transport['quietByDefault'] and transport['routes']==139 and len(transport['requests'])==27
    for item in [browser,runtime,launcher,transport]:assert not item['browserAcceptance'] and not item['completeGame'] and not item['nativeEquivalent']
    return dict(schema='th14/config-startup-evidence/1',verifiedConfigStartupRecovery=True,
        parentPublishedCommit=PARENT,unchangedGameplayCoreCommit='51fcb47992be0af65777d2ea87e9e409be6cc641',
        applicationSourceSha256=SHA(app),nativeComponentCases=1568,nativeAcceptedCases=21,nativeRejectedCases=1547,
        nativeResetInstructionsExecuted=True,declaredControllerAndCrtBoundaries=True,originalFileSystemOrUiAccepted=False,
        actualApplicationCases=13,actualApplicationFrames=frames,oldBinaryMalformedConfigFailureRetained=True,
        validConfigPreserved=True,freshProcessFilesByteUnchanged=True,strictImportValidationSourceUnchanged=True,
        sharedSyntaxTitles=[12,13,14,16],browserCompiledUnits=1,browserReusedUnits=145,browserWasmSha256=browser['wasmSha256'],
        httpChecks=27,routes=139,generatedResourceBytesAliased=414850582,physicalAudioDevicesOpened=0,
        browserAcceptance=False,persistenceInIndexedDbAccepted=False,wholeApplicationReplayAccepted=False,
        completeGame=False,nativeEquivalent=False,bindings=bindings,verifierSha256=SHA(Path(__file__).read_bytes()))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    output=args.output.resolve();assert output.is_relative_to(R);result=evidence()
    if args.check:assert json.loads(output.read_bytes())==result
    else:assert not output.exists();output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({key:result[key]for key in ['verifiedConfigStartupRecovery','nativeComponentCases','actualApplicationCases','browserAcceptance']}))

if __name__=='__main__':main()
