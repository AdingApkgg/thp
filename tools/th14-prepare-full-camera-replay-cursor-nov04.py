"""Extend the frozen shared-event-clock observer with camera tails and cursor reads."""
from pathlib import Path
import argparse,ast,hashlib,json
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
P=R/'artifacts/th14/unified-event-context-trace-nov04'


def prepare(out):
 parent=(P/'observer.py').read_bytes();assert SHA(parent)=='742e84932b89d3b8837ba44caa867ee944e8ec588fbeb98378b58d94a72990be'
 assert parent==(P/'native/observer-source.py').read_bytes()
 helper_path=R/'tools/th14-replay-cursor-readonly-nov04.py';helper=helper_path.read_bytes();text=parent.decode().replace('\r\n','\n')
 def replace(old,new,count=1):
  nonlocal text
  assert text.count(old)==count,(old[:80],text.count(old));text=text.replace(old,new)
 replace('def player_snapshot():',helper.decode().replace('\r\n','\n')+'\n\ndef player_snapshot():')
 replace('camera_raw=bytearray();live_capture_callbacks=', 'camera_tail_raw=bytearray();replay_cursor_raw=bytearray();replay_eof_watch_pc=0;replay_branch_events=[]\ncamera_raw=bytearray();live_capture_callbacks=')
 replace("targets[0x469c48]='winmain-loop-exit-boundary'", "targets[0x469c48]='winmain-loop-exit-boundary'\ntargets.update({0x4552cd:'replay-declared-input-exhaustion-branch',0x45521b:'replay-all-ffff-marker-branch'})")
 replace('    for index,address in enumerate(addresses):',
  '    if first_snapshot is not None and not trace_publications and tid==pi.tid and not transition_trace and replay_eof_watch_pc:\n        addresses[3]=replay_eof_watch_pc # Rotate the otherwise free/final-loop-exit DR3 only near final-stage EOF.\n    for index,address in enumerate(addresses):')
 replace('                        if camera_read_hit:', '''                        if pc in (0x4552cd,0x45521b):
                            assert ev.tid==pi.tid and replay_eof_watch_pc==pc
                            cursor_words=struct.unpack('<14I',snapshot(read))
                            assert cursor_words[2:4]==(1,6) and cursor_words[10]&65535==6
                            if pc==0x4552cd:assert cursor_words[7]>=cursor_words[9] and cursor_words[7]<0x80000000
                            else:assert cursor_words[12:14]==(0xffffffff,0xffff)
                            row=dict(event=targets[pc],pc=pc,threadId=ev.tid,precedingPlayerCallbacks=callback_count,
                                hostMonotonicNs=observation_clock_ns(),cursorWords=list(cursor_words),readOnly=True,
                                instructionStillPending=True,hardwareExecuteBreakpoint=True,markerHandlerExecuted=False)
                            replay_branch_events.append(row)
                            with(home/'replay-reader-branch-events.jsonl').open('a',encoding='utf8')as stream:stream.write(event_json(row)+'\\n')
                            replay_eof_watch_pc=0
                        elif camera_read_hit:''')
 replace('                            camera_raw.extend(read(0x4d9514,0x124));raw.extend(','''                            full_camera=read(0x4d9514,300);camera_raw.extend(full_camera[:292]);camera_tail_raw.extend(full_camera[292:])
                            cursor_bytes=snapshot(read);replay_cursor_raw.extend(cursor_bytes);cursor_words=struct.unpack('<14I',cursor_bytes)
                            if cursor_words[0]&15==15 and cursor_words[3]==6 and cursor_words[10]&65535==6:
                                candidate=0x4552cd if cursor_words[7]>=cursor_words[9] and cursor_words[7]<0x80000000 else 0x45521b if cursor_words[0]&16 and cursor_words[12:14]==(0xffffffff,0xffff) else 0
                                if candidate and not any(row['pc']==candidate for row in replay_branch_events):replay_eof_watch_pc=candidate
                            raw.extend(''')
 marker="(home/'world-camera.raw').write_bytes(camera_raw);(home/'hud-score.u32').write_bytes(hud_raw)"
 replace(marker,marker+";(home/'world-camera-tail.u32').write_bytes(camera_tail_raw);(home/'replay-cursor.u32').write_bytes(replay_cursor_raw)",2)
 marker="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
 addition="""    assert len(camera_tail_raw)==callback_count*8 and len(replay_cursor_raw)==callback_count*56
    report.update(worldCameraTailStride=8,worldCameraTailSha256=sha(camera_tail_raw),worldCameraTailBytes=len(camera_tail_raw),
        worldCameraAll75WordsCaptured=True,worldCameraTailNativeWordIndices=[73,74],replayCursorStride=STRIDE,
        replayCursorFields=FIELDS,replayCursorSha256=sha(replay_cursor_raw),replayCursorBytes=len(replay_cursor_raw),
        replayCursorReadOnly=True,replayCursorHelperEmbeddedSha256='HELPER_SHA',replayReaderBranchEvents=replay_branch_events,
        actualDeclaredInputExhaustionBranchObserved=any(row['pc']==0x4552cd for row in replay_branch_events),
        actualAllFfffMarkerBranchObserved=any(row['pc']==0x45521b for row in replay_branch_events),
        markerHandlerCompletionObserved=False,finalStageEofWatchRotatesMainDr3OutsideLoading=True,
        sourceParentObserverSha256='PARENT_SHA',completeGame=False,nativeEquivalent=False)
""".replace('HELPER_SHA',SHA(helper)).replace('PARENT_SHA',SHA(parent))
 replace(marker,addition+marker)
 tree=ast.parse(text);writes=[n for n in ast.walk(tree)if isinstance(n,ast.Attribute)and n.attr=='WriteProcessMemory'];assert len(writes)==1
 assert 'SuspendThread'not in text and 'ResumeThread'not in text
 assert not out.exists();out.mkdir(parents=True);(out/'observer.py').write_bytes(text.encode())
 report=dict(prepared=True,observerSha256=SHA(text.encode()),parentObserverSha256=SHA(parent),embeddedCursorHelperSha256=SHA(helper),
  preparerSha256=SHA(Path(__file__).read_bytes()),sameEventClockPreserved=True,existingCameraStridePreserved=292,
  additionalCameraTailStride=8,replayCursorStride=56,all75CameraWordsPerPlayer=True,actualEofBranchWatchImplemented=True,
  originalGameStarted=False,productionSourcesChanged=False,completeGame=False,nativeEquivalent=False)
 (out/'prepared.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());return report


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to(R/'artifacts/th14');print(json.dumps(prepare(out)))
