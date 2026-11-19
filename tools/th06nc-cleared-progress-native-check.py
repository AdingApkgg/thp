"""Actual stage-init 3af27..3afe5 and ending-init 2c9ef..2caa6 CLRD updates.

Complete CLRD bytes compare; stage increment and ending's already-cleared flag
compare too. Inputs cover profile/difficulty, stage markers, protection, deaths,
continues, practice and playback. Other scene initialization, ending presentation,
unlock consumers, persistence and browser excluded.
"""
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn.x86_const import *

def main():
    source='shared/th06nc/cleared-progress.mjs';sha=hashlib.sha256((ROOT/source).read_bytes()).hexdigest();script="""
import{advanceClearedProgress,markClearedCompletion}from'./shared/th06nc/cleared-progress.mjs';const cases=[],hex=b=>Buffer.from(b).toString('hex');for(let profile=0;profile<4;profile++)for(let difficulty=0;difficulty<5;difficulty++)for(const stageIndex of [0,1,5,6,7])for(const lifeProtection of [false,true])for(const deathCount of [0,5,6])for(const continuesUsed of [0,1])for(const mode of ['ordinary','practice','spellPractice','playback']){const n=cases.length,before=Uint8Array.from({length:96},(_,i)=>[0,1,5,6,99,255][(n+i)%6]),e={character:profile>>1,shot:profile&1,difficulty,stageIndex,lifeProtection,deathCount,continuesUsed,practice:mode==='practice',spellPractice:mode==='spellPractice',replayPlayback:mode==='playback'},advance=before.slice(),ending=before.slice(),next=advanceClearedProgress(advance,e),result=markClearedCompletion(ending,e);cases.push({before:hex(before),e,advance:hex(advance),ending:hex(ending),next,result});}console.log(JSON.stringify(cases));
"""
    cases=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;digest=hashlib.sha256()
    for i,c in enumerate(cases):
        e=c['e'];m.mem_write(0x1404f1e80,bytes([e['character'],e['shot']]));m.mem_write(0x1404f27c0,struct.pack('<i',e['difficulty']));m.mem_write(0x1404f278c,bytes([e['replayPlayback']]));m.mem_write(0x1404f27b4,bytes([e['practice'],e['spellPractice']]));m.mem_write(0x1404f27c4,bytes([e['lifeProtection']]));m.mem_write(0x1404f1e60,struct.pack('<i',e['deathCount']));m.mem_write(0x1404ff0dc,bytes([e['continuesUsed']]));m.mem_write(0x1404f1e84,struct.pack('<i',e['stageIndex']));m.mem_write(0x1404ff0f4,bytes.fromhex(c['before']));m.reg_write(UC_X86_REG_RDI,0x1404f1e60);m.reg_write(UC_X86_REG_R14,0);m.emu_start(0x14003af27,0x14003afe5,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x14003afe5,(i,'advance stop');actual=bytes(m.mem_read(0x1404ff0f4,96));assert actual==bytes.fromhex(c['advance']),(i,'advance CLRD');assert struct.unpack('<i',m.mem_read(0x1404f1e84,4))[0]==c['next'],(i,'stage');digest.update(actual)
        m.mem_write(0x1404ff0f4,bytes.fromhex(c['before']));m.mem_write(n.owner+0x124c,b'\xff');m.reg_write(UC_X86_REG_RDI,n.owner);m.emu_start(0x14002c9ef,0x14002caa6,count=1000);assert m.reg_read(UC_X86_REG_RIP)==0x14002caa6,(i,'ending stop');actual=bytes(m.mem_read(0x1404ff0f4,96));assert actual==bytes.fromhex(c['ending']),(i,'ending CLRD');assert bool(m.mem_read(n.owner+0x124c,1)[0])==c['result']['alreadyCleared'],(i,'already cleared');assert bool(m.reg_read(UC_X86_REG_R9)&255)==c['result']['restricted'],(i,'restricted');digest.update(actual)
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha
    report=dict(scope=__doc__,cases=len(cases),stateSha256=digest.hexdigest(),sourceSha256={source:sha},executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False)
    (ROOT/'docs/porting/th06nc-cleared-progress-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'cases':len(cases)}))
if __name__=='__main__':main()
