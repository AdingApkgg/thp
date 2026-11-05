"""Add output-only slot snapshots to the frozen strict Supervisor driver."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
H=R/'artifacts/th14/shot-lifetime-native-nov05'
parent=R/'artifacts/th14/supervisor-pass-rng-nov05/comparison-driver-v6/driver.mjs'
raw=parent.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='d9247f1c8889063065dfd3c8a895b9ea2e504f29902fe58f364e23e5970ce67c'
s=raw.decode();changes=[]


def replace(before,after):
    global s
    assert s.count(before)==1,(before,s.count(before))
    s=s.replace(before,after);changes.append((before,after))


replace("'tools/th14-supervisor-rng-read-evidence-nov05.py'","'tools/th14-shot-lifetime-register-evidence-nov05.py'")
replace('function compare(index){', '''const lifetimeSnapshots=[];
function retainLifetime(index){
 if(c.shot_lifetime_meta(0)!==index+1)return;
 const meta=Array.from({length:6},(_,word)=>c.shot_lifetime_meta(word)>>>0);
 assert.equal(meta[3],96);assert.equal(meta[4],256);assert(lifetimeSnapshots.length<64);
 const data=Buffer.from(new Uint8Array(c.memory.buffer,c.shot_lifetime_data(),256*96*4));
 const name='shot-lifetime-'+(index+1)+'.u32';write(resolve(out,name),data,{flag:'wx'});
 lifetimeSnapshots.push({callback:meta[0],stage:meta[1],stageFrame:meta[2],stride:96,slots:256,file:name,bytes:data.length,sha256:sha(data)});
 write(resolve(out,'shot-lifetime-index.json'),JSON.stringify({readOnly:true,originalValuesProvidedToEngine:false,snapshots:lifetimeSnapshots})+'\\n');
}
function compare(index){''')
replace('rows.push(...row);for(let k=0;k<32;k++){','rows.push(...row);retainLifetime(index);for(let k=0;k<32;k++){')
replace('initialCreationCount=c.observed_creation_count();compare(0);',
        'initialCreationCount=c.observed_creation_count();assert.equal(c.shot_lifetime_install(1),1);compare(0);')
# Reversing exactly these edits must restore every byte of the strict parent.
restored=s
for before,after in reversed(changes):
    assert restored.count(after)==1;restored=restored.replace(after,before)
assert restored.encode()==raw
out=H/'comparison-driver-v2';assert not out.exists();out.mkdir()
path=out/'driver.mjs';path.write_text(s,encoding='utf8',newline='\n')
off=s.replace('c.shot_lifetime_install(1)','c.shot_lifetime_install(0)')
assert off!=s
(out/'driver-off.mjs').write_text(off,encoding='utf8',newline='\n')
subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(path)],check=True,capture_output=True,timeout=30)
report=dict(prepared=True,parentStrictDriverSha256=sha(raw),driverSha256=sha(path.read_bytes()),
    disabledDriverSha256=sha((out/'driver-off.mjs').read_bytes()),
    onlyOutputProbeAndDeclaredObserverProvenanceChanged=True,allOriginalComparisonsAndFinalGatesByteIdentical=True,
    originalRngOrGameStateSuppliedToEngine=False,ordinaryIndependentTimingAccepted=False,
    toolSha256=sha(Path(__file__).read_bytes()),completeGame=False)
(out/'prepared.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
