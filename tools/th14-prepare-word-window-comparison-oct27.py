"""Compose a frozen multi-transition diagnostic from the unchanged comparator.

Only observed instruction boundaries and time can change Scene delivery. Copied
native camera values remain comparisons, never inputs to the C++ model.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'artifacts/th14') and not out.exists()
    base = ROOT / 'tools/th14-compare-native-campaign.mjs'
    raw = base.read_bytes()
    source = raw.decode().replace('\r\n', '\n')
    marker = "root=resolve(import.meta.dirname,'..')"
    assert source.count(marker) == 1
    source = source.replace(marker, 'root=' + json.dumps(str(ROOT)))
    start = source.index("if(options.has('scene-copy-observation')){")
    end = source.index('\nif(phasedScheduler){', start)
    original = source[start:end]
    assert "prefix===15000" in original and "assert.equal(words.length,3)" in original
    replacement = """if(options.has('scene-copy-observation')){
 assert(phasedScheduler&&prefix>0&&prefix<=52000,'This diagnostic requires a retained prefix within its declared52000 maximum');
 const proof=JSON.parse(read(resolve(root,options.get('scene-copy-observation'))));
 assert(proof.verifiedFiniteOriginalSceneCopyObservation&&proof.diagnosticPrefixOnly&&proof.callbacks===prefix);
 assert.equal(proof.plannedMaximumCallbacks,52000);
 assert(!proof.completeGame&&!proof.nativeEquivalent&&!proof.oldCameraFailureClosed);
 assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-scene-copy-word-window-evidence-oct27.py'))));
 for(const[path,row]of Object.entries(proof.bindings))assert.equal(sha(read(resolve(root,path))),row.sha256,'Observation binding changed: '+path);
 const nativeKey=relative(root,resolve(nativeHome,'report.json')).replaceAll('\\\\','/');
 assert.equal(proof.bindings[nativeKey]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
 const words=read(resolve(nativeHome,'scene-camera-word-copy-events.jsonl'),'utf8').trim().split('\\n').map(x=>JSON.parse(x));
 assert.equal(words.length,9);assert.equal(proof.sceneCopiesObserved,3);
 for(let index=0;index<words.length;index+=3){
  const lanes=words.slice(index,index+3);assert.deepEqual(lanes.map(row=>row.word),[0,1,2]);
  const stage=lanes[0].stage,callback=lanes[0].precedingPlayerCallbacks;
  const before=sceneEvents.find(row=>row.stage===stage&&row.event==='scene-camera-copy-before');
  const after=sceneEvents.find(row=>row.stage===stage&&row.event==='scene-camera-copy-after');
  assert(before&&after&&before.precedingPlayerCallbacks<=callback&&callback<=after.precedingPlayerCallbacks);
  for(const row of lanes){
   assert(row.readOnly&&row.exactTrapFlagStep&&row.actualOriginalRepIterationObserved&&!row.nativeValuesProvidedToEngine);
   assert.equal(row.stage,stage);assert.equal(row.precedingPlayerCallbacks,callback);
   assert.equal(row.threadId,before.threadId);assert.equal(row.scene,before.scene);
  }
  const completePerspective=before.mainPhaseAtObservation==='draw'&&before.precedingPlayerCallbacks===callback&&lanes.every(row=>{
   const b=row.lastMainCameraBoundary;
   return b?.readOnly&&b.event==='world-perspective-right-written'&&b.pc===0x4465a6&&b.mainPhaseAtObservation==='draw'
    &&b.precedingPlayerCallbacks===callback&&b.stage===stage&&b.hostMonotonicNs<row.hostMonotonicNs;
  });
  if(!completePerspective){
   sceneCopyWordHandoffs.push({stage,callback,applied:false,completionSource:'ExistingBoundaryDeliveryRetained',
    copyStartCallback:before.precedingPlayerCallbacks,
    stoppedMainPcs:lanes.map(row=>row.mainThreadRegisters.eip)});
   continue;
  }
  // Actual copy values and matrices are never supplied to the engine.
  const delivery={stage,callback,applied:true,readyNs:lanes[0].hostMonotonicNs,
   completionSource:'OriginalThreeWordTrapsAfterObservedPerspectiveBoundary',
   perspectiveBoundaryNs:lanes[0].lastMainCameraBoundary.hostMonotonicNs};
  assert(!sceneWordDelivery.has(stage));sceneWordDelivery.set(stage,delivery);sceneCopyWordHandoffs.push(delivery);
 }
}
"""
    source = source[:start] + replacement + source[end:]
    generated = source.encode()
    verifier_base = ROOT / 'tools/th14-verify-native-campaign.py'
    verifier_raw = verifier_base.read_bytes()
    verifier = verifier_raw.decode().replace('\r\n', '\n')
    marker = 'ROOT=Path(__file__).resolve().parents[1]'
    assert verifier.count(marker) == 1
    verifier = verifier.replace(marker, 'ROOT=Path(' + repr(str(ROOT)) + ')')
    marker = "assert original['childExited']and not original['error']"
    assert verifier.count(marker) == 1
    verifier = verifier.replace(marker, "assert original['childExited']")
    start = verifier.index('    if args.scene_copy_observation:')
    end = verifier.index("    else:assert original['hardwareBreakpointsOnly']", start)
    previous = verifier[start:end]
    assert 'args.prefix==15000' in previous and 'len(reported[\'sceneCopyWordHandoffs\'])==1' in previous
    replacement = """    if args.scene_copy_observation:
        assert 0<args.prefix<=52000 and original.get('hardwareDebugRegistersAndTrapFlagOnly')
        proof_path=args.scene_copy_observation.resolve();proof=load(proof_path)
        assert proof['verifiedFiniteOriginalSceneCopyObservation']and proof['diagnosticPrefixOnly']and proof['callbacks']==args.prefix
        assert proof['plannedMaximumCallbacks']==52000 and proof['originalCaptureTerminalErrorRetained']==original['error']
        assert proof['bindings'][(native/'report.json').relative_to(ROOT).as_posix()]['sha256']==SHA(read(native/'report.json'))
        plans=[ROOT/path for path in proof['bindings']if path.endswith('/plan.json')]
        assert len(plans)==1 and proof['sceneCopiesObserved']==3 and proof['actualRightWordObservations']==9
        command=[sys.executable,str(ROOT/'tools/th14-scene-copy-word-window-evidence-oct27.py'),'--home',str(plans[0].parent),'--output',str(proof_path),'--check']
        if original['error']:
            assert proof['captureBudgetStopped']and not proof['originalCaptureSucceeded']and not proof['captureReachedDeclaredMaximum']
            command.append('--budget-stop-diagnostic')
        else:assert proof['originalCaptureSucceeded']and not proof['captureBudgetStopped']
        subprocess.run(command,check=True)
        assert reported['sceneCopyObservationSha256']==SHA(read(proof_path))and len(reported['sceneCopyWordHandoffs'])==3
"""
    verifier = verifier[:start] + replacement + verifier[end:]
    marker = "else:assert original['hardwareBreakpointsOnly']"
    assert verifier.count(marker) == 1
    verifier = verifier.replace(marker, marker + "and not original['error']")
    marker = '    if args.prefix:result[\'limitations\'].append('
    assert verifier.count(marker) == 1
    verifier = verifier.replace(marker, "    result.update(originalCaptureSucceeded=not bool(original['error']),originalCaptureTerminalErrorRetained=original['error'],plannedCaptureCompleted=not bool(original['error'])and captured==original['observerOptions']['maximum_callbacks'])\n" + marker)
    verifier = verifier.replace('only the declared15000-callback prefix is accepted', 'only the declared52000-callback window is accepted')
    import ast
    ast.parse(verifier)
    verifier_generated = verifier.encode()
    out.mkdir()
    (out / 'comparison.mjs').write_bytes(generated)
    (out / 'verifier.py').write_bytes(verifier_generated)
    result = dict(baseComparisonPath=base.relative_to(ROOT).as_posix(), baseComparisonSha256=SHA(raw),
        generatedComparisonSha256=SHA(generated), baseVerifierPath=verifier_base.relative_to(ROOT).as_posix(),
        baseVerifierSha256=SHA(verifier_raw), generatedVerifierSha256=SHA(verifier_generated),
        preparerSha256=SHA(Path(__file__).read_bytes()), allStateCameraHudVmCombatAndAllocationGatesRetained=True,
        maximumCallbacks=52000, actualCountFromVerifiedRecord=True, budgetStoppedCaptureRemainsFailure=True,
        sceneTransitions=3, productionEngineChanged=False,
        nativeCameraValuesProvidedToEngine=False, unmodelledWordBoundariesRemainDiagnostics=True,
        completeGame=False, nativeEquivalent=False, browserAcceptance=False)
    (out / 'prepared.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
