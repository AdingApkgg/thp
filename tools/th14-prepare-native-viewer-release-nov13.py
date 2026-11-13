"""Prepare a viewer-only Runtime delta and reuse the validated COW packager."""
from pathlib import Path
import ast,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/native-viewer-application-nov13/release';B=H.parent/'browser';U=H/'upload';U.mkdir(exist_ok=False)
load=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
core=load(H.parent/'publication/published.json')['commit'];frontend='c091d46188ad5edf61963ecb4f4da2171d96c345';build=load(B/'build.json')
gh='C:/Program Files/GitHub CLI/gh.exe';tree=json.loads(subprocess.check_output([gh,'api','repos/AdingApkgg/thp/git/trees/'+core+'?recursive=1'],timeout=60));assert not tree.get('truncated')
blobs={x['path']:x.get('sha')for x in tree['tree']}
for n,h in build['sourceBindings'].items():
 b=(R/n).read_bytes();assert sha(b)==h and blobs[n]==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),n
directory=load(H/'baseline/runtime-files.json');manifest=load(H/'baseline/manifest.json');assert len(directory['files'])==39
old_wasm=manifest['execution']['sha256'];old_version=manifest['version'];assert old_wasm=='e7492a1951778c146ee48bfdf29dde9f89c39300383797238fe382694a33509d'
manifest['version']='1.00b-thp-'+core[:8];manifest['execution']['sha256']=build['sha256'];manifest['execution']['loaderSha256']=build['loaderSha256'];assert manifest['completeGame']is False
files={'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode()}
for n,meta in build['runtimeFiles'].items():
 assert n in directory['files'],n;b=(B/n).read_bytes();assert sha(b)==meta['sha256']and len(b)==meta['bytes']
 if n=='shell.mjs':
  s=b.decode();assert s.count(old_wasm)==1;b=s.replace(old_wasm,build['sha256']).replace(old_version,manifest['version']).encode()
 if directory['files'][n]!=dict(bytes=len(b),sha256=sha(b)):files[n]=b
for n,b in files.items():directory['files'][n]=dict(bytes=len(b),sha256=sha(b))
files['runtime-files.json']=(json.dumps(directory,indent=2)+'\n').encode()
for n,b in files.items():p=U/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
release='/home/i/Code/th14-release/viewer-nov13-'+core[:8]
j=dict(sourceCommit=core,frontendSource=frontend,remoteRelease=release,wasmSha256=build['sha256'],loaderSha256=build['loaderSha256'],
 changedFiles=[dict(path=n,bytes=len(b),sha256=sha(b))for n,b in files.items()],runtimeFiles=39,rawAssetsTransferred=False,preserveExistingVorbisTracks=18,
 allPublishedBuildSourceBlobsVerified=len(build['sourceBindings']),copyStrategy='Btrfs reflink, distinct inodes; existing generations preseeded with COW',completeGame=False)
for p in [H/'release-input.json',U/'release-input.json']:p.write_text(json.dumps(j,indent=2)+'\n')
# Reuse the exact canonical packaging and allocation logic already deployed.
tree=ast.parse((R/'tools/th14-prepare-behavior-runtime-release-nov13.py').read_text())
assignment=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='script'for t in x.targets))
script=assignment.value.func.value.value
assert script.count('option-init-nov13-59a8cc4c')==1
script=script.replace('option-init-nov13-59a8cc4c','behavior-nov13-336a1ff0')
script=script.replace("site/'vendor/country-flag-icons/LICENSE',site/'vendor/tinysynth/LICENSE'","site/'launcher/public/vendor/country-flag-icons.LICENSE',site/'launcher/public/vendor/webaudio-tinysynth.LICENSE'")
script=script.replace("assert not subprocess.check_output", "assert len(license_hashes)==2\nassert not subprocess.check_output",1)
(H/'prepare-arch.sh').write_text(script.replace('RELEASE',release),encoding='utf8',newline='\n')
activate=(R/'artifacts/th14/behavior-release-nov13/activate-arch.sh').read_text()
activate=activate.replace('behavior-nov13-336a1ff0','viewer-nov13-'+core[:8]).replace('hosted-before-336a1ff0','hosted-before-'+core[:8])
activate=activate.replace('336a1ff0f9fdd197eba3ff5d8e7f94f1e31c34b4',core).replace('c533083814963d42c522ac4aaa429df3f6138208',frontend).replace(old_wasm,build['sha256'])
(H/'activate-arch.sh').write_text(activate,encoding='utf8',newline='\n')
(H/'verify-public-compressed.py').write_bytes((R/'artifacts/th14/behavior-release-nov13/verify-public-compressed.py').read_bytes())
print(json.dumps(dict(sourceCommit=core,frontendSource=frontend,changedRuntimeFiles=len(files),bytes=sum(map(len,files.values())),remoteRelease=release)))
