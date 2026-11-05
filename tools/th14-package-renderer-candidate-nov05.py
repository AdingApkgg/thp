"""Package the declared TH14 GLES or WebGPU browser build without duplicating generated assets.



Generated, hash-checked font/FLAC resources are immutable local hard-link aliases.

Original game files are neither copied nor linked. The default preview is not

changed and packaging never opens or drives a browser.

"""

from pathlib import Path

import argparse

import hashlib

import importlib.util

import json

import os

import re

import subprocess



ROOT = Path(__file__).resolve().parents[1]

SHA = lambda raw: hashlib.sha256(raw).hexdigest()





def main():

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--build',type=Path,required=True)

    parser.add_argument('--output',type=Path,required=True)

    args=parser.parse_args();home=args.build.resolve(strict=True);out=args.output.resolve()

    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()

    out.mkdir(parents=True)

    spec=importlib.util.spec_from_file_location('storage',ROOT/'tools/th14-test-storage.py')

    storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage);storage.check_budget(out)

    build_raw=(home/'build.json').read_bytes();build=json.loads(build_raw)

    assert build['compiled']and build['title']==14 and not build['browserAcceptance']

    backend=build.get('backend')
    legacy_webgpu_report=backend is None
    if legacy_webgpu_report:
        assert build['schema']=='th14/browser-webgpu-candidate-build/1'
        backend='webgpu'
    assert backend in ('gles','webgpu')
    assert ('-DTH14_WEBGPU_BACKEND=1' in build['flags'])==(backend=='webgpu')
    assert ('-DTH14_ARCHIVE_WORKER=1' in build['flags'])==(backend=='webgpu')
    for symbol in ['th14_webgpu_invoke','th14_webgpu_frame']:
        assert (symbol in build['exports'])==(backend=='webgpu')

    version='1.00b-'+backend+'-candidate'

    gpu_files=['Th14WebGpuHost.mjs','Th14WebGpuRuntime.mjs','Th14WebGpuCore.mjs','Th14WebGpu.wgsl','Th14WebGpuResample.wgsl'] if backend=='webgpu' else []

    assert build['backgroundArchiveIntegration']==(backend=='webgpu')

    async_gles=backend=='gles' and 'th14_async_frame' in build['exports']
    assert ('th14_async_invoke' in build['exports'])==async_gles
    assert build['frameAndWorkerCallbacksSerialized']==(backend=='webgpu' or async_gles)
    if async_gles:gpu_files+=['Th14AsyncRuntime.mjs']

    gpu_files+=list(build.get('independentRestoreModuleFiles',{}))
    gpu_files+=list(build.get('pthreadModuleFiles',{}))

    assert SHA((home/'th14-sdl.wasm').read_bytes())==build['wasmSha256']

    assert SHA((home/'th14-sdl.mjs').read_bytes())==build['loaderSha256']

    for path,row in build['sourceBindings'].items():assert SHA((home/'source'/path).read_bytes())==row['sha256'],path

    courier=ROOT/'tools/tmp/github-source-release'

    base_commit=build['basePublishedCommit']

    assert re.fullmatch('[0-9a-f]{40}',base_commit)

    assert subprocess.check_output(['git','-C',str(courier),'cat-file','-t',base_commit],text=True).strip()=='commit'

    bindings={};files={};base_bindings={}

    def source(path):

        raw=path.read_bytes();bindings[str(path.relative_to(ROOT)).replace('\\','/')]=dict(bytes=len(raw),sha256=SHA(raw));return raw

    def put(name,raw):

        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);files[name]=dict(bytes=len(raw),sha256=SHA(raw))

    def base_source(name):

        assert name.startswith(('runtimes/th12/th12_web/sdl-runtime/','runtimes/th12/portable/browser/'))

        raw=subprocess.check_output(['git','-C',str(courier),'show',base_commit+':'+name])

        # Keep a small immutable provenance copy rather than binding a mutable

        # checkout whose HEAD may advance after the browser build completes.

        frozen=out/'platform-source'/name;frozen.parent.mkdir(parents=True,exist_ok=True);frozen.write_bytes(raw)

        bindings[frozen.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw))

        base_bindings[name]=dict(commit=base_commit,bytes=len(raw),sha256=SHA(raw))

        return raw

    shared='runtimes/th12/th12_web/sdl-runtime/'

    shell=base_source(shared+'shell.mjs').decode()

    if async_gles:
        # Patch the frozen platform base only at the callback ownership boundary.
        # Never mix unrelated mutable platform edits into a TH14 package.
        assert shell.count('const runtime=Module.th14WebGpuRuntime;')==2
        shell=shell.replace('const runtime=Module.th14WebGpuRuntime;','const runtime=Module.th14AsyncRuntime??Module.th14WebGpuRuntime;')
        old='if(Module.th14WebGpuRuntime){core=Module.th14WebGpuRuntime.bindCore(core);window.core=core;}'
        assert shell.count(old)==1
        shell=shell.replace(old,'const runtime=Module.th14AsyncRuntime??Module.th14WebGpuRuntime;\n if(runtime){core=runtime.bindCore(core);window.core=core;}')
        old='Module.onWebGpuError=error;';assert shell.count(old)==1
        shell=shell.replace(old,"""Module.onWebGpuError=error;
 Module.onAsyncError=error;
 if(typeof Module._th14_async_frame==='function'){
  const {Th14AsyncRuntime}=await import('./Th14AsyncRuntime.mjs');
  Module.th14AsyncRuntime=new Th14AsyncRuntime(Module);
 }""")

    replacements=[("game='th11'","game='th14'"),('th11-sdl.mjs','th14-sdl.mjs'),('th11-sdl.wasm','th14-sdl.wasm'),

        ('/savesth11','/savesth14'),('scoreth11','scoreth14'),('th11\\.cfg','th14\\.cfg'),("'th11.cfg'","'th14.cfg'"),

        ('th11_(?:','th14_(?:'),('/thcrap/th11/','/thcrap/th14/'),('TH11','TH14'),('地灵殿','辉针城')]

    for old,new in replacements:

        assert old in shell,old;shell=shell.replace(old,new)

    marker="/*TH14_BUILD_INFO*/{version:'development-incomplete',completeGame:false}"

    assert marker in shell;shell=shell.replace(marker,'/*TH14_BUILD_INFO*/'+json.dumps(dict(version=version,completeGame=False,nativeEquivalent=False,sha256=build['wasmSha256']),ensure_ascii=False))

    assert 'await mountData();'in shell;shell=shell.replace('await mountData();',"await mountData();\n Module.FS.symlink('/th14.dat','/th11.dat');")

    assert "await callCore('th11_initialize')"in shell and 'bindCore(core)'in shell and "case 'launch':await launch()"in shell

    put('shell.mjs',shell.encode())

    html=base_source(shared+'managed.html').decode().replace('地灵殿','辉针城').replace('<head>','<head><meta name="eagler-data-provider" content="retail-memory">');put('th14.html',html.encode())

    for name in ['managed.css','keyboard.mjs','directory-keyboard.mjs','eagler-host.mjs','runtime-epoch.mjs']:put(name,base_source(shared+name))

    motion=base_source('runtimes/th12/portable/browser/motion-replay.mjs').decode().replace('TH11','TH14').replace('t11r','t13r').replace('0x72313174','0x72333174').replace('74 31 31 72','74 31 33 72');put('motion-replay.mjs',motion.encode())

    for name in ['th14-sdl.wasm','th14-sdl.mjs',*gpu_files]:put(name,source(home/name))

    for name,row in build.get('archiveWorkerFiles',{}).items():

        raw=source(home/name);assert len(raw)==row['bytes'] and SHA(raw)==row['sha256'];put(name,raw)

    generated=ROOT/'runtimes/th14/th14_web/assets/sdl-native';resources=[];aliases=[]

    font_manifest=json.loads(source(generated/'fonts/manifest.json'));music_manifest=json.loads(source(generated/'music-verification.json'))

    assert len(font_manifest['files'])==10 and len(music_manifest)==18

    for folder,rows in [('fonts',font_manifest['files']),('music',music_manifest)]:

        for row in rows:

            name=row['file'];assert Path(name).name==name

            original=(generated/folder/name).resolve(strict=True);assert original.is_relative_to(generated.resolve())and original.is_file()

            with original.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()

            expected=row['sha256']if folder=='fonts'else row['encodedSha256'];assert digest==expected,name

            target=out/folder/name;target.parent.mkdir(parents=True,exist_ok=True)

            # Only generated, hash-bound immutable resources may be aliased.

            # The original retail archive and original music container are not.

            os.link(original,target);assert os.path.samefile(original,target)

            size=original.stat().st_size;files[folder+'/'+name]=dict(bytes=size,sha256=digest)

            resources.append(dict(path='/'+folder+'/'+name,url='./'+folder+'/'+name,bytes=size,sha256=digest))

            aliases.append(dict(path=folder+'/'+name,source=original.relative_to(ROOT).as_posix(),bytes=size,sha256=digest))

    put('resources.json',(json.dumps(dict(schema='eagler-sdl-resources/1',game='th14',resources=resources),indent=2)+'\n').encode())

    put('manifest.json',(json.dumps(dict(game='th14',protocol='eagler-touhou/1',adapter='sdl3-eagler',profile='production-candidate',

        version=version,completeGame=False,nativeEquivalent=False,features=dict(thprac=False,languages=False,focusHitbox=False),

        music=['midi','none'],touchReplay=True,execution=dict(kind='th14-sdl3-'+backend+'-candidate',backend=backend,sha256=build['wasmSha256'],loaderSha256=build['loaderSha256'])),indent=2)+'\n').encode())

    abi_script="const f=require('fs');const m=new WebAssembly.Module(f.readFileSync(process.argv[1]));console.log(JSON.stringify({exports:WebAssembly.Module.exports(m),imports:WebAssembly.Module.imports(m)}));"

    node=ROOT/'tools/emsdk/node/24.19.0_64bit/node.exe'

    if not node.exists():node=Path('C:/nvm4w/nodejs/node.exe')

    abi=json.loads(subprocess.check_output([str(node),'-e',abi_script,str(out/'th14-sdl.wasm')],text=True))

    names={row['name']for row in abi['exports']};assert set(build['exports'])<=names

    assert not any(re.match(r'th11_(probe_|audio_probe|audio_samples|tick$)',name)for name in names)

    for name in ['shell.mjs',*[name for name in gpu_files if name.endswith('.mjs')]]:

        subprocess.run([str(node),'--check',str(out/name)],check=True,capture_output=True)

    put('runtime-files.json',(json.dumps(dict(schema='eagler-touhou/runtime-directory/1',game='th14',files=files),indent=2)+'\n').encode())

    result=dict(schema='th14/renderer-candidate-package/1',backend=backend,prepared=True,buildSha256=SHA(build_raw),wasmSha256=build['wasmSha256'],

        backendBoundToCompilerFlagsAndExports=True,legacyWebGpuBuildReport=legacy_webgpu_report,
        backgroundArchiveIntegration=build['backgroundArchiveIntegration'],frameAndWorkerCallbacksSerialized=build['frameAndWorkerCallbacksSerialized'],

        files=files,sourceBindings=bindings,frozenPlatformCommit=base_commit,frozenPlatformBindings=base_bindings,generatedResourceAliases=aliases,generatedResourceBytesAliased=sum(row['bytes']for row in aliases),

        originalRetailFilesLinked=False,originalAssetsCopied=False,noDiagnosticGameControlExports=True,abi=abi,

        toolSha256=SHA(Path(__file__).read_bytes()),defaultPreviewChanged=False,browserRun=False,browserAcceptance=False,

        completeGame=False,nativeEquivalent=False,scope='Local managed TH14 renderer candidate with its declared backend and async-aware shell, exact ABI and source hashes. Only generated immutable font/FLAC resources are hard-linked to avoid duplication. No browser launch, UI, presentation, persistence or whole-game acceptance.')

    (out/'package-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key]for key in ['prepared','wasmSha256','generatedResourceBytesAliased','defaultPreviewChanged','browserAcceptance']}))





if __name__=='__main__':main()
