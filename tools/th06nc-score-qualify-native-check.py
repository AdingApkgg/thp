"""State-9 candidate/qualification body 70bab..70dca, actual ranked lists.

Candidate fields, previous name, first-ten gate, cursor and group interrupts.
One selected rank-head pointer is normalized to the port's external array.
Qualified cases also execute name input and compare the candidate alias.
Allocator/memset/achievement/config-save are services; label publication,
common ANM tick and UI are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    sources=['shared/th06nc/'+s+'.mjs'for s in ['score-qualify','score-tables','score-file','score-name-input','sound-queue']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};script="""
import{createHash}from'node:crypto';import{createDefaultScoreTables}from'./shared/th06nc/score-tables.mjs';import{qualifyResultScore}from'./shared/th06nc/score-qualify.mjs';import{advanceScoreNameInput}from'./shared/th06nc/score-name-input.mjs';const hex=b=>Buffer.from(b).toString('hex'),sha=b=>createHash('sha256').update(b).digest('hex'),defaults=createDefaultScoreTables(),cases=[];for(const character of [0,1])for(const shot of [0,1])for(const difficulty of [0,1,2,3,4])for(const mode of [0,1])for(const score of [0n,99999n,100000n,100001n,1000000n,0xffffffffffffffffn])for(const cleared of [false,true])for(const name of ['', 'A  ','12345678','东方']){const bytes=new Uint8Array(0xbb48),v=new DataView(bytes.buffer);v.setInt32(4,character,true);v.setInt32(0xa8,difficulty,true);v.setInt32(0xac,mode,true);v.setInt32(0x9e94,9,true);v.setInt32(0x9e7c,1,true);bytes.set(Buffer.from('PREVIOUS\\0'),0x9e88);for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,85,true);const table=defaults.get(`${mode}/${difficulty}/${character*2+shot}`).map(r=>r.slice()),before=table.map(hex),result=qualifyResultScore({bytes,v},table,{shot,score,stageIndex:3,cleared,previousName:name});const c={character,shot,difficulty,mode,score:String(score),cleared,name:[...new TextEncoder().encode(name)],before,rank:result.rank,qualifies:result.qualifies,table:table.map(hex),sha256:sha(bytes)};if(result.qualifies){const soundSlots=[-1,-1,-1];v.setInt32(0x4450,30,true);v.setInt32(0,0,true);advanceScoreNameInput({bytes,v},{held:256,soundSlots});v.setInt32(0,95,true);advanceScoreNameInput({bytes,v},{held:256,soundSlots});c.edited={sha256:sha(bytes),table:table.map(hex),soundSlots};}cases.push(c);}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;cursor=n.vm+0x4000;digest=hashlib.sha256();qualified=0;inNameInput=False;m.mem_write(0x1402c0370,struct.pack('<Q',n.vm+0x9000))
    def hook(m,a,size,u):
        nonlocal cursor
        if a==0x140070dca:
            if not inNameInput:m.emu_stop()
            return
        if a==0x140072743:m.emu_stop();return
        sp=m.reg_read(UC_X86_REG_RSP)
        if a==n.vm+0x9000:
            size=m.reg_read(UC_X86_REG_RCX);out=cursor;cursor+=(size+15)&~15;assert cursor<n.vm+0x9000;m.mem_write(out,bytes(size));m.reg_write(UC_X86_REG_RAX,out)
        elif a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8));m.reg_write(UC_X86_REG_RAX,m.reg_read(UC_X86_REG_RCX))
        m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [n.vm+0x9000,0x1402bdee2,0x140070dca,0x140072743,0x140067cb0,0x14007bc00]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for index,c in enumerate(cases):
        inNameInput=False
        raw=bytearray(0xbb48);struct.pack_into('<i',raw,4,c['character']);struct.pack_into('<2i',raw,0xa8,c['difficulty'],c['mode']);struct.pack_into('<i',raw,0x9e94,9);struct.pack_into('<i',raw,0x9e7c,1);raw[0x9e88:0x9e91]=b'PREVIOUS\0'
        for i in range(38):struct.pack_into('<h',raw,0xb0+i*288+0x8a,85)
        m.mem_write(n.owner,bytes(raw));headOffset=0x4458+((c['mode']*5+c['difficulty'])*4+c['character']*2+c['shot'])*24;head=n.owner+headOffset;cursor=n.vm+0x4000
        for i,r in enumerate(c['before']):
            ptr=n.assets+i*64;m.mem_write(ptr,bytes.fromhex(r));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,head);m.reg_write(UC_X86_REG_RDX,ptr);m.emu_start(0x14006cbc0,n.stack+0xf000,count=100000)
        m.mem_write(0x1404f1e81,bytes([c['shot']]));m.mem_write(0x1404f2798,struct.pack('<Q',int(c['score'])));m.mem_write(0x1404f27b3,bytes([c['cleared']]));m.mem_write(0x1404f1e84,b'\3');m.mem_write(0x140c21dc4,bytes(128));m.mem_write(0x140c21dc4,bytes(c['name']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,1);m.reg_write(UC_X86_REG_RCX,c['shot']);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140070bab,n.stack+0xf000,count=100000);actual=bytearray(m.mem_read(n.owner,0xbb48));actual[headOffset:headOffset+24]=bytes(24);assert hashlib.sha256(actual).hexdigest()==c['sha256'],(index,'owner');rows=[];node=struct.unpack('<Q',m.mem_read(head+16,8))[0]
        while node:
            ptr=struct.unpack('<Q',m.mem_read(node,8))[0];rows.append(bytes(m.mem_read(ptr,36)).hex());node=struct.unpack('<Q',m.mem_read(node+16,8))[0]
        assert rows==c['table'],(index,'rank order');assert (m.reg_read(UC_X86_REG_RIP)==0x140070dca)==c['qualifies'],(index,'qualification');qualified+=int(c['qualifies']);digest.update(actual)
        if c['qualifies']:
            inNameInput=True;m.mem_write(n.owner+0x4450,struct.pack('<i',30));m.mem_write(0x140a6ec60,struct.pack('<2I',256,0));m.mem_write(0x140a6ec48,bytes(4));m.mem_write(0x140509694,b'\0');m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1))
            for selection in [0,95]:
                m.mem_write(n.owner,struct.pack('<i',selection));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R12,4);m.reg_write(UC_X86_REG_R15,1);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140070dca,n.stack+0xf000,count=100000)
            actual=bytearray(m.mem_read(n.owner,0xbb48));actual[headOffset:headOffset+24]=bytes(24);assert hashlib.sha256(actual).hexdigest()==c['edited']['sha256'],(index,'edited owner');rows=[];node=struct.unpack('<Q',m.mem_read(head+16,8))[0]
            while node:
                ptr=struct.unpack('<Q',m.mem_read(node,8))[0];rows.append(bytes(m.mem_read(ptr,36)).hex());node=struct.unpack('<Q',m.mem_read(node+16,8))[0]
            assert rows==c['edited']['table'],(index,'edited candidate alias');assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['edited']['soundSlots'],(index,'edited sounds');digest.update(actual)
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(cases),qualified=qualified,editedCandidates=qualified,rejected=len(cases)-qualified,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-score-qualify-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
