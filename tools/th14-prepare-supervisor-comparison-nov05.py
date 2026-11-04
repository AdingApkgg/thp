"""Derive an explicit Supervisor-pass clock diagnostic without weakening gates.

Missing main-camera/VM/controller observations are not fabricated. The camera
comparisons and their final failure assertions stay enabled. This driver may
therefore reject those fields while still retaining useful RNG diagnostics.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main(out):
    parent=R/'tools/th14-compare-native-player-pump-ready-nov05.mjs';raw=parent.read_bytes()
    assert SHA(raw)=='d3e1bcdf456e3339b16bce7ea00d6e1c42d4656d33cd042804ac8ba6cd4d18bd'
    s=raw.decode()
    def replace(a,b):
        nonlocal s
        assert s.count(a)==1,(a[:120],s.count(a));s=s.replace(a,b)
    replace("'native-read-evidence']);","'native-read-evidence','supervisor-pass-evidence','supervisor-resource-pump']);")
    replace("const root=resolve(import.meta.dirname,'..'),",'const root='+json.dumps(R.as_posix())+',')
    replace("const phasedScheduler=schedulerPhases!=='legacy';","const phasedScheduler=schedulerPhases!=='legacy';\nconst supervisorPassMode=options.has('supervisor-pass-evidence');\nconst supervisorResourcePump=options.get('supervisor-resource-pump')??'disabled';assert(['enabled','disabled'].includes(supervisorResourcePump));assert(supervisorPassMode||supervisorResourcePump==='disabled');")
    replace("const cameraSourceReads=phasedScheduler?stageEvents('worker-camera-source-read-events.jsonl'):[];",
        "const cameraSourceReads=phasedScheduler&&!supervisorPassMode?stageEvents('worker-camera-source-read-events.jsonl'):[];")
    replace("const controllerEvents=schedulerPhases==='observed'?stageEvents('controller-phase-events.jsonl'):[];",
        "const controllerEvents=schedulerPhases==='observed'&&!supervisorPassMode?stageEvents('controller-phase-events.jsonl'):[];")
    block='''const supervisorClock=new Map(),supervisorPumpClock=new Map(),supervisorClockInputs=[];let supervisorEvidenceSha256=null;
if(supervisorPassMode){
 assert(phasedScheduler&&!options.has('scene-copy-observation'));
 assert(nativeReport.supervisorPlayerPumpWatchesFixed&&nativeReport.mainCameraVmControllerWatchesGivenUpAfterPrefix);
 const proofRaw=read(resolve(root,options.get('supervisor-pass-evidence'))),proof=JSON.parse(proofRaw);supervisorEvidenceSha256=sha(proofRaw);
 assert(proof.verifiedFixedHardwareBoundaries&&proof.callbacks===limit&&!proof.physicalFrameIdentityProven);
 assert.equal(proof.verifierSha256,sha(read(resolve(root,'tools/th14-supervisor-pass-timeline-nov05.py'))));
 const reportName=relative(root,resolve(nativeHome,'report.json')).replaceAll('\\\\','/');
 assert.equal(proof.evidenceBindings[reportName]?.sha256,sha(read(resolve(nativeHome,'report.json'))));
 for(const[name,row]of Object.entries(proof.evidenceBindings))assert.equal(sha(read(resolve(root,name))),row.sha256,'Changed fixed-pass evidence '+name);
 const rows=read(resolve(nativeHome,'supervisor-pass-events.jsonl'),'utf8').trim().split('\\n').filter(Boolean).map(x=>JSON.parse(x));
 const entries=new Map(rows.filter(x=>x.pc===0x444890).map(x=>[x.supervisorPassOrdinal,x]));
 const pumps=new Map(rows.filter(x=>x.pc===0x47d720).map(x=>[x.supervisorPassOrdinal,x]));
 for(const player of rows.filter(x=>x.pc===0x44dbd0)){
  const entry=entries.get(player.supervisorPassOrdinal),callback=player.precedingPlayerCallbacks+1;
  assert(entry&&entry.threadId===player.threadId&&entry.debugEventSequence<player.debugEventSequence);
  const pump=pumps.get(player.supervisorPassOrdinal);
  assert(pump&&pump.threadId===player.threadId&&entry.debugEventSequence<pump.debugEventSequence&&pump.debugEventSequence<player.debugEventSequence);
  assert(entry.hostMonotonicNs<=pump.hostMonotonicNs&&pump.hostMonotonicNs<=player.hostMonotonicNs);
  assert(entry.hostMonotonicNs<=player.hostMonotonicNs&&callback>publicationCutoff&&!supervisorClock.has(callback));
  assert.equal(BigInt(player.hostMonotonicNs),times.readBigUInt64LE((callback-1)*8));
  supervisorClock.set(callback,entry.hostMonotonicNs);
  supervisorPumpClock.set(callback,pump.hostMonotonicNs);
  supervisorClockInputs.push({callback,supervisorPassOrdinal:entry.supervisorPassOrdinal,entryPc:entry.pc,entryReceiptNs:entry.hostMonotonicNs,pumpReceiptNs:pump.hostMonotonicNs,playerReceiptNs:player.hostMonotonicNs});
 }
 for(let callback=publicationCutoff+1;callback<=limit;++callback)assert(supervisorClock.has(callback),'Missing actual Supervisor entry for Player '+callback);
}
'''
    replace("if(options.has('scene-copy-observation')){",block+"if(options.has('scene-copy-observation')){")
    replace("if(phasedScheduler){\n assert(c.observed_player_boundary", "if(phasedScheduler&&!supervisorPassMode){\n assert(c.observed_player_boundary")
    replace("resolve(root,'tools/th14-player-pump-trace-evidence-nov05.py')",
        "resolve(root,supervisorPassMode?'tools/th14-supervisor-rng-read-evidence-nov05.py':'tools/th14-player-pump-trace-evidence-nov05.py')")
    replace("assert(prefix===35000&&schedulerPhases==='observed'&&nativeReport.playerPumpDr0MultiplexedDuringRngWatch);",
        "assert(prefix===35000&&schedulerPhases==='observed'&&(supervisorPassMode?(nativeReport.supervisorPlayerPumpWatchesFixed&&!nativeReport.playerPumpDr0MultiplexedDuringRngWatch):nativeReport.playerPumpDr0MultiplexedDuringRngWatch));")
    replace('const observed=controlClock.get(i+1)??pumpClock.get(i+1);',
        'const observed=supervisorPassMode&&i+1>publicationCutoff?supervisorClock.get(i+1):controlClock.get(i+1)??pumpClock.get(i+1);')
    replace('if(phasedScheduler&&maxStage>=2){','if(phasedScheduler&&(maxStage>=2||supervisorPassMode)){')
    replace('assert.equal(c.observed_player_boundary(i+1,lastNow),1);',
        'if(maxStage>=2)assert.equal(c.observed_player_boundary(i+1,lastNow),1);')
    replace('assert.equal(c.rng_audit_menu_tick(updateNow,0),1);',
        "if(supervisorResourcePump==='enabled'&&supervisorPumpClock.has(i+1))assert.equal(c.observed_supervisor_resource_clock(i+1,updateNow,baseNow+BigInt(supervisorPumpClock.get(i+1))-playerOrigin),1);\n assert.equal(c.supervisor_pump_menu_tick(updateNow,0),1);")
    replace('const report={schedulerPhases,',
        'const report={supervisorResourcePump,supervisorResourceClockMeta:Array.from({length:6},(_,word)=>c.supervisor_resource_clock_meta(word)>>>0),supervisorPassMode,supervisorEvidenceSha256,supervisorClockInputCount:supervisorClockInputs.length,actualObservedPassEntryClocksUsed:supervisorPassMode,mainCameraBoundaryDeliveryNotInvented:supervisorPassMode,physicalFrameEntryRecovered:false,schedulerPhases,')
    replace('const sourceReadSnapshots=[];',
        "write(resolve(out,'supervisor-clock-inputs.json'),JSON.stringify({inputs:supervisorClockInputs,passBoundaryPc:0x444890,physicalFrameIdentityProven:false,nativeValuesProvidedToEngine:false})+'\\n',{flag:'wx'});\nconst sourceReadSnapshots=[];")
    replace('report.originalSourceReadPcObserved=true;',
        'report.originalSourceReadPcObserved=!supervisorPassMode&&sourceReadWindows.length>0;')
    old="const original=JSON.parse(gunzipSync(compressed));assert.equal(original.callback,snapshot.callback);assert.equal(original.stage,snapshot.stage);assert.equal(original.stageFrame,snapshot.stageFrame);"
    replace(old,"""const original=JSON.parse(gunzipSync(compressed));
  if(original.callback!==snapshot.callback||original.stage!==snapshot.stage||original.stageFrame!==snapshot.stageFrame){
   const auditCount=c.rng_audit_meta(2),auditWords=[];
   for(let row=0;row<auditCount;++row)for(let word=0;word<16;++word)auditWords.push(c.rng_audit_word(row,word)>>>0);
   write(resolve(out,'rng-register-audit-at-failure.u32'),Buffer.from(new Uint32Array(auditWords).buffer),{flag:'wx'});
   const failure={kind:'combat-checkpoint-boundary-mismatch',callback:snapshot.callback,native:{stage:original.stage,stageFrame:original.stageFrame},portable:{stage:snapshot.stage,stageFrame:snapshot.stageFrame},
    supervisorClockInput:supervisorClockInputs.find(x=>x.callback===snapshot.callback),stateDifferenceCountsBeforeThisCheckpoint:counts,
    nativeState32:Array.from({length:32},(_,word)=>nativeRaw.readUInt32LE(index*128+word*4)),portableState32:Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32)),
    firstScriptReadWindows,firstScriptReadReadyAtObservedPump,firstScriptReadStates:firstScriptReadWindows.map(window=>({stage:window.stage,words:Array.from({length:12},(_,word)=>c.first_script_read_window_word(window.stage,word)>>>0)})),
    auditMeta:Array.from({length:5},(_,word)=>c.rng_audit_meta(word)>>>0),supervisorResourcePump,supervisorResourceClockMeta:Array.from({length:6},(_,word)=>c.supervisor_resource_clock_meta(word)>>>0),clockInputsOnly:true,noOriginalStateValuesProvidedToEngine:true,comparisonGateUnchanged:true,completeGame:false};
   write(resolve(out,'checkpoint-failure.json'),JSON.stringify(failure,null,2)+'\\n',{flag:'wx'});
  }
  assert.equal(original.callback,snapshot.callback);assert.equal(original.stage,snapshot.stage);assert.equal(original.stageFrame,snapshot.stageFrame);""")
    # Gate code is byte-for-byte retained, including state, camera, HUD, live
    # VM, allocation, expanded camera/cursor and source-snapshot assertions.
    gates=raw.decode()[raw.decode().index('assert(report.allRaw32ByteIdentical);'):]
    assert s[s.index('assert(report.allRaw32ByteIdentical);'):]==gates
    assert not out.exists();out.mkdir(parents=True);driver=out/'driver.mjs';driver.write_text(s,encoding='utf8',newline='\n')
    subprocess.run(['C:/nvm4w/nodejs/node.exe','--check',str(driver)],check=True,capture_output=True)
    report=dict(prepared=True,parentDriverSha256=SHA(raw),driverSha256=SHA(driver.read_bytes()),allFinalGatesByteIdentical=True,
        observedSupervisorEntryPc=0x444890,missingCameraVmControllerEventsNotInvented=True,nativeStateValuesProvidedToEngine=False,
        representativePreviousPlayerClockFallbackAdded=False,physicalFrameEntryRecovered=False,ordinaryIndependentTimingAccepted=False,
        toolSha256=SHA(Path(__file__).read_bytes()),completeGame=False)
    (out/'prepared.json').write_text(json.dumps(report,indent=2)+'\n');(out/'prepare-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert out.is_relative_to(R/'artifacts/th14')and not out.exists();main(out)
