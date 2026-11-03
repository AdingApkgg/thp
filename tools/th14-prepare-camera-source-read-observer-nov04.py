"""Preserve controller events while observing camera publication and worker source reads."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
 parent=R/'tools/th14-prepare-camera-publication-write-observer-nov04.py'
 subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
 previous=(out/'prepared.json').read_bytes();prep=json.loads(previous);(out/'write-parent-prepared.json').write_bytes(previous)
 source=out/'observer.py';text=source.read_text(encoding='utf8');assert SHA(source.read_bytes())==prep['observerSha256']
 def replace(old,new,count=1):
  nonlocal text
  assert text.count(old)==count,(old,text.count(old));text=text.replace(old,new)
 replace('camera_right_write_count=0;latest_camera_right_write=None',
  'camera_right_write_count=0;latest_camera_right_write=None\ncamera_pub_pending=False;camera_source_read_tid=None;camera_source_reads=[]')
 replace('    if watch_camera_write:addresses[2]=0x4d9544',
  '''    if watch_camera_write:addresses[2]=0x4d9544
    if watch_camera_write and main_camera_phase=='update':
        addresses[1]=0x40dae9 if camera_pub_pending else 0x436bed
    watch_camera_read=opt.camera_write_events and tid==camera_source_read_tid and tid!=pi.tid and tid not in pending_worker_rng
    if watch_camera_read:addresses[2]=0x4d9544''')
 replace("    if watch_camera_write:struct.pack_into('<I',b,24,struct.unpack_from('<I',b,24)[0]|0xd000000)",
  "    if watch_camera_write:struct.pack_into('<I',b,24,struct.unpack_from('<I',b,24)[0]|0xd000000)\n    if watch_camera_read:struct.pack_into('<I',b,24,struct.unpack_from('<I',b,24)[0]|0xf000000)")
 replace('    global stage_object_vm_window_tid,stage_object_vm_active,stage_object_vm_closing_restore\n    if pc in store_signatures',
  '    global stage_object_vm_window_tid,stage_object_vm_active,stage_object_vm_closing_restore,camera_pub_pending,camera_source_read_tid\n    if pc==0x40dae9:camera_pub_pending=False\n    if pc in store_signatures')
 replace("            hud_score_pc[tid]=0x40d447",
  "            camera_source_read_tid=tid\n            hud_score_pc[tid]=0x40d447")
 replace("        elif pc==0x40d447:\n",
  "        elif pc==0x40d447:\n            camera_source_read_tid=None\n")
 replace("row.update(mainThreadPcAtWorkerEvent=struct.unpack_from('<I',main,184)[0],lastMainCameraRightWrite=latest_camera_right_write)",
  """row.update(mainThreadPcAtWorkerEvent=struct.unpack_from('<I',main,184)[0],lastMainCameraRightWrite=latest_camera_right_write,
                    mainThreadRegistersAtWorkerCameraEvent=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',main,156))),
                    worldCameraHexAtWorkerEvent=read(0x4d9514,300).hex())
                if pc==0x40d447:row['copiedCameraHex']=read(ebx+0x4274,300).hex()""",2)
 replace("if pc in targets or camera_write_hit or (serial_watch_manager",
  "camera_read_hit=opt.camera_write_events and ev.tid==camera_source_read_tid and ev.tid!=pi.tid and bool(struct.unpack_from('<I',b,20)[0]&4)and struct.unpack_from('<I',b,12)[0]==0x4d9544 and struct.unpack_from('<I',b,24)[0]&0xf000000==0xf000000\n                    if pc in targets or camera_write_hit or camera_read_hit or (serial_watch_manager")
 replace('                        if camera_write_hit:\n',
  '''                        if camera_read_hit:
                            assert pc==0x40d445 and read(pc,2)==bytes.fromhex('f3a5')
                            regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
                            copied=(regs['esi']-0x4d9514)//4;assert 13<=copied<=75 and regs['ecx']==75-copied
                            scene=regs['edi']-copied*4-0x4274
                            assert scene!=0x4d9514 and regs['ebx']==scene
                            main=context(threads[pi.tid]);main_regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',main,156)))
                            row=dict(event='worker-scene-camera-right-source-access',pc=pc,threadId=ev.tid,stage=u32(0x4f58a4),precedingPlayerCallbacks=callback_count,
                                hostMonotonicNs=time.monotonic_ns(),ordinal=len(camera_source_reads)+1,registers=regs,copiedDwords=copied,scene=scene,
                                copiedCameraHex=read(scene+0x4274,300).hex(),worldCameraHex=read(0x4d9514,300).hex(),
                                mainThreadRegisters=main_regs,lastMainCameraRightWrite=latest_camera_right_write,
                                hardwareReadWriteWatch=True,watchAddress=0x4d9544,readOnly=True,providedToEngine=False)
                            if main_regs['eip']==0x40dae7:
                                words=(main_regs['edi']-0x4d9514)//4;owner=main_regs['esi']-words*4-0x4274
                                row['mainPublicationRepProgress']=dict(owner=owner,copiedDwords=words,remainingDwords=main_regs['ecx'],
                                    sourceCameraHex=read(owner+0x4274,300).hex(),rawOwnerStageNumberWord=u32(owner+0x423c))
                            camera_source_reads.append(row)
                            with(home/'worker-camera-source-read-events.jsonl').open('a',encoding='utf8')as stream:stream.write(json.dumps(row)+'\\n')
                        elif camera_write_hit:
''')
 replace("                            if pc==0x40dae7:\n",
  "                            if pc==0x40dae7:\n                                camera_pub_pending=True\n")
 replace("rawOwnerPrefixHex=read(owner,32).hex(),dataWriteObserved=True,providedToEngine=False)",
  "rawOwnerPrefixHex=read(owner,32).hex(),rawOwnerStageNumberWord=u32(owner+0x423c),dataWriteObserved=True,providedToEngine=False)")
 marker="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
 replace(marker,"    report.update(cameraSourceReadEvents=len(camera_source_reads),cameraSourceReadEventsSha256=sha((home/'worker-camera-source-read-events.jsonl').read_bytes())if camera_source_reads else None,controllerSlotRotatesAfterObservedCameraWrite=True)\n"+marker)
 compile(text,str(source),'exec');source.write_bytes(text.encode())
 prep.update(preparerSha256=SHA(Path(__file__).read_bytes()),observerSha256=SHA(text.encode()),cameraReadParentPreparerSha256=SHA(parent.read_bytes()),cameraReadParentPreparationSha256=SHA(previous),controllerReadSlotPreservedByObservedWriteRotation=True,workerReadWatchOnlyBetweenSceneCopyBeforeAndAfter=True,workerCameraSourceReadValuesNotEngineInputs=True)
 (out/'prepared.json').write_bytes((json.dumps(prep,indent=2)+'\n').encode());print(json.dumps(prep),flush=True)
if __name__=='__main__':main()
