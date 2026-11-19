"""Actual Result entry fade block 73d75..73dcf, excluding Practice17.

Full 56-byte retained fade comparison for ordinary and standalone entry,
including null fade, mode gates, existing color/alpha and unrelated bytes.
Resource/font initialization and task registration remain excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/result-entry-fade.mjs','shared/th06nc/fade.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{NativeFade}from'./shared/th06nc/fade.mjs';import{initializeResultEntryFade}from'./shared/th06nc/result-entry-fade.mjs';const cases=[];
for(const state of [0,2,9,10,12,13,15])for(const standalone of [false,true])for(const mode of [-1,0,1,2,3,4])for(const color of [0,0xffffff,0xaabbccdd])for(const alpha of [0,127,255])for(const present of [false,true]){const fade=new NativeFade();fade.state.set(Uint8Array.from({length:56},(_,i)=>(i*7+5)&255));fade.v.setInt32(0x34,mode,true);fade.v.setUint32(0x20,color,true);fade.v.setInt32(0x28,alpha,true);const before=[...fade.state];initializeResultEntryFade(present?fade:null,{state,standalone});cases.push({state,standalone,mode,color,alpha,present,before,after:[...fade.state]});}console.log(JSON.stringify(cases));
"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for index,c in enumerate(cases):
  m.mem_write(n.owner+0x9e9a,bytes([c['standalone']]));m.mem_write(n.vm,bytes(c['before']));m.mem_write(0x140c22158,struct.pack('<Q',n.vm if c['present']else 0))
  for reg,value in [(UC_X86_REG_RCX,n.owner),(UC_X86_REG_R15,n.owner),(UC_X86_REG_R13,0),(UC_X86_REG_RAX,c['state'])]:m.reg_write(reg,value)
  m.emu_start(0x140073d75,0x140073dcf,count=100);assert bytes(m.mem_read(n.vm,56))==bytes(c['after']),(index,c);digest.update(m.mem_read(n.vm,56))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
 report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-result-entry-fade-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,cases=len(cases),stateSha256=digest.hexdigest())))

if __name__=='__main__':main()
