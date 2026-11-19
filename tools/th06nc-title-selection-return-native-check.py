"""Actual selection return decision, cold/warm-title helper and state-2 acceptance prefix, including full fade owner.

Real base title ANMs and backdrop helper execute. Complete VM/control bytes and
relevant scalar fields compare. Resource reload/cache, main input processing,
application task graph, UI drawing and audible output are excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 sources=['shared/th06nc/title-selection-return.mjs','shared/th06nc/title-backdrop.mjs'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 script="""
import{NativeFade}from'./shared/th06nc/fade.mjs';import{readFileSync}from'node:fs';import{readAnm}from'./shared/th06nc/anm.mjs';import{TitleAnimations}from'./shared/th06nc/title-animations.mjs';import{titleResources}from'./shared/th06nc/title-layout.mjs';import{TitleBackdrop}from'./shared/th06nc/title-backdrop.mjs';import{advanceSelectionReturn,warmTitleMain,finishWarmTitleMain}from'./shared/th06nc/title-selection-return.mjs';const resources=new Map(titleResources.map(r=>[r.file,readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/th06TL.dat/'+r.file))])),snap=g=>[...g.slots].map(([offset,vm])=>({offset,file:[...resources].find(([n,r])=>r===vm.resource)?.[0],state:Buffer.from(vm.state).toString('hex')})),cases=[],decisions=[];
for(const frame of [-1,0,29,30,31,2147483647]){const initial={state:10,frame,selection:2};decisions.push({initial,expected:advanceSelectionReturn(initial)});}for(const priorTween of [0,17])for(const fadeMode of [0,1,2,3])for(const startupOverlay of [false,true])for(const selection of [0,1,2,3,9])for(const prior of [0,20,60]){const fade=new NativeFade();fade.request(0x112233,100,fadeMode);fade.v.setInt32(0x28,87,true);const fadeBefore=Buffer.from(fade.state).toString('hex');const group=new TitleAnimations(resources),backdrop=new TitleBackdrop(group);if(prior){backdrop.request(4);for(let i=0;i<prior;i++)backdrop.tick();}const initial={state:0,frame:31,selection,pulse:71,inputCooldown:9,warmReturn:true,mainFastEntry:false,startupOverlay,menuFadeDuration:77,entryHold:false,returnTweenTicks:priorTween,returnTweenY:0.625,returnTweenX:0.875},before=snap(group),controlBefore=Buffer.from(backdrop.control).toString('hex'),warm=warmTitleMain(group,initial,backdrop),warmed=snap(group),controlAfter=Buffer.from(backdrop.control).toString('hex'),finished=finishWarmTitleMain(group,warm,{backdrop,fade});cases.push({fadeBefore,fadeAfter:Buffer.from(fade.state).toString('hex'),initial,before,controlBefore,warm,warmed,controlAfter,counter:backdrop.counter,finished,after:snap(group)});}console.log(JSON.stringify({refs:titleResources,decisions,cases}));
"""
 data=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();n.load_title(data['refs']);m=n.m;digest=hashlib.sha256()
 for c in data['decisions']:
  m.mem_write(n.owner,bytes(0x16900));m.mem_write(n.owner+0x168b0,struct.pack('<i',10));m.mem_write(n.owner+0x9638,struct.pack('<i',c['initial']['frame']));m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_RBP,0);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14004b0d7,0x14004cbf4,count=100);assert struct.unpack('<i',m.mem_read(n.owner+0x168b0,4))[0]==c['expected']['state'];assert struct.unpack('<i',m.mem_read(n.owner+0x9638,4))[0]==c['expected']['frame']
 fields=[(0x1685c,'returnTweenTicks','i'),(0x16860,'returnTweenY','f'),(0x16864,'returnTweenX','f'),(0x168b0,'state','i'),(0x9638,'frame','i'),(0x28,'selection','i'),(0x30,'pulse','i'),(0x1686c,'inputCooldown','i'),(0x16876,'warmReturn','B'),(0x16875,'mainFastEntry','B'),(0x16874,'startupOverlay','B'),(0x168a8,'menuFadeDuration','i'),(0x16877,'entryHold','B')]
 def verify(slots,expected):
  for p,key,fmt in fields:assert struct.unpack('<'+fmt,m.mem_read(n.owner+p,struct.calcsize(fmt)))[0]==expected[key],(key,expected)
  for slot in slots:
   actual=bytearray(m.mem_read(n.owner+slot['offset'],288))
   for p in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',actual,p)[0]
    if ptr:struct.pack_into('<Q',actual,p,ptr-next(lo for lo,hi in n.ranges if lo<=ptr<hi))
   ptr=struct.unpack_from('<Q',actual,0x100)[0]
   if ptr:struct.pack_into('<Q',actual,0x100,(ptr-n.manager-0x608)//64+1)
   wanted=bytes.fromhex(slot['state']);assert actual==wanted,(slot['offset'],[(hex(i),a,b)for i,(a,b)in enumerate(zip(actual,wanted))if a!=b][:12]);digest.update(actual)
 for index,c in enumerate(data['cases']):
  m.mem_write(n.owner,bytes(0x20000))
  for slot in c['before']:
   raw=bytearray.fromhex(slot['state'])
   for p in [0xf0,0xf8]:
    ptr=struct.unpack_from('<Q',raw,p)[0]
    if ptr:struct.pack_into('<Q',raw,p,n.assetByFile[slot['file']]+ptr)
   ptr=struct.unpack_from('<Q',raw,0x100)[0]
   if ptr:struct.pack_into('<Q',raw,0x100,n.manager+0x608+(ptr-1)*64)
   m.mem_write(n.owner+slot['offset'],bytes(raw))
  for p,key,fmt in fields:m.mem_write(n.owner+p,struct.pack('<'+fmt,c['initial'][key]))
  m.mem_write(n.owner+0x16834,bytes.fromhex(c['controlBefore']));sp=n.stack+0x8000;m.mem_write(sp,struct.pack('<Q',n.stack+0xf000));m.reg_write(UC_X86_REG_RSP,sp);m.reg_write(UC_X86_REG_RCX,n.owner);m.emu_start(0x14004d370,n.stack+0xf000,count=10000000);assert m.reg_read(UC_X86_REG_RIP)==n.stack+0xf000;verify(c['warmed'],c['warm']);assert bytes(m.mem_read(n.owner+0x16834,40)).hex()==c['controlAfter']
  assert struct.unpack('<i',m.mem_read(n.owner+0x16868,4))[0]==c['counter']
  m.reg_write(UC_X86_REG_RSI,n.owner);m.reg_write(UC_X86_REG_RBP,0);m.reg_write(UC_X86_REG_RBX,int(c['warm']['mainFastEntry']));m.reg_write(UC_X86_REG_R10,3);m.reg_write(UC_X86_REG_R11,6);m.reg_write(UC_X86_REG_R12,28);m.reg_write(UC_X86_REG_RDI,8);m.reg_write(UC_X86_REG_R14,24);m.mem_write(n.vm,bytes.fromhex(c['fadeBefore']));m.mem_write(0x140c22158,struct.pack('<Q',n.vm));m.emu_start(0x140047fa2 if c['initial']['startupOverlay'] else 0x14004801b,0x140048174,count=2000);verify(c['after'],c['finished']);assert bytes(m.mem_read(n.vm,56)).hex()==c['fadeAfter']
 assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources};report=dict(scope=__doc__,decisionCases=len(data['decisions']),warmCases=len(data['cases']),vmComparisons=len(data['cases'])*132*2,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-title-selection-return-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'decisionCases':len(data['decisions']),'warmCases':len(data['cases'])}))
if __name__=='__main__':main()
