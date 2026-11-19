"""Actual title start settings 4dbc0..4dc3c and gameplay stock/power prefix.

Compare all seven settings written by the title prefix, plus actual live stock
copies, initial player Power and score-extend index from 3aa0f..3aaf6. Compare all16 movement rectangle bytes initialized at3aa49..3aa71. Also compare initial rank at new-run and playback-stage original call sites.
Unrelated gameplay owner
fields, remaining initializer, music teardown and native task graph excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
 source='shared/th06nc/gameplay-start-settings.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
 script="""
import{gameplayStartSettings,gameplayPlayerBounds}from'./shared/th06nc/gameplay-start-settings.mjs';const cases=[];for(const mode of [0,1,2,255])for(const practice of [0,1,255])for(const difficulty of [-1,0,1,3,4,5])for(const lives of [0,2,8,255])for(const bombs of [0,3,8,255]){const input={mode,practice,difficulty,lives,bombs};cases.push({input,expected:gameplayStartSettings(input),bounds:gameplayPlayerBounds});}console.log(JSON.stringify(cases));
"""
 cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
 fields={'lifeProtection':(0x1404f27c4,'B'),'practice':(0x1404f27b4,'B'),'spellPractice':(0x1404f27b5,'B'),'defaultLives':(0x1404ff0f0,'B'),'defaultBombs':(0x1404ff0f1,'B'),'replayPlayback':(0x1404f278c,'B'),'gameState':(0x140c21d9c,'i')}
 for index,c in enumerate(cases):
  a=c['input'];e=c['expected'];m.mem_write(n.manager+0x168d1,bytes([a['practice']]));m.mem_write(0x140c21db4,bytes([a['lives'],a['bombs']]));m.mem_write(0x140c21dbb,bytes([a['mode']]));m.mem_write(0x1404f27c0,struct.pack('<i',a['difficulty']))
  for address,fmt in fields.values():m.mem_write(address,bytes([0xa5])*struct.calcsize(fmt))
  m.reg_write(UC_X86_REG_RCX,n.manager);m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);m.emu_start(0x14004dbc0,0x14004dc3c,count=1000)
  actual={key:struct.unpack('<'+fmt,m.mem_read(address,struct.calcsize(fmt)))[0]for key,(address,fmt)in fields.items()}
  assert actual=={key:e[key]for key in fields},(index,actual,e)
  m.mem_write(n.owner,bytes(0xd300));m.mem_write(n.owner+0x960,struct.pack('<i',a['difficulty']));m.reg_write(UC_X86_REG_RCX,n.owner);m.reg_write(UC_X86_REG_R14,0);m.reg_write(UC_X86_REG_R13,8);m.reg_write(UC_X86_REG_RBP,0);m.reg_write(UC_X86_REG_R10,4);m.emu_start(0x14003aa0f,0x14003aaf6,count=1000)
  assert list(struct.unpack('<4f',m.mem_read(n.owner+0xd280,16)))==c['bounds'],(index,'player bounds')
  power=struct.unpack('<H',m.mem_read(n.owner+0x28,2))[0];assert power==e['playerPower'],(index,'power',power,e)
  assert bytes(m.mem_read(0x140c21de0,2))==bytes([e['defaultLives'],e['defaultBombs']]),(index,'live stocks')
  assert bytes(m.mem_read(n.owner+0xd292,1))[0]==e['continueState'],(index,'extend index')
  digest.update(bytes([actual['defaultLives'],actual['defaultBombs'],power,e['continueState']]))
 rank_expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import{initialGameplayRank}from'./shared/th06nc/gameplay-start-settings.mjs';console.log(JSON.stringify([0,1,2,3,4].map(initialGameplayRank)));"],cwd=ROOT));rank_cases=0
 for difficulty,rank in enumerate(rank_expected):
  for prior in range(16):
   for start,end in [(0x14003aed7,0x14003af10),(0x14003b15d,0x14003b171)]:
    m.mem_write(n.owner,bytes([prior*17])*0xd500);m.mem_write(0x1404f27c0,struct.pack('<i',difficulty));m.reg_write(UC_X86_REG_RDI,n.owner);m.reg_write(UC_X86_REG_RSI,0x140000000);m.emu_start(start,end,count=1000);actual=bytes(m.mem_read(n.owner+0xd41c,4));assert struct.unpack('<i',actual)[0]==rank,(difficulty,start);digest.update(actual);rank_cases+=1
 assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
 report=dict(scope=__doc__,cases=len(cases),boundsCases=len(cases),rankCases=rank_cases,stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-gameplay-start-settings-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases),'rankCases':rank_cases}))
if __name__=='__main__':main()
