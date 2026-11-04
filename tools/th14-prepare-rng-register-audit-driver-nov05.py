"""Add output-only RNG value audits to the retained observed-clock driver."""
from pathlib import Path
import hashlib, json

R=Path(__file__).resolve().parents[1]
P=R/'tools/th14-compare-native-hard-rep-split-v4-nov05.mjs'
D=R/'tools/th14-compare-native-rng-register-audit-nov05.mjs'
SHA=lambda b:hashlib.sha256(b).hexdigest()
raw=P.read_bytes();assert SHA(raw)=='1af7e21434fa1245980cbe7d020d238344dba213d4e99afef9b111280d104a61'
s=P.read_text()
def replace(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
replace("'partial-scene-copy-mode']);", "'partial-scene-copy-mode','rng-audit-first','rng-audit-last']);")
replace("const out=resolve(root,options.get('output')),scope=", "const auditFirst=Number(options.get('rng-audit-first')??0),auditLast=Number(options.get('rng-audit-last')??0);assert(Number.isInteger(auditFirst)&&Number.isInteger(auditLast)&&auditFirst>=0&&auditLast>=auditFirst&&!!auditFirst===!!auditLast);\nconst out=resolve(root,options.get('output')),scope=")
s=s.replace('c.menu_tick(', 'c.rng_audit_menu_tick(').replace('c.draw()', 'c.rng_audit_draw()')
replace('assert.equal(c.perspective_rep_split_capture_install(),1);',
    'assert.equal(c.perspective_rep_split_capture_install(),1);if(auditFirst)assert.equal(c.rng_audit_install(auditFirst,auditLast),1);')
anchor="write(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\\n',{flag:'wx'});"
replace(anchor,"""const auditMeta=Array.from({length:5},(_,i)=>c.rng_audit_meta(i)>>>0);assert.equal(auditMeta[3],0,'RNG audit capacity exceeded');
const auditBytes=Buffer.alloc(auditMeta[2]*16*4);
for(let row=0;row<auditMeta[2];row++)for(let word=0;word<16;word++)auditBytes.writeUInt32LE(c.rng_audit_word(row,word)>>>0,(row*16+word)*4);
write(resolve(out,'rng-register-audit.u32'),auditBytes,{flag:'wx'});
report.rngRegisterAudit={enabled:!!auditFirst,meta:auditMeta,fields:['callback','stage','point','rngRole','seed','calls','file','script','vmFlags2','pendingStage','loadPhase','initializing','preparingScene','spawnDepth','clockLow','clockHigh'],
 outputSha256:sha(auditBytes),originalValuesProvidedToEngine:false,ordinaryIndependentTimingAccepted:false};
"""+anchor)
assert not D.exists();D.write_text(s,encoding='utf8',newline='\n')
out=R/'artifacts/th14/script-rng-read-generation-nov05/portable-audit-driver-prepared.json';assert not out.exists()
out.write_text(json.dumps(dict(driver=D.relative_to(R).as_posix(),driverSha256=SHA(D.read_bytes()),parentDriverSha256=SHA(raw),outputOnlyAuditAdded=True,
    additionalNativeRngValuesProvidedToEngine=False,readOrderSchedulerChanged=False,completeGame=False,toolSha256=SHA(Path(__file__).read_bytes())),indent=2)+'\n')
print(json.dumps(dict(prepared=True,driverSha256=SHA(D.read_bytes()),readOrderSchedulerChanged=False)))
