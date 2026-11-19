"""Title replay list 48b45..48c48 and stage navigation 48eef..48f90.

Actual native helper 4d1f0 and sound queues execute. Compares complete title
owner bytes in these slices. Headers are controlled; confirmation, loading,
animation/common tail, drawing and physical input are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

def main():
 names=['title-replay-navigation','title-navigation','sound-queue'];hashes={f'shared/th06nc/{p}.mjs':hashlib.sha256((ROOT/f'shared/th06nc/{p}.mjs').read_bytes()).hexdigest()for p in names}
 script="""
import{navigateTitleReplayList,navigateTitleReplayStage}from'./shared/th06nc/title-replay-navigation.mjs';const cases=[];
for(const kind of ['list','stage'])for(const count of kind==='list'?[0,1,14,15,16,29,30,31,60]:[1,21,64,85,127])for(const selection of kind==='list'?[...new Set([0,Math.max(0,count-1),Math.min(14,Math.max(0,count-1))])]:[0,1,3,6])for(const frame of [39,40])for(const held of [0,16,32,48,64,128,192,80,160,240])for(const previous of [0,held])for(const repeat of [0,1])for(const disabled of [false,true]){
const initial={state:kind==='list'?18:20,frame,selection,replaySelection:2,pulse:31,totalFrame:99},keys={held,previous,repeat},sound={disabled,slots:[-1,-1,-1]},stageOffsets=Array.from({length:7},(_,i)=>count&(1<<i)?120+i*32:null),result=kind==='list'?navigateTitleReplayList(initial,count,keys,sound):navigateTitleReplayStage(initial,stageOffsets,keys,sound);cases.push({kind,count,initial,keys,disabled,stageOffsets,result});}console.log(JSON.stringify(cases));
 """
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 def hook(m,a,size,u):
  if a in [0x140048c48,0x140048f90,0x14004cbe6,0x140048e77]:m.emu_stop()
 m.hook_add(UC_HOOK_CODE,hook)
 for index,c in enumerate(cases):
  raw=bytearray(0x20000);fields=[(0x168b0,'state'),(0x9638,'frame'),(0x28,'selection'),(0x963c,'replaySelection'),(0x30,'pulse'),(0x2c,'totalFrame')]
  for offset,key in fields:struct.pack_into('<i',raw,offset,c['initial'][key])
  struct.pack_into('<i',raw,0x168b4,c['count'])
  if c['kind']=='stage':
   for i,p in enumerate(c['stageOffsets']):struct.pack_into('<Q',raw,0x7a18+2*120+64+i*8,0 if p is None else p)
  m.mem_write(n.owner,bytes(raw));m.mem_write(0x140a6ec60,struct.pack('<2I',c['keys']['held'],c['keys']['previous']));m.mem_write(0x140a6ec48,struct.pack('<i',c['keys']['repeat']));m.mem_write(0x140509670,struct.pack('<3i',-1,-1,-1));m.mem_write(0x140509694,bytes([c['disabled']]))
  for reg,value in [(UC_X86_REG_RSI,n.owner),(UC_X86_REG_RBP,0),(UC_X86_REG_RSP,n.stack+0x8000),(UC_X86_REG_RBX,4),(UC_X86_REG_R13,11),(UC_X86_REG_R15,0x100),(UC_X86_REG_RDI,8)]:m.reg_write(reg,value)
  m.emu_start(0x140048b45 if c['kind']=='list'else 0x140048eef,n.stack,count=100000)
  expected=bytearray(raw)
  for offset,key in fields:struct.pack_into('<i',expected,offset,c['result']['state'][key])
  actual=bytes(m.mem_read(n.owner,len(raw)));assert actual==expected,(index,c,[hex(i)for i,(a,b)in enumerate(zip(actual,expected))if a!=b][:10]);assert list(struct.unpack('<3i',m.mem_read(0x140509670,12)))==c['result']['soundSlots'],(index,'sound');digest.update(actual)
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-replay-navigation-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'stateSha256':report['stateSha256']}))

if __name__=='__main__':main()
