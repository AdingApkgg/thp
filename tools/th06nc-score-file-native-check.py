"""Score.dat crypt/checksum and native decoded payload, 6ca60/74a3a.

Actual user's score.dat is read only; synthetic/bit-flipped containers also
execute the original codec. Allocation/copy/free are explicit host services.
Full record serialization, disk writes, result UI and persistence excluded.
"""
import hashlib,json,struct,subprocess
from pathlib import Path
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/score-file.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{readFileSync}from'node:fs';import{decodeScoreFile,encodeScoreFile,createScoreChunk,createScoreFile}from'./shared/th06nc/score-file.mjs';const hex=b=>Buffer.from(b).toString('hex'),cases=[],original=readFileSync('H:/Games/th/06nc/score.dat');let random=0x1234abcd;const byte=()=>{random^=random<<13;random^=random>>>17;random^=random<<5;return random&255;};
const documents=[createScoreFile()];for(const seed of [0,1,86,255])for(const size of [10,12,16,24,36,384,4096]){const d=createScoreFile();d.header[0]=byte();d.header[1]=seed;d.header[6]=byte();d.header[7]=byte();const raw=createScoreChunk('TEST',size);for(let i=9;i<size;i++)raw[i]=byte();d.records.push(raw);documents.push(d);}documents.push(decodeScoreFile(original));
for(const document of documents){const encoded=encodeScoreFile(document),decoded=decodeScoreFile(encoded),body=Buffer.concat(decoded.records),plain=new Uint8Array(encoded.length);plain.set(decoded.header);plain.set(body,decoded.header.length);cases.push({encoded:hex(encoded),plain:hex(plain),body:hex(body),accepted:true});const flipped=encoded.slice();flipped[encoded.length-1]^=1;let rejected=false;try{decodeScoreFile(flipped);}catch{rejected=true;}if(!rejected)throw Error('Corrupt fixture unexpectedly valid');cases.push({encoded:hex(flipped),accepted:false});}
if(Buffer.compare(original,encodeScoreFile(decodeScoreFile(original))))throw Error('Original bytes failed round trip');
const malformed=[];for(const size of [0,1,19,23]){let failed=false;try{decodeScoreFile(new Uint8Array(size));}catch{failed=true;}if(!failed)throw Error('Accepted truncated file');malformed.push(size);}console.log(JSON.stringify({cases,malformed,originalBytes:original.length,originalSha256:(await import('node:crypto')).createHash('sha256').update(original).digest('hex'),originalRecords:decodeScoreFile(original).records.length}));
"""
    data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;heap=0x75000000;m.mem_map(heap,0x400000);cursor=heap;digest=hashlib.sha256();encodedCount=0;accepted=0;rejected=0
    m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000));m.mem_write(0x1402c0378,struct.pack('<Q',n.vm+0x9010))
    def hook(m,a,size,u):
        nonlocal cursor
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:
            count=m.reg_read(UC_X86_REG_RCX);result=cursor;cursor+=(count+15)&~15;assert cursor<heap+0x400000;m.mem_write(result,bytes(count));m.reg_write(UC_X86_REG_RAX,result)
        elif a==0x1402bdee8:
            dst=m.reg_read(UC_X86_REG_RCX);m.mem_write(dst,bytes(m.mem_read(m.reg_read(UC_X86_REG_RDX),m.reg_read(UC_X86_REG_R8))));m.reg_write(UC_X86_REG_RAX,dst)
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [n.vm+0x9000,n.vm+0x9010,0x1402bdee8]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(data['cases']):
        raw=bytes.fromhex(c['encoded']);cursor=heap;m.mem_write(n.assets,raw);m.mem_write(0x140c22148,struct.pack('<Q',n.assets));m.mem_write(0x140c21f6c,struct.pack('<I',len(raw)));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.emu_start(0x14006ca60,n.stack+0xf000,count=3000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000,(index,'decoder stop');result=m.reg_read(UC_X86_REG_RAX)
        if not c['accepted']:assert result==0,(index,'corruption accepted');rejected+=1;continue
        assert result!=0,(index,'valid rejected');body=bytes.fromhex(c['body']);assert struct.unpack('<I',m.mem_read(result,4))[0]==24;assert struct.unpack('<I',m.mem_read(result+0x10,4))[0]==24+len(body);actual=bytes(m.mem_read(result+24,len(body)));assert actual==body,(index,'payload');digest.update(actual);accepted+=1
        plain=bytearray.fromhex(c['plain']);struct.pack_into('<H',plain,2,0);m.mem_write(n.owner,bytes(plain));m.reg_write(UC_X86_REG_RBP,n.owner);m.reg_write(UC_X86_REG_EBX,len(plain));m.reg_write(UC_X86_REG_RDI,len(plain));m.reg_write(UC_X86_REG_R8,4);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140074a3a,0x140074aa2,count=3000000);assert bytes(m.mem_read(n.owner,len(plain)))==raw,(index,'encoder bytes');digest.update(raw);encodedCount+=1
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,accepted=accepted,rejectedCorruption=rejected,encoded=encodedCount,strictTruncationCases=data['malformed'],originalFileBytes=data['originalBytes'],originalFileSha256=data['originalSha256'],originalRecords=data['originalRecords'],stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-file-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
