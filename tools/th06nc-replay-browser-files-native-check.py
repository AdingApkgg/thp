"""Decode actual browser-recorded/exported replay files with native 6b00b body.

Inputs are artifacts produced by browser save/reload/overwrite checks. Compares
all decoded bytes after native heap relocations normalize to file offsets.
Native filesystem I/O and full gameplay playback are excluded.
"""
from pathlib import Path
import hashlib,json,struct,subprocess
from th06nc_native import Native,ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
def main():
 sources=['shared/th06nc/'+s+'.mjs'for s in ['replay-recorder','replay-assemble','replay-file','replay-date','rng']]+['runtimes/th06nc/'+s for s in ['game.mjs','game-save.mjs']];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sources}
 homes=['natural-run-marisa-b-difficulty3-challenge-browser','natural-run-reimu-b-difficulty2-challenge-browser','natural-run-marisa-a-difficulty0-challenge-browser','natural-run-reimu-a-difficulty1-challenge-browser',*[f'extra-{p}-challenge-clear-handoff-browser'for p in ['reimu-a','reimu-b','marisa-a','marisa-b']],'replay-playback-reimu-a-browser','replay-playback-reimu-b-browser','replay-playback-marisa-a-browser','replay-playback-marisa-b-browser','replay-overwrite-browser','replay-save-chord-browser','replay-list-save-request-reimu-a-browser','replay-list-save-request-reimu-b-browser','replay-list-save-request-marisa-a-browser'];homes.extend(p.name for p in sorted((ROOT/'artifacts/th06nc').glob('natural-run-*-challenge-browser')) if p.name not in homes and (ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).is_file() and json.loads((ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).read_text(encoding='utf-8')).get('passed') is True);homes.extend(f'extra-natural-{p}-challenge-browser'for p in ['reimu-a','reimu-b','marisa-a','marisa-b']);homes.extend(p.name for p in sorted((ROOT/'artifacts/th06nc').glob('extra-natural-*-standard-browser')) if p.name not in homes and (ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).is_file() and json.loads((ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).read_text(encoding='utf-8')).get('passed') is True);homes.extend(p.name for p in sorted((ROOT/'artifacts/th06nc').glob('natural-run-*-standard-browser')) if p.name not in homes and (ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).is_file() and (lambda report:report.get('passed')is True and report.get('continuesUsed')==0)(json.loads((ROOT/'docs/porting'/('th06nc-'+p.name+'-verified.json')).read_text(encoding='utf-8'))));paths=[p for home in homes for p in sorted((ROOT/'artifacts/th06nc'/home).glob('*.rpy'))];assert len(paths)>=10,[str(p)for p in paths]
 script="import{readFileSync}from'node:fs';import{decodeReplayFile}from'./shared/th06nc/replay-file.mjs';const paths="+json.dumps([str(p)for p in paths])+";console.log(JSON.stringify(paths.map(p=>({path:p,decoded:Buffer.from(decodeReplayFile(new Uint8Array(readFileSync(p))).bytes).toString('hex')}))));";expected=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT));n=Native();m=n.m;base=n.assets+0x100000;rejected=False;files=[];digest=hashlib.sha256()
 def hook(m,a,size,u):
  nonlocal rejected
  rejected=True;m.reg_write(UC_X86_REG_RIP,0x14006b0e0)
 m.hook_add(UC_HOOK_CODE,hook,begin=0x14006b0f3,end=0x14006b0f3)
 for p,e in zip(paths,expected):
  raw=p.read_bytes();assert len(raw)<0x100000;m.mem_write(base,raw);m.reg_write(UC_X86_REG_RBX,base);m.reg_write(UC_X86_REG_ESI,len(raw));m.reg_write(UC_X86_REG_RSP,n.stack+0x8000);rejected=False;m.emu_start(0x14006b00b,0x14006b0e0,count=max(1000000,len(raw)*64));assert m.reg_read(UC_X86_REG_RIP)==0x14006b0e0,(str(p),'native decode instruction bound');assert not rejected,str(p);decoded=bytearray(m.mem_read(base,len(raw)))
  for offset in range(64,120,8):
   pointer=struct.unpack_from('<Q',decoded,offset)[0]
   if pointer:struct.pack_into('<Q',decoded,offset,pointer-base)
  assert decoded.hex()==e['decoded'],str(p);digest.update(decoded);files.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),decodedSha256=hashlib.sha256(decoded).hexdigest()))
 assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items());report=dict(scope=__doc__,files=files,stateSha256=digest.hexdigest(),sourceSha256=hashes,executableSha256=n.target['sha256'],passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-replay-browser-files-native-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'files':len(files),'stateSha256':report['stateSha256']}))
if __name__=='__main__':main()
