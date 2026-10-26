"""Private actual Continue music command queue plus restore; silent COM."""
from pathlib import Path
import hashlib,json,struct,sys
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];tool=R/'tools/th14-music-subframe-native-oct26.py';assert hashlib.sha256(tool.read_bytes()).hexdigest()=='6fe01cc3d493ba001639199946679a4ec857cc2718270b5d7314d375776b1bcb';source=tool.read_text();prefix=source[:source.index('\nrows=[]')];ns={'__file__':str(tool)};exec(compile(prefix,str(tool),'exec'),ns);O=ns['O'];assert not any(O.iterdir()),'Use a fresh private output directory';m=ns['m'];put=ns['put'];get=ns['get'];controller=ns['controller'];reader=ns['reader'];stack=ns['stack'];base=ns['base'];registry=base+0x100000;saved=base+0x80000;observed=[];rows=[];sha=lambda b:hashlib.sha256(b).hexdigest()
def log_stub(*args):ns['ret'](0)
def restore_observe(*args):observed.append(dict(fileCursor=ns['file_cursor'],readerLoopReached=get(reader+0x9c),formatName=bytes(m.mem_read(get(reader+0x90),16)).split(b'\0')[0].decode(),queueKind=get(0x4f9f00)))
m.hook_add(UC_HOOK_CODE,log_stub,begin=0x482000,end=0x482000);m.hook_add(UC_HOOK_CODE,restore_observe,begin=0x481ee0,end=0x481ee0)
for prior in [0,128]:
 for track in range(18):
  for clock_ns in [0,1,11000,22675,22676,1250000000]:
   seconds=clock_ns/1e9
   ns['heap']=ns['heap_base'];ns['play_cursor']=0;observed.clear()
   for name in ['buffers','events','reads','created','unlocked']:ns[name].clear()
   m.mem_write(registry,ns['format_bytes']);m.mem_write(saved,bytes(0x500));m.mem_write(saved+0x2dc,struct.pack('<d',seconds));entry=ns['format_bytes'][track*52:(track+1)*52];filename=entry[:16].split(b'\0')[0];m.mem_write(saved+0x2e4,filename+b'\0');m.mem_write(0x4f9f00,bytes(0x10c*32));m.mem_write(0x4f95dc,bytes(0x720));m.mem_write(0x4d9152,b'\0');put(0x4d916c,0);put(0x4f7b64,ns['device_holder']);put(0x4f94d8,registry);m.mem_write(0x4f9e00,b'th128_08.wav\0')
   m.mem_write(controller,bytes(0xb0));m.mem_write(reader,bytes(0xa0));put(controller+4,ns['holder']);put(ns['holder'],ns['old_buffer']);put(ns['old_buffer'],ns['vtable']);ns['buffers'][ns['old_buffer']]=(ns['allocate'](705600),705600);put(controller+8,705600);put(controller+0xc,reader);put(controller+0x10,1);put(controller+0x24,1);m.mem_write(controller+0x58,ns['descriptor']);put(controller+0x7c,ns['device_holder']);put(controller+0x94,88200);put(controller+0x98,0x1234);put(reader+0x90,registry+17*52);put(reader+0x8c,7);put(0x4fd180,controller)
   put(stack,base);put(stack+4,ns['old_buffer']);put(stack+8,0);put(stack+12,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,controller);m.emu_start(0x480cf0,base,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==base
   for step in range(prior):
    ns['play_cursor']=((step+1)*88200)%705600;put(stack,base);put(stack+4,0);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_ECX,controller);m.emu_start(0x481620,base,count=5000000);assert m.reg_read(UC_X86_REG_EIP)==base
   before=dict(fileCursor=ns['file_cursor'],readerLoopReached=get(reader+0x9c));
   for name in ['events','reads','created','unlocked']:ns[name].clear()
   put(stack,base);m.reg_write(UC_X86_REG_ESP,stack);m.reg_write(UC_X86_REG_EDI,saved);m.reg_write(UC_X86_REG_MXCSR,0x1f80);m.reg_write(UC_X86_REG_FPCW,0x37f);m.reg_write(UC_X86_REG_FPSW,0);m.reg_write(UC_X86_REG_FPTAG,0xffff)
   try:m.emu_start(0x44aef0,0x44af2c,count=5000000)
   except Exception as error:raise RuntimeError(hex(m.reg_read(UC_X86_REG_EIP)))from error
   assert m.reg_read(UC_X86_REG_EIP)==0x44af2c and len(observed)==1 and observed[0]['formatName']==filename.decode() and observed[0]['readerLoopReached']==0 and get(0x4f9f00)==0
   pcm,size=ns['buffers'][get(get(controller+4))];raw=bytes(m.mem_read(pcm,size));assert sha(raw)==ns['unlocked'][-1]['sha256'];name=f'prior-{prior:03d}-track-{track:02d}-time-{clock_ns:010d}.s16';(O/name).write_bytes(raw[:4096]);rows.append(dict(priorResultRefills=prior,track=track,name=filename.decode(),restoreSeconds=seconds,clockNs=clock_ns,before=before,beforeRestore=observed[0],seeks=[e for e in ns['events']if e['kind']=='seek'],reads=ns['reads'][:],fills=ns['unlocked'][:],created=ns['created'][:],prefixFile=name,prefixSha256=sha(raw[:4096])))
ns['k'].CloseHandle(ns['file_handle']);report=dict(cases=len(rows),rows=rows,executableSha256=sha(ns['image'].data),baseHarnessSha256=sha(tool.read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),scope='Actual original44aef0..44af2c Continue music window, including44c070 withempty sound buffers,46ef90 queue,whole46e5e0 consumer,actual format lookup,481a60 resets,480a00 recreation,481880/480cf0 fill,481120 Play,final481ee0 restore. Controlled COM/QPC and actual readonly Windows file calls; original program bytes unmodified. Prior result song starts at th128_08 with0or128 notifications;18 restored names and6 exact nanosecond times. Excludes physical notification races between queue Play and finalrestore, hardware queue, remaining Continue player/HUD code and complete ordinary game.',audioDevicesOpened=0,audioPlayed=False,productionChanged=False,completeGame=False,nativeEquivalent=False);(O/'native.json').write_text(json.dumps(report,indent=2)+'\n')
