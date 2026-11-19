"""Native ending flag publication and Result clear-marker consumer.

Actual 2c914 store and 70c04..70c22 consumer, coupled to the shared JS alias.
Native game initializer reset is modeled as its known zero byte input. Other
Result fields/qualification, task registration and rendering are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 source='shared/th06nc/game-clear-flag.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="import{bindGameClearFlag,markEndingGameClear}from'./shared/th06nc/game-clear-flag.mjs';const cases=[];for(const flag of [0,1,2,255])for(const stage of [1,5,6,7]){const e=bindGameClearFlag({messageTaskSuspended:flag}),initial=e.cleared;e.cleared=false;const reset={flag:e.messageTaskSuspended,cleared:e.cleared};markEndingGameClear(e);cases.push({flag,stage,initial,reset,ending:{flag:e.messageTaskSuspended,cleared:e.cleared}});}console.log(JSON.stringify(cases));";cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 for c in cases:
  m.mem_write(0x1404f27b3,bytes([c['flag']]));m.mem_write(0x1404f1e84,struct.pack('<i',c['stage']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R15,1);m.reg_write(UC_X86_REG_RCX,99);m.emu_start(0x140070c04,0x140070c22,count=10);marker=m.mem_read(n.owner+0x9e6f,1)[0];assert marker==(99 if c['initial']else c['stage']);assert c['reset']==dict(flag=False,cleared=False);m.mem_write(0x1404f27b3,b'\0');m.emu_start(0x14002c914,0x14002c91b,count=2);assert m.mem_read(0x1404f27b3,1)[0]==c['ending']['flag']==c['ending']['cleared']==1;digest.update(bytes([marker]))
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha;report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-game-clear-flag-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
