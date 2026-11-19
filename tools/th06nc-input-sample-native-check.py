"""Keyboard-mask12d69..13019 and actual controller composer127d0.
Full returned mask, uint16 shared shot/focus counter and raw secret bitfield.
Keyboard layout lookup/physical sampling supplied; controller API supplies
26-byte native packets and status. CRT atan2 receives identical float32 angle,
not a native/libm equivalence claim. No browser/hardware/lifecycle claim.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/input-sample.mjs','shared/th06nc/config-file.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};data=json.loads(subprocess.check_output(['node','tools/th06nc-input-sample-cases.mjs'],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256();m.mem_write(0x140c21e60,bytes(range(256)))
 for index,c in enumerate(data['keyboard']):
  m.mem_write(n.owner,bytes.fromhex(c['raw']));m.reg_write(UC_X86_REG_R14,n.owner);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x140012d69,0x140013019,count=1000);actual=m.reg_read(UC_X86_REG_ECX);assert actual==c['mask'],(index,'keyboard',hex(actual),hex(c['mask']));digest.update(struct.pack('<I',actual))
 current=None
 def hook(m,a,size,u):
  if a==0x1400a9fd0:
   if current['connected']:m.mem_write(m.reg_read(UC_X86_REG_RDX),bytes.fromhex(current['packet']));m.reg_write(UC_X86_REG_EAX,0)
   else:m.reg_write(UC_X86_REG_EAX,0xffffffff)
  elif a==0x1402be065:m.reg_write(UC_X86_REG_XMM0,struct.unpack('<I',struct.pack('<f',current['angle']))[0])
  sp=m.reg_read(UC_X86_REG_RSP);m.reg_write(UC_X86_REG_RIP,struct.unpack('<Q',m.mem_read(sp,8))[0]);m.reg_write(UC_X86_REG_RSP,sp+8)
 for a in[0x1400a9fd0,0x1402be065,0x1402bcf20]:m.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 for index,current in enumerate(data['controller']):
  c=current;m.mem_write(0x140c21da4,bytes.fromhex(c['config']));m.mem_write(0x140a6eb50,struct.pack('<H',c['initial']['focusClock']));m.mem_write(0x140c21e58,struct.pack('<I',c['initial']['secretMask']));m.mem_write(0x140c21d9c,struct.pack('<i',c['gameState']));m.mem_write(0x1404f27b0,bytes([c['paused'],c['gameOver']]));m.mem_write(0x1404f27b6,bytes([c['spellResultVisible']]));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_ECX,c['keyboardMask']);m.emu_start(0x1400127d0,n.stack+0xf000,count=10000);actual=m.reg_read(UC_X86_REG_EAX);state=dict(focusClock=struct.unpack('<H',m.mem_read(0x140a6eb50,2))[0],secretMask=struct.unpack('<I',m.mem_read(0x140c21e58,4))[0]);assert actual==c['mask'],(index,'controller',hex(actual),hex(c['mask']),c);assert state==c['state'],(index,'state',state,c);digest.update(struct.pack('<IHI',actual,state['focusClock'],state['secretMask']))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,keyboardCases=len(data['keyboard']),controllerCases=len(data['controller']),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-input-sample-native-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['passed','keyboardCases','controllerCases','stateSha256']}))
if __name__=='__main__':main()
