"""Prepare only the changed runtime files; reuse the deployed assets and Vorbis."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/option-initial-state-release-nov13';H.mkdir()
P=R/'artifacts/th14/option-refresh-oracle-nov13';GH='C:/Program Files/GitHub CLI/gh.exe'
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','i@100.75.145.75']
load=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
published=load(P/'release-published.json');commit=published['commit'];assert commit=='59a8cc4cc5ae404d8439019b35f4915f75c03c5d'
build=load(P/'browser/build.json');assert build['unitsRecompiled']==1 and build['objectsVerifiedReused']==145
assert load(P/'current-replay/qualified.json')['allChildrenWorkersHostsGpuAndClockRetired']
assert load(R/'artifacts/th14/camera-copy-constructor-nov13/result.json')['passed']
tree=json.loads(subprocess.check_output([GH,'api','repos/AdingApkgg/thp/git/trees/'+commit+'?recursive=1'],timeout=45))
assert not tree.get('truncated');blobs={e['path']:e.get('sha')for e in tree['tree']}
for name,digest in build['sourceBindings'].items():
 raw=(R/name).read_bytes();assert sha(raw)==digest
 assert blobs[name]==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),name
remote='''from pathlib import Path
import json,subprocess,shutil
p=Path('/home/i/Code/th14-release/player-init-nov13-b8e36ef2/input-runtime')
j={n:(p/n).read_text()for n in ['manifest.json','shell.mjs','runtime-files.json']}
j['coreHead']=subprocess.check_output(['git','-C','/home/i/Code/th14-site/ports/th14','rev-parse','HEAD'],text=True).strip()
j['frontendHead']=subprocess.check_output(['git','-C','/home/i/Code/th14-site','rev-parse','HEAD'],text=True).strip()
j['freeBytes']=shutil.disk_usage('/home/i/Code/th14-release').free
print(json.dumps(j))
'''
info=json.loads(subprocess.check_output([*ssh,'python3 -'],input=remote.encode(),timeout=45))
(H/'remote-before.json').write_text(json.dumps(info,indent=2)+'\n')
assert info['coreHead']=='b8e36ef27d96238352f5edaf9b368ca23394ceb3'
assert info['frontendHead']=='bd9badc9fe2c2766d732d7722eaa48026fdfce6f'
assert info['freeBytes']>8*1024**3
upload=H/'upload';upload.mkdir()
wasm=(P/'browser/th14-sdl.wasm').read_bytes();loader=(P/'browser/th14-sdl.mjs').read_bytes()
assert sha(wasm)==build['sha256']and sha(loader)==build['loaderSha256']
manifest=json.loads(info['manifest.json']);old_wasm=manifest['execution']['sha256'];old_version=manifest['version']
assert old_wasm=='5a1badbd123a966e78a22efbd8e64e3c0dbf553f50afcd39a2d81e6305a749fe'
assert manifest['execution']['loaderSha256']==sha(loader)
manifest['version']='1.00b-thp-'+commit[:8];manifest['execution']['sha256']=sha(wasm)
assert not manifest['completeGame']
shell=info['shell.mjs'];assert shell.count(old_wasm)==1
shell=shell.replace(old_wasm,sha(wasm)).replace(old_version,manifest['version'])
files={'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode(),'shell.mjs':shell.encode(),'th14-sdl.wasm':wasm}
directory=json.loads(info['runtime-files.json']);assert len(directory['files'])==39
for name,data in files.items():directory['files'][name]=dict(bytes=len(data),sha256=sha(data))
files['runtime-files.json']=(json.dumps(directory,indent=2)+'\n').encode()
for name,data in files.items():(upload/name).write_bytes(data)
receipt=dict(sourceCommit=commit,frontendSource=info['frontendHead'],frontendRuntimeCodeSource='2eeb8db4b6f2ef337656d4d979c60abfaca579be',
 publishedBuildSourcesVerified=369,wasmSha256=sha(wasm),loaderSha256=sha(loader),runtimeInputFiles=39,
 changedFiles=[dict(path=n,bytes=len(b),sha256=sha(b))for n,b in files.items()],rawGameAssetsTransferred=False,
 existingVorbisTracksPreserved=True,loaderUnchanged=True,remoteRelease='/home/i/Code/th14-release/option-init-nov13-'+commit[:8],completeGame=False)
(upload/'release-input.json').write_text(json.dumps(receipt,indent=2)+'\n');(H/'release-input.json').write_text(json.dumps(receipt,indent=2)+'\n')
(H/'release-published.json').write_bytes((P/'release-published.json').read_bytes())
old=R/'artifacts/th14/player-initialization-oracle-nov13'
prepare=(old/'prepare-arch.sh').read_text()
prepare=prepare.replace('/home/i/Code/th14-release/player-init-nov13-b8e36ef2',receipt['remoteRelease'])
prepare=prepare.replace('old=/home/i/Code/th14-release/feedback-nov13-84b8741a','old=/home/i/Code/th14-release/player-init-nov13-b8e36ef2')
prepare=prepare.replace('b8e36ef27d96238352f5edaf9b368ca23394ceb3',commit)
prepare=prepare.replace('2eeb8db4b6f2ef337656d4d979c60abfaca579be',info['frontendHead'])
prepare=prepare.replace('--th14-ogg="$old/content-vorbis"','--th14-ogg=/home/i/Code/th14-release/feedback-nov13-84b8741a/content-vorbis')
(H/'prepare-arch.sh').write_text(prepare,encoding='utf8',newline='\n')
activate=(old/'activate-arch.sh').read_text()
activate=activate.replace('/home/i/Code/th14-release/player-init-nov13-b8e36ef2',receipt['remoteRelease'])
activate=activate.replace('hosted-before-b8e36ef2','hosted-before-59a8cc4c')
activate=activate.replace('b8e36ef27d96238352f5edaf9b368ca23394ceb3',commit)
activate=activate.replace('2eeb8db4b6f2ef337656d4d979c60abfaca579be',info['frontendHead'])
activate=activate.replace(old_wasm,sha(wasm))
(H/'activate-arch.sh').write_text(activate,encoding='utf8',newline='\n')
(H/'verify-public-compressed.py').write_bytes((old/'verify-public-compressed.py').read_bytes())
print(json.dumps(dict(sourceCommit=commit,changedRuntimeFiles=len(files),bytes=sum(len(b)for b in files.values()),remoteFreeBytes=info['freeBytes'],remoteRelease=receipt['remoteRelease'])))
