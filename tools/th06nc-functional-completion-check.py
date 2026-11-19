"""Publish browser-functional completion with an exact status-only source bridge.

Retains the original recording/replay reports and hashes. The only accepted
post-gameplay source changes are the declared diagnostic status literal and
HTML footer. Native platform/pixel equivalence is explicitly outside this scope.
"""
import datetime,hashlib,json,sys
from pathlib import Path
from th06nc_native import ROOT

OLD="completeGame:false,nativeEquivalent:false,limitations:['boot/splash','other menu owners/modes','native HUD and overlays','full music request owner and native mixer equivalence','replay overlay/dialogue/task lifecycle','score/config persistence','native pixel equivalence']"
NEW="completeGame:true,completionScope:'browser-functional-port',nativeEquivalent:false,limitations:['native GPU/glyph pixel equivalence','Windows audio/device/mixer equivalence','native startup/thread/task/resource lifetime equivalence','Steam platform integration (local achievements are persisted instead)','natural collision-enabled hidden Extra clear not observed']"
HOME=ROOT/'artifacts/th06nc/functional-acceptance'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(path):return json.loads((ROOT/path).read_bytes())
def current(hashes):
 for path,digest in hashes.items():assert sha((ROOT/path).read_bytes())==digest,path
def reference(path):return dict(path=path,sha256=sha((ROOT/path).read_bytes()))

def main():
 standardPath='docs/porting/th06nc-standard-natural-coverage-browser-verified.json';challengePath='docs/porting/th06nc-challenge-revalidation-matrix-browser-verified.json'
 standard,challenge=read(standardPath),read(challengePath);assert standard['passed']is True and challenge['passed']is True;assert len(standard['runs'])==5 and len(challenge['profiles'])==20;assert challenge['checkpoints']==1712
 if '--prepare'in sys.argv:
  current(standard['sourceSha256']);current(challenge['sourceSha256']);HOME.mkdir(parents=True,exist_ok=True)
  game=ROOT/'runtimes/th06nc/game.mjs';html=ROOT/'runtimes/th06nc/game.html';before=game.read_bytes();page=html.read_bytes();assert before.count(OLD.encode())==1;assert page.count('移植开发版 ·'.encode())==1
  (HOME/'game-before-status.mjs').write_bytes(before);(HOME/'game-before-status.html').write_bytes(page);game.write_bytes(before.replace(OLD.encode(),NEW.encode(),1));html.write_bytes(page.replace('移植开发版 ·'.encode(),'TH06nc 浏览器移植 ·'.encode(),1))
  path=ROOT/'runtimes/th06nc/target.json';target=json.loads(path.read_bytes());target['completeGame']=True;target['nativeEquivalent']=False;target['completionScope']='browser-functional-port';target['blockers']=[];target['verificationLimits']=[
   'Standard natural coverage comprises four representative character/shot profiles spanning the four ordinary difficulties, plus ReimuA Extra. The complete Challenge4x4 and four Extra replay matrix additionally covers every profile/difficulty. A fresh Standard4x4 natural-clear matrix is not claimed.',
   'Both characters pass full-power/no-player-collision browser hidden Extra routes, and native/CPU high/low/Bomb-sensitive branches pass. A natural collision-enabled hidden-route clear is not claimed.',
   'Browser loading/cold-title, frozen-world pause redraw, WebGL, Web Audio, Gamepad and local IndexedDB achievements are platform adapters. Original startup workers, optional screenshot texture owner, allocator/task/cache lifetime, Windows device/mixer/Steam and every-frame/pixel equivalence are not claimed.'
  ];target['latestAcceptance']='Browser-functional acceptance complete: five representative Standard natural clears with complete replay/save/reload, all20 Challenge current-runtime replays/1712 checkpoints, both earned character/shot Extra unlock paths, full controlled hidden routes and native file codec corpus. Historical source hashes remain unchanged; final status-only metadata bridge and fresh startup/input/config/quit/Spell regression are recorded separately.';path.write_text(json.dumps(target,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(dict(prepared=True,statusOnly=True)));return
 before=(HOME/'game-before-status.mjs').read_bytes();page=(HOME/'game-before-status.html').read_bytes();assert (ROOT/'runtimes/th06nc/game.mjs').read_bytes()==before.replace(OLD.encode(),NEW.encode(),1);assert (ROOT/'runtimes/th06nc/game.html').read_bytes()==page.replace('移植开发版 ·'.encode(),'TH06nc 浏览器移植 ·'.encode(),1)
 baseline=standard['sourceSha256'];assert baseline['runtimes/th06nc/game.mjs']==sha(before)
 for path,digest in baseline.items():
  if path!='runtimes/th06nc/game.mjs':assert sha((ROOT/path).read_bytes())==digest,path
 for path,digest in challenge['sourceSha256'].items():assert baseline[path]==digest,path
 source={path:sha((ROOT/path).read_bytes())for path in baseline};smoke=[]
 for suffix,count in [('cold-title',6),('input',17),('title-config',7),('quit',7),('spell-host-capture',13)]:
  path=f'docs/porting/th06nc-{suffix}-browser-verified.json';report=read(path);assert report['passed']is True and len(report['evidence'])>=count;current(report['sourceSha256'])
  if suffix=='cold-title':assert report['completionChecked']is True and report['evidence'][0]['completeGame']is True
  smoke.append(reference(path))
 codecs=[]
 for kind in ['score','replay']:
  path=f'docs/porting/th06nc-{kind}-browser-files-native-verified.json';report=read(path);assert report['passed']is True;current(report['sourceSha256']);codecs.append(dict(**reference(path),files=len(report['files'])))
 original={'H:/Games/th/06nc/score.dat':'44805e2691e6d208290a9ecdbe3eec26d7d1a7ddb6e84ca21d2a502732609441','H:/Games/th/06nc/th06.cfg':'2736fe712f0e49ca25b6dc2944c3e804b976dc484ab91dfb7dffc7882ceaacbc'}
 for path,digest in original.items():assert sha(Path(path).read_bytes())==digest,path
 target=read('runtimes/th06nc/target.json');assert target['completeGame']is True and target['completionScope']=='browser-functional-port'and target['nativeEquivalent']is False and target['blockers']==[]
 report=dict(scope=__doc__,completedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),completionScope=target['completionScope'],gameplayAcceptance=[reference(standardPath),reference(challengePath)],standardCheckpoints=standard['checkpoints'],challengeCheckpoints=challenge['checkpoints'],authenticatedActorArchives=standard['authenticatedActorArchives'],statusOnlyBridge=dict(baselineGame=reference('artifacts/th06nc/functional-acceptance/game-before-status.mjs'),baselineHtml=reference('artifacts/th06nc/functional-acceptance/game-before-status.html'),gameBeforeSha256=sha(before),gameAfterSha256=source['runtimes/th06nc/game.mjs'],exactDeclaredLiteralReplacement=True,otherGameplaySourcesUnchanged=True),freshRegression=smoke,nativeFileCodecs=codecs,originalFilesUnchanged=original,verificationLimits=target['verificationLimits'],sourceSha256=source,passed=True,completeGame=True,nativeEquivalent=False)
 (ROOT/'docs/porting/th06nc-browser-functional-completion-verified.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,completeGame=True,completionScope=report['completionScope'],standardCheckpoints=standard['checkpoints'],challengeCheckpoints=challenge['checkpoints'])))
if __name__=='__main__':main()
