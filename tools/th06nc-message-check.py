"""Independent structural decode of all seven native message resources.

Checks original PKGL hashes, all aliased table entries, record times/opcodes,
argument bytes and malformed file boundaries; does not claim execution.
"""
import hashlib,json,struct,subprocess
from th06nc_native import ROOT

def main():
    source='shared/th06nc/message.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{readMessage}from'./shared/th06nc/message.mjs';const manifest=JSON.parse(readFileSync('artifacts/th06nc/messages.json')),files=manifest.map(f=>{const p=readMessage(readFileSync(f.path));return{name:f.name,offsets:p.offsets,scripts:p.uniqueScripts.map(s=>({...s,instructions:s.instructions.map(i=>({...i,args:Buffer.from(i.args).toString('hex')}))})),aliasIdentity:p.scripts.every((s,i)=>p.scripts.every((t,j)=>(p.offsets[i]===p.offsets[j])===(s===t)))};});const raw=readFileSync(manifest[0].path),last=files[0].scripts[0].instructions.at(-1).offset,malformed=[Buffer.alloc(0),Buffer.from([2,0,0,0,8,0,0,0]),Buffer.from([1,0,0,0,0,0,0,0]),Buffer.from([1,0,0,0,8,0,0,0]),raw.subarray(0,raw.length-1),Buffer.from(raw)],rejected=[];malformed.at(-1)[last+3]=255;for(const b of malformed){try{readMessage(b);rejected.push(false);}catch{rejected.push(true);}}console.log(JSON.stringify({files,rejected}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));manifest=json.loads((ROOT/'artifacts/th06nc/messages.json').read_bytes());digest=hashlib.sha256();ops={};commands=0;unique=0;aliases=0
    for f,actual in zip(manifest,data['files']):
        raw=(ROOT/f['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==f['sha256'];count=struct.unpack_from('<I',raw)[0];offsets=list(struct.unpack_from('<'+'I'*count,raw,4));scripts=[];starts=sorted(set(offsets));unique+=len(starts);aliases+=count-len(starts)
        for index,start in enumerate(starts):
            end=starts[index+1]if index+1<len(starts)else len(raw);p=start;records=[]
            while p<end:
                time,op,size=struct.unpack_from('<HBB',raw,p);records.append(dict(offset=p,time=time,opcode=op,length=4+size,args=raw[p+4:p+4+size].hex()));p+=4+size;ops[op]=ops.get(op,0)+1;commands+=1
            assert p==end;scripts.append(dict(offset=start,end=end,instructions=records))
        assert actual==dict(name=f['name'],offsets=offsets,scripts=scripts,aliasIdentity=True),f['name'];digest.update(raw)
    assert all(data['rejected']);assert set(ops)==set(range(15));assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,files=len(manifest),scriptIds=unique+aliases,uniqueScripts=unique,aliasedEntries=aliases,commands=commands,opcodes=ops,malformedRejected=len(data['rejected']),resourceSha256=digest.hexdigest(),sourceSha256={source:sha},passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-message-structure-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
