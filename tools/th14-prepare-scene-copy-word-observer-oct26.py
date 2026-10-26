"""Prepare a frozen observer with destination watches and bounded TF copy stepping.

The existing versioned campaign observer remains unchanged. The generated source
adds read-only word-copy observations and a declared prefix stop, without input,
code, RNG, counter, health or native camera-value injection.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    source_path=ROOT/'tools/th14-native-campaign-observer-oct25.py';raw=source_path.read_bytes();source=raw.decode().replace('\r\n','\n')
    # The composition is also bound by exact replacement counts below.
    patches=[]
    def replace(old,new,label):
        nonlocal source
        assert source.count(old)==1,label+' base observer structure changed'
        source=source.replace(old,new);patches.append(label)
    replace('root=Path(__file__).resolve().parents[1]', 'root=Path('+repr(str(ROOT))+')','workspaceRoot')
    replace('opt=parser.parse_args()',"parser.add_argument('--scene-copy-word-events',action='store_true',help='Three read-only worker destination data watches during the original75-dword Scene copy; diagnostic prefix only')\nopt=parser.parse_args()\nassert opt.scene_copy_word_events and opt.scene_camera_events and opt.controller_phase_events",'declaredOption')
    replace('pending_worker_rng=set()', 'pending_worker_rng=set()\nscene_copy_word_watches={}\nscene_copy_word_events=[]\nscene_copy_modules=[]\nscene_copy_step_owned=set()','wordEventStorage')
    replace("    if first_snapshot is None and tid==pi.tid and not ascii_create_invocations:addresses[0]=0x44477a",
        "    if first_snapshot is None and tid==pi.tid and not ascii_create_invocations:addresses[0]=0x44477a\n    copy_watch=scene_copy_word_watches.get(tid)\n    if copy_watch:\n        assert tid!=pi.tid and opt.scene_copy_word_events\n        addresses=[copy_watch['destination']+4*lane for lane in range(3)]+[0x40d447]",'wordWatchAddresses')
    replace('    if current:struct.pack_into',"    if copy_watch:\n        struct.pack_into('<I',b,24,0x55|0x0ddd0000)\n        struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]|0x100);scene_copy_step_owned.add(tid)\n    elif tid in scene_copy_step_owned:\n        struct.pack_into('<I',b,192,struct.unpack_from('<I',b,192)[0]&~0x100);scene_copy_step_owned.remove(tid)\n    if current:struct.pack_into",'wordWatchAndTrapControl')
    replace('            hud_score_pc[tid]=0x40d447', "            assert tid!=pi.tid and tid not in scene_copy_word_watches\n            scene_copy_word_watches[tid]=dict(scene=ebx,destination=ebx+0x42a4,stage=row['stage'],lanes=[],copiedWords=0,steps=0)\n            hud_score_pc[tid]=0x40d447",'beginWordWatch')
    replace('            scene_camera_copies.append(row);hud_score_pc[tid]=0x43605a',
        "            watch=scene_copy_word_watches.pop(tid)\n            assert watch['scene']==ebx and watch['lanes']==[0,1,2]and watch['copiedWords']==75\n            row.update(threeDestinationWordsObservedDirectly=True,originalRepCopiedWords=watch['copiedWords'],originalCopyStepEvents=watch['steps'])\n            scene_camera_copies.append(row);hud_score_pc[tid]=0x43605a",'finishWordWatch')
    old="                    if pc in targets or camera_write_hit or (serial_watch_manager"
    new="                    scene_copy_word_hit=ev.tid in scene_copy_word_watches and bool(struct.unpack_from('<I',b,20)[0]&(7|0x4000))\n                    if pc in targets or camera_write_hit or scene_copy_word_hit or (serial_watch_manager"
    replace(old,new,'dispatchWordWatch')
    code="""                        if scene_copy_word_hit:
                            watch=scene_copy_word_watches[ev.tid];dr=struct.unpack_from('<6I',b,4);bits=dr[4]&7
                            regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
                            main=context(threads[pi.tid]);main_regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',main,156)))
                            step=dict(workerPc=pc,threadId=ev.tid,hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,
                                scene=watch['scene'],debugRegisters=dict(zip(['dr0','dr1','dr2','dr3','dr6','dr7'],dr)),workerRegisters=regs,mainThreadRegisters=main_regs,
                                previousCopiedWords=watch['copiedWords'],readOnly=True)
                            with(home/'scene-camera-copy-step-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(step)+'\\n')
                            watch['steps']+=1;assert watch['steps']<=80
                            assert pc in(0x40d43a,0x40d43f,0x40d445,0x40d447)
                            assert dr[4]&0x4000,'Exact TF step required; grouped data traps cannot supply missing word times'
                            if pc in(0x40d445,0x40d447):
                                copied=75-regs['ecx'];assert 0<=copied<=75
                                assert regs['esi']==0x4d9514+4*copied and regs['edi']==watch['destination']-0x30+4*copied
                                assert copied-watch['copiedWords']in(0,1),'Grouped REP iterations are retained failures, not split into inferred events'
                                previous=watch['copiedWords'];watch['copiedWords']=copied
                                if copied!=previous and 13<=copied<=15:
                                    lane=copied-13;assert lane==len(watch['lanes']);watch['lanes'].append(lane)
                                else:lane=None
                            else:lane=None
                            if lane is None:
                                if pc==0x40d447:event_snapshot(pc,ev.tid,b)
                                install(ev.tid,current=True)
                                continue
                            module=next((mod for mod in scene_copy_modules if mod['base']<=main_regs['eip']<mod['base']+mod['imageBytes']),None)
                            row=dict(event='scene-camera-right-word-copied',word=lane,workerPc=pc,threadId=ev.tid,
                                hostMonotonicNs=time.monotonic_ns(),precedingPlayerCallbacks=callback_count,stage=u32(0x4f58a4),
                                scene=watch['scene'],destination=watch['destination']+4*lane,workerRegisters=regs,debugRegisters=step['debugRegisters'],
                                copiedWordHex=read(watch['destination']+4*lane,4).hex(),
                                sourceRightHex=read(0x4d9544,12).hex(),destinationRightHex=read(watch['destination'],12).hex(),
                                mainThreadRegisters=main_regs,mainThreadStackHex=read(main_regs['esp'],64).hex(),
                                mainModule=module,mainModuleRva=None if module is None else main_regs['eip']-module['base'],
                                lastMainCameraBoundary=latest_camera_boundary,readOnly=True,hardwareDataWrite=True,
                                actualOriginalRepIterationObserved=True,exactTrapFlagStep=True,nativeValuesProvidedToEngine=False)
                            scene_copy_word_events.append(row)
                            with(home/'scene-camera-word-copy-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\\n')
                        elif camera_write_hit:"""
    replace('                        if camera_write_hit:',code,'wordReadOnlyCapture')
    dll_code="""            elif ev.kind==6:
                if ev.data.dll.file:
                    name=C.create_unicode_buffer(4096)
                    getter=k.GetFinalPathNameByHandleW;getter.argtypes=[W.HANDLE,W.LPWSTR,W.DWORD,W.DWORD];getter.restype=W.DWORD
                    length=getter(ev.data.dll.file,name,len(name),0)
                    if 0<length<len(name) and name.value.lower().endswith('d3dx9_43.dll'):
                        dll_path=Path(name.value);dll_raw=dll_path.read_bytes()
                        assert sha(dll_raw)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
                        pe=struct.unpack_from('<I',dll_raw,0x3c)[0];image_size=struct.unpack_from('<I',dll_raw,pe+0x50)[0]
                        scene_copy_modules.append(dict(name='d3dx9_43.dll',base=int(ev.data.dll.base),imageBytes=image_size,sha256=sha(dll_raw)))
                        (home/'scene-copy-modules.json').write_text(json.dumps(scene_copy_modules,indent=2)+'\\n')
                    k.CloseHandle(ev.data.dll.file)"""
    replace('            elif ev.kind==6:\n                if ev.data.dll.file:k.CloseHandle(ev.data.dll.file)',dll_code,'loadedD3dxIdentity')
    replace('diagnosticPrefixOnly=False,asciiBeginObserved', 'diagnosticPrefixOnly=True,asciiBeginObserved','prefixScope')
    replace('hardwareBreakpointsOnly=True,instructionBytesPatched=0', 'hardwareBreakpointsOnly=False,hardwareDebugRegistersAndTrapFlagOnly=True,instructionBytesPatched=0','hardwareTrapScope')
    replace("    (home/'report.json').write_text", "    report.update(sceneCopyWordEvents=len(scene_copy_word_events),sceneCopyWordEventsSha256=sha((home/'scene-camera-word-copy-events.jsonl').read_bytes())if(home/'scene-camera-word-copy-events.jsonl').exists()else None,sceneCopyWordModules=scene_copy_modules,sceneCopyWordObserversRemaining=len(scene_copy_word_watches),diagnosticStopReason='maximumCallbacks'if callback_count>=opt.maximum_callbacks else 'naturalEnd'if complete else 'errorOrBudget',fullReplayAccepted=False)\n    (home/'report.json').write_text",'wordReportBindings')
    replace('if error or not complete:raise SystemExit(1)', 'if error or (not complete and callback_count<opt.maximum_callbacks):raise SystemExit(1)','declaredPrefixExit')
    ast.parse(source)
    out.mkdir();generated=source.encode();(out/'observer.py').write_bytes(generated)
    receipt=dict(baseObserverPath=source_path.relative_to(ROOT).as_posix(),baseObserverSha256=SHA(raw),
        generatedObserverSha256=SHA(generated),preparerSha256=SHA(Path(__file__).read_bytes()),exactCompositionSteps=patches,
        diagnosticPrefixOnly=True,originalProcessLaunched=False,threeWorkerDestinationWordWatches=True,originalCopyTrapFlagStepping=True,
        changedOriginalInstructions=False,nativeValuesProvidedToEngine=False,completeGame=False,nativeEquivalent=False)
    (out/'prepared.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
