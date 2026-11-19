"""Actual state2 gate47f6a..47fa2. Acceptance prefix/draw/audio excluded."""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 source='shared/th06nc/title-selection-return.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""import{titlePromptReady}from'./shared/th06nc/title-selection-return.mjs';const cases=[];for(const mainFastEntry of [false,true])for(const frame of [-1,0,29,30,31,2147483647])for(let a=0;a<32;a++)for(let b=0;b<32;b++){const state={mainFastEntry,frame},held=(a<<8)|0x8001,previous=(b<<8)|0x2040;cases.push({state,held,previous,ready:titlePromptReady(state,{held,previous})});}console.log(JSON.stringify(cases));"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m
 def stop(m,a,size,u):m.emu_stop()
 for a in [0x14004cbe6,0x140047fa2,0x14004801b]:m.hook_add(UC_HOOK_CODE,stop,begin=a,end=a)
 for c in cases:
  m.mem_write(n.owner+0x16875,bytes([int(c['state']['mainFastEntry'])]));m.mem_write(n.owner+0x9638,struct.pack('<i',c['state']['frame']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_EDX,c['held']);m.reg_write(UC_X86_REG_R8D,c['previous']);m.emu_start(0x140047f6a,n.stack,count=100);assert (m.reg_read(UC_X86_REG_RIP)!=0x14004cbe6)==c['ready'],c
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(cases),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-prompt-gate-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(cases))))
if __name__=='__main__':main()
