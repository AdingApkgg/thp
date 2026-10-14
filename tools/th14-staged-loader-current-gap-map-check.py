"""Map retained current loading gaps to proven original lifecycle boundaries.

Read-only captures/source audit; it never changes state or masks a difference.
RNG differences are recomputed from complete paired raw32 files. Enemy-owner
records come from the hash-bound independent full-combat comparison explicitly.
"""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'docs/porting/th14-template-layer-full-combat-verified-oct14.json'
OUTPUT=ROOT/'docs/porting/th14-staged-loader-current-gap-map-verified-oct14.json'
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    report=json.loads(REPORT.read_text(encoding='utf-8'))
    assert report['diagnosticEvidenceVerified'] and not report['comparisonPassed']
    assert report['sourceFilesVerified']==265
    for path,digest in report['sourceHashes'].items():assert SHA(ROOT/'runtimes/th12/th12_web'/path)==digest,path
    def paired(suffix):
        matches=[(p,b) for p,b in report['bindings'].items() if p.endswith(suffix)]
        assert len(matches)==1,matches
        path,binding=matches[0];target=ROOT/path
        assert target.stat().st_size==binding['bytes'] and SHA(target)==binding['sha256']
        return path,binding,target.read_bytes()
    port_path,port_binding,port=paired('/portable-state.u32')
    native_path,native_binding,native=paired('/native-state.u32')
    assert len(port)==len(native)==90793*32*4
    raw=[];visual=Counter()
    for index,(a,b) in enumerate(zip(struct.iter_unpack('<32I',port),struct.iter_unpack('<32I',native))):
        for field,(actual,wanted) in enumerate(zip(a,b)):
            if actual==wanted:continue
            if field in (21,22):visual[field]+=1;continue
            assert field==24 and a[0]==b[0]==0 and a[30]==b[30]
            raw.append(dict(index=index,stage=a[30],frame=a[0],field='replayCalls',port=actual,native=wanted))
    assert raw==report['rawGameplayDifferenceRecords'] and len(raw)==25
    owner=[r for r in report['detailDifferenceRecords'] if r['kind']=='enemyNextId']
    assert len(owner)==72 and report['inactiveLoadingDetailDifferenceKinds']=={'enemyNextId':72}
    assert report['allInactiveDetailDifferencesAreLoadingEnemyNextId']
    assert all(r['port']==1 and r['native']==0 and r['frame']==0 for r in owner)
    groups=[]
    for stage in range(2,7):
        r=[x for x in raw if x['stage']==stage];e=[x for x in owner if x['stage']==stage]
        assert len(r)==5 and e
        assert [x['index'] for x in r]==list(range(r[0]['index'],r[0]['index']+5))
        assert [x['index'] for x in e]==list(range(e[0]['index'],e[-1]['index']+1))
        assert r[0]['index']==e[0]['index']
        assert len({x['native'] for x in r})==1 and all(x['port']==0 for x in r)
        groups.append(dict(stage=stage,firstInactiveCallback=r[0]['index'],
                           retainedRngCountCallbacks=len(r),lastOldNativeCallsCallback=r[-1]['index'],
                           nativeGameplayCallsBeforeReset=r[0]['native'],portGameplayCallsAlreadyReset=0,
                           resetBoundaryCallback=r[-1]['index']+1,
                           retainedOwnerAbsentCallbacks=len(e),lastNativeOwnerAbsentCallback=e[-1]['index'],
                           ownerPublicationBoundaryCallback=e[-1]['index']+1,
                           nativeOwnerObservableNextId=0,portAlreadyPublishedNextId=1))
    assert [r['retainedOwnerAbsentCallbacks'] for r in groups]==[15,13,10,15,19]
    proof_paths=[
        'docs/porting/th14-staged-loader-owner-boundary-observed-oct14.json',
        'docs/porting/th14-staged-loader-owner-publication-boundary-observed-oct14.json',
        'docs/porting/th14-staged-loader-wait-predicate-verified-oct14.json',
        'docs/porting/th14-staged-loader-capture-queue-verified-oct14.json',
        'docs/porting/th14-staged-loader-host-boundary-verified-oct14.json']
    proofs={p:dict(bytes=(ROOT/p).stat().st_size,sha256=SHA(ROOT/p)) for p in proof_paths}
    active=[r for r in report['detailDifferenceRecords'] if r['kind']!='enemyNextId']
    assert len(active)==8 and all(r['kind']=='damageAreas' for r in active)
    source_map={
        'GameSession.cpp':'NextStage captures live seed/clearscalls or restoresReplay immediately beforebattle->next_stage. This precedes the original456050 boundary afterguard/Sleep60.',
        'GameBattle.cpp':'next_stage currentlyloads wholeStageResources, thenenter_stage_transition callsenemies.reset(next.timeline); this publishesnextId1 before originalowner creation and has noowner-absent state.',
        'EnemyManager.cpp':'reset destroys entries but retainscommands.manager andenvironment.th14_enemy_list, andtotal_created becomes1; original422821 unpublishes4db544 until4228de/4228e4 publishesemptynewowner/nextId1.',
        'GameResources.cpp':'load_stage mixesSTD/background/logo/enemy parsing withECL/ANIM/messages; nativeStage40d8a0 completion precedesEnemyconstructor publication anditsECL422340.',
        'GameSessionResources.cpp':'load_stage queues allscene/ECL GPUprepare then swapsstage/previous; needs stablepending StageResources and separate scene/timeline readiness.',
        'Application.cpp':'Existing-battle boot upload path doubleupdatesANM andreturnsframe; loader must keep normalcallbacks andpump realwork without thiswholeframe pause.'}
    result=dict(diagnosticEvidenceVerified=True,comparisonPassed=False,productionChanged=False,
                completeGame=False,nativeEquivalent=False,raw32CallbacksRecomputed=90793,rawGameplayDifferences=25,
                rawVisualDifferences=sum(visual.values()),rawVisualDifferenceCounts=dict(visual),
                retainedLoadingEnemyNextIdDifferences=72,retainedOtherActiveDamageAreaDifferences=8,
                stageGroups=groups,sourceMapping=source_map,
                originalMapping=dict(retire='4226c0->422821: global4db544 null; gameplay RNG survives',
                                     request='43726e request12;446a99 initialStageFlag0',
                                     firstSlot='signed manager+20 isfirstscreen-copy fileindex;0waits,negativeleaves; onlyfirstslotchecked',
                                     interrupt='Whileguard>=0,SupervisorFlags4d9684&0x180 chooses435f6f abort;negative skips thiswaitingabortcheck',
                                     minimumWait='435b0d requests60ms onlyinitialStageFlag4d9658==0; no fixedcallback count',
                                     screenCopyAnimation='435b11 reads4d911c=Supervisor+1bc detached compositorcopy0;435b2a pendinginterrupt2;435b3a real46fe50 beforeReplayinitialize. This is not the separateASCII17 loadingindicator.',
                                     rngReset='435f32->456050:45610f gameplay seed,456123 visual seed,456129 gameplaycalls0',
                                     scene='435f3d HUD42eb30 firstloadslogoANMslot6 andcurrentcharacterMSG, then435f4b Stage40d8a0; both precedeEnemyowner publication.',
                                     publish='435f66->4228a0:4228de owner,4228e4 nextId1 before4228fa ECL422340'),
                sourceFilesVerified=265,sourceHashes=report['sourceHashes'],
                bindings={REPORT.relative_to(ROOT).as_posix():dict(bytes=REPORT.stat().st_size,sha256=SHA(REPORT)),port_path:port_binding,native_path:native_binding,**proofs},
                ownerRecordsProvenance='72 records retained from the unchanged hash-bound independent full-combat report. This mapper independently recomputes raw32 differences but does not repeat its complete sparse-object comparison.',
                timingLimitation='5 RNG and15/13/10/15/19 absent-owner callbacks are thisnativecapture outcomes, not implementation constants or newly observedhost time. A minimum60ms isoriginalrequest evidence; Stage/ECL completion must come from actual work.',
                verifierSha256=SHA(Path(__file__)),
                scope='Current265 core source plus immutable raw32/counter records and original unit evidence. The 25+72 loading differences identify premature reset/publication boundaries; no productionfix, timefabrication, masks, completeordinaryNativeending/GPU/audio or whole-game completion.8 active damage-area and181570 visual differences remain failures outside thisloader map.')
    OUTPUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(diagnosticEvidenceVerified=True,rawGameplayDifferences=25,loadingNextIdDifferences=72,
                          retainedActiveDamageAreaDifferences=8,ownerWindowLengths=[15,13,10,15,19],sourceFilesVerified=265)))


if __name__=='__main__':main()
