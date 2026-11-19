"""Structural ECL life/spell metadata walk 21dc0 and query wrapper 21fb0.

All seven programs/five difficulty masks, mid-sub starts, excluded callbacks,
depth-8/9 boundary, sentinel/invalid starts. Result, metadata and full visited
set compared. Runtime control flow/gauge drawing/GPU excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
    source='shared/th06nc/ecl-life-query.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    script="""
import{readFileSync}from'node:fs';import{createHash}from'node:crypto';import{readEcl}from'./shared/th06nc/ecl.mjs';import{scanEclLife,queryEclLife}from'./shared/th06nc/ecl-life-query.mjs';const programs=[];for(let stage=1;stage<=7;stage++){const file='ecldata'+stage+'.ecl',program=readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/'+file)),cases=[];function run(index,difficulty,variant){const sub=program.subroutines[index],visited=new Uint8Array(1024),callback=sub?.instructions.find(i=>i.opcode===114),exclude=variant===1&&callback?new DataView(callback.args.buffer,callback.args.byteOffset,callback.args.byteLength).getInt32(0,true):variant===4?index:-1;if(exclude>=0&&exclude<1024)visited[exclude]=1;const startOffset=variant===1&&sub?sub.instructions[Math.floor(sub.instructions.length/2)]?.offset??sub.end-12:variant===5&&sub?sub.end-12:null,depth=variant===2?8:variant===3?9:0,metadata={containsSpell:false,nextThreshold:-1,nextSubroutine:-1},result=scanEclLife(program,index,{difficulty,depth,startOffset,visited,metadata});cases.push({index,difficulty,variant,exclude,startOffset,depth,foundLife:result.foundLife,metadata:result.metadata,wrapperMetadata:depth===0?queryEclLife(program,index,{difficulty,startOffset,excludeSubroutine:exclude}):null,visitedSha256:createHash('sha256').update(result.visited).digest('hex')});}for(let index=0;index<program.subroutines.length;index++)for(let difficulty=0;difficulty<5;difficulty++)for(let variant=0;variant<6;variant++)run(index,difficulty,variant);for(const index of [-1,program.subroutines.length,1024])run(index,1,0);programs.push({file,subroutines:program.subroutines.length,cases});}console.log(JSON.stringify(programs));
"""
    programs=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();checked=0;wrapperChecked=0
    def hook(m,a,size,u):
        if a==0x1402bdee2:m.mem_write(m.reg_read(UC_X86_REG_RCX),bytes([m.reg_read(UC_X86_REG_RDX)&255])*m.reg_read(UC_X86_REG_R8))
        sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
    for a in [0x1402bdee2,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
    for p in programs:
        raw=(ROOT/'runtimes/th06nc/artifacts/scripts/th06ST.dat'/p['file']).read_bytes();m.mem_write(n.assets,raw)
        for index,c in enumerate(p['cases']):
            visited=bytearray(1024)
            if 0<=c['exclude']<1024:visited[c['exclude']]=1
            m.mem_write(n.owner,bytes(visited));m.mem_write(n.vm,struct.pack('<B3xii',0,-1,-1));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<QQ',n.vm,0 if c['startOffset']is None else n.assets+c['startOffset']));m.mem_write(0x1404f27c0,struct.pack('<i',c['difficulty']));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.assets);m.reg_write(UC_X86_REG_EDX,c['index']&0xffffffff);m.reg_write(UC_X86_REG_R8D,c['depth']);m.reg_write(UC_X86_REG_R9,n.owner);m.emu_start(0x140021dc0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000
            actual=bytes(m.mem_read(n.vm,12));result=c['metadata'];expected=struct.pack('<B3xii',result['containsSpell'],result['nextThreshold'],result['nextSubroutine']);assert actual==expected,(p['file'],index,'metadata',actual.hex(),expected.hex());assert bool(m.reg_read(UC_X86_REG_RAX)&255)==c['foundLife'],(p['file'],index,'result');visited=bytes(m.mem_read(n.owner,1024));assert hashlib.sha256(visited).hexdigest()==c['visitedSha256'],(p['file'],index,'visited');digest.update(actual);digest.update(visited);checked+=1
            if c['wrapperMetadata']is not None:
                m.mem_write(0x140a6eb78,struct.pack('<Q',n.assets));m.mem_write(n.vm,bytes([0xa5])*12);sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.mem_write(sp+0x28,struct.pack('<i',c['exclude']));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RDX,n.vm);m.reg_write(UC_X86_REG_R8D,c['index']&0xffffffff);m.reg_write(UC_X86_REG_R9,0 if c['startOffset']is None else n.assets+c['startOffset']);m.emu_start(0x140021fb0,n.stack+0xf000,count=1000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;result=c['wrapperMetadata'];expected=struct.pack('<B3xii',result['containsSpell'],result['nextThreshold'],result['nextSubroutine']);expected=expected[:1]+bytes([0xa5])*3+expected[4:];actual=bytes(m.mem_read(n.vm,12));assert actual==expected,(p['file'],index,'wrapper metadata',actual.hex(),expected.hex());assert hashlib.sha256(bytes(m.mem_read(sp-0x428,1024))).hexdigest()==c['visitedSha256'],(p['file'],index,'wrapper visited');digest.update(actual);wrapperChecked+=1
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,programs=len(programs),subroutines=sum(p['subroutines']for p in programs),queries=checked,wrapperQueries=wrapperChecked,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-ecl-life-query-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
