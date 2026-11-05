"""Bind visible save/reload/replay evidence for the current quiet TH14 build.

Menu/HUD observations are operator observations, not automated pixel checks.
No replay was exported: this tool does not read browser storage or substitute
filesystem access for the refused browser download. It reads only screenshots,
AX text, and metadata already written by the permitted UI observations.
"""
from pathlib import Path
import argparse
import hashlib
import json

R = Path(__file__).resolve().parents[1]
H = R / 'artifacts/th14/sidebar-visibility-long-nov05'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def evidence():
    bindings = {}

    def raw(name):
        path = H / name
        data = path.read_bytes()
        bindings[path.relative_to(R).as_posix()] = dict(bytes=len(data), sha256=SHA(data))
        return data

    focus = json.loads(raw('inactive-tab-focus.json'))
    assert len(focus) == 8 and all(not row['sidebarPresent'] for row in focus)
    assert any('checkbox 14' in line for row in focus for line in row['focus'])
    assert 'Value: 1' in raw('keyboard-selected-ax.txt').decode()
    for name in ['after-save-selected-ax.txt', 'after-replay-selected-ax.txt', 'final-sidebar-ax.txt']:
        text = raw(name).decode()
        assert 'button 管理' in text and 'button 启动游戏' in text
    for name in ['manager-before-play-ax.txt', 'manager-after-play-ax.txt']:
        text = raw(name).decode()
        assert 'th14_01.rpy' in text and '1 个文件' in text
    assert json.loads(raw('console-after-play.json')) == []
    names = ['inactive-initial', 'keyboard-selected', 'reimu-b-weapon', 'live-current',
             'live-save-choice', 'save-empty-slots', 'name-editor-initial',
             'name-c-end-selected', 'name-c-end-actual', 'slot01-after-save',
             'after-save-quit', 'manager-before-play', 'reloaded-replay-list',
             'replay-stage-list', 'replay-observed', 'replay-stable-end',
             'replay-returned', 'quit-attempt-opened-options',
             'after-replay-actual-quit', 'manager-after-play', 'final-sidebar']
    for name in names:
        assert raw(name + '.jpg')[:3] == b'\xff\xd8\xff'
    # Absence is about this evidence directory only. Never search browser
    # downloads, caches, or IndexedDB to work around the refused export.
    assert not list(H.glob('*.rpy'))
    parent_path = R / 'artifacts/th14/sidebar-visibility-nov05/launcher/launcher-report.json'
    parent_raw = parent_path.read_bytes()
    parent = json.loads(parent_raw)
    assert parent['buildId'] == '8db50b49997b0bbd7a69'
    assert parent['wasmSha256'] == '7396f28c66e97e961b94352fca493ee54ad1b67ae757b1715b811826db410325'
    return dict(schema='th14/current-browser-visible-new-recording/1',
        verifiedFiniteVisibleSaveReloadPlay=True,
        observationSource='Operator-visible ordinary menus/HUD and screenshot bindings; no engine state extraction or pixel-equivalence claim.',
        browserId='2', tabId='4', origin='http://localhost:8210/', quiet=True,
        wasmSha256=parent['wasmSha256'], candidateBuildId=parent['buildId'],
        launcherReportSha256=SHA(parent_raw),
        inactiveKeyboard=dict(tabSteps=8, hiddenSidebarNeverInAx=True,
                              keyboardSelectedGameAndRevealedSidebar=True),
        recording=dict(slot=1, previouslyEmpty=True, name='C', character='Reimu', subtype='B',
            difficulty='Normal', stage=1, naturalCollisionGameOver=True, continueUsed=False,
            saveEntry='GameOver Save directly to slot list', nameAppendedAndEndConfirmed=True,
            saveYesNoConfirmationObserved=False, returnedTitleAndOrdinaryQuit=True),
        replay=dict(parentPageReloaded=True, ordinaryListRetainedNameAndSelection=True,
            ordinaryStageOneStarted=True, fastForwardUsed=False, naturalEndObserved=True,
            secondStableMenuObserved=True, returnedReplayListAndOrdinaryQuit=True),
        selectedVisibleTerminalFields=dict(displayedScore=4320, lives=0, lifePieces='0/3',
            bombs=3, bombPieces='0/8', power='1.00', pointValue=10010, graze=13,
            matchedLiveGameOverAndReplayEnd=True),
        sidebar=dict(additionalOrdinaryQuitCycles=2, accessibleBeforeOpeningRecoveryModal=True,
            managersOpenedAfterSaveAndReplay=True, visibleFilesAfterEach=1,
            refreshOrChangelogUsedForFailureRecovery=False, permanentFixAccepted=False,
            comparableUnmodifiedLongControlRun=False),
        retainedActionDeviation=dict(quitAttemptOpenedOptions=True, optionsSettingsChanged=False,
            actualMenuObservedAndCorrected=True, immediateBatchKeyDeliveryReliabilityProven=False),
        download=dict(approvalRejected=True, replayExportAcquired=False, retryOrWorkaround=False),
        newReplayByteIdentityVerified=False, newReplayNativeCodecVerified=False,
        newReplayOriginalPlaybackVerified=False, exactReplayBytesOrFrameCountKnown=False,
        user8208TabOrDataTouched=False, engineInternalsRead=False,
        browserEvaluationMutatedApp=False, settingsChanged=False, viewportChanged=False,
        consoleWarningsOrErrors=0, gameplayOrPlatformSourcesChanged=False,
        longSessionAcceptance=False, allSavePathsAccepted=False, allModesAccepted=False,
        wholeOriginalPixelsOrPcmCompared=False, completeBrowserAcceptance=False,
        completeGame=False, nativeEquivalent=False,
        rawAssetsOrObservationsUploaded=False, evidenceBindings=bindings,
        toolSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    report = evidence()
    target = R / 'docs/porting/th14-browser-current-recording-nov05.json'
    if args.check:
        assert json.loads(target.read_bytes()) == report
    else:
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(visibleFlowVerified=True, replayByteVerification=False,
                         additionalQuitCycles=2, permanentFixAccepted=False, completeGame=False)))
