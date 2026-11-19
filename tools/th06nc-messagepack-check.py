"""Independent Python msgpack comparison for original localization/practice data.

Compares complete decoded trees, including every language string. This proves
resource decoding, not language selection, UI, spells or practice execution.
"""
import hashlib,json,subprocess
import msgpack
from th06nc_native import ROOT

def main():
    script="""
import{readFileSync}from'node:fs';import{readMessagePack}from'./shared/th06nc/messagepack.mjs';const names=['localization','spellpractice'];console.log(JSON.stringify(names.map(name=>({name,value:readMessagePack(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/'+name+'.msgpack'))}))));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));files=[]
    for c in cases:
        raw=(ROOT/'runtimes/th06nc/artifacts/scripts/th06IN.dat'/f"{c['name']}.msgpack").read_bytes();reference=msgpack.unpackb(raw,raw=False);assert reference==c['value'],c['name'];files.append(dict(name=c['name'],sha256=hashlib.sha256(raw).hexdigest(),decodedSha256=hashlib.sha256(json.dumps(reference,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()))
    localization=cases[0]['value'];report=dict(scope=__doc__,files=files,localizationKeys=len(localization),languageValues=sum(len(v)for v in localization.values()),practiceEntries=len(cases[1]['value']['entries']),sourceSha256=hashlib.sha256((ROOT/'shared/th06nc/messagepack.mjs').read_bytes()).hexdigest(),reference=f'Python msgpack {msgpack.__version__}',passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-messagepack-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
