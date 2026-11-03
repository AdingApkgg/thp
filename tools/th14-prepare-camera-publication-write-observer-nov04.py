"""Watch camera right.x writes in both update and draw, preserving actual REP progress."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(R/'artifacts/th14')and not out.exists()
 parent=R/'tools/th14-prepare-replay-rng-completion-stage-observer-nov04.py';subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(out)],cwd=R,check=True,capture_output=True)
 prior=(out/'prepared.json').read_bytes();prepared=json.loads(prior);(out/'completion-parent-prepared.json').write_bytes(prior);source=out/'observer.py';text=source.read_text(encoding='utf8');assert sha(source.read_bytes())==prepared['observerSha256']
 old="watch_camera_write=first_snapshot is not None and not trace_publications and tid==pi.tid and transition_trace and opt.camera_write_events and main_camera_phase=='draw'";assert text.count(old)==1
 text=text.replace(old,"watch_camera_write=first_snapshot is not None and not trace_publications and tid==pi.tid and transition_trace and opt.camera_write_events and stage_object_vm_window_tid is None")
 old='assert not opt.stage_object_vm_window_events or (opt.worker_rng_events and opt.worker_main_context and not opt.camera_write_events)';assert text.count(old)==1
 text=text.replace(old,'assert opt.stage_object_vm_window_events and opt.worker_rng_events and opt.worker_main_context and opt.camera_write_events')
 marker='                            latest_camera_right_write=row';assert text.count(marker)==1
 extra="""                            regs=dict(zip(['edi','esi','ebx','edx','ecx','eax','ebp','eip','cs','eflags','esp'],struct.unpack_from('<11I',b,156)))
                            row['registers']=regs;row['originalBytesAtPc']=read(pc,8).hex()
                            row['debugRegisters']=dict(addresses=list(struct.unpack_from('<4I',b,4)),status=struct.unpack_from('<I',b,20)[0],control=struct.unpack_from('<I',b,24)[0])
                            if pc==0x40dae7:
                                assert read(pc,2)==bytes.fromhex('f3a5')
                                owner=regs['esi']-(regs['edi']-0x4d9514)-0x4274
                                row['mainPublicationRepProgress']=dict(owner=owner,remainingDwords=regs['ecx'],sourcePointer=regs['esi'],destinationPointer=regs['edi'],
                                    publicationEventPc=0x40dae9,sourceCameraHex=read(owner+0x4274,300).hex(),worldCameraHex=read(0x4d9514,300).hex(),
                                    rawOwnerPrefixHex=read(owner,32).hex(),dataWriteObserved=True,providedToEngine=False)
"""
 text=text.replace(marker,extra+marker);compile(text,str(source),'exec');source.write_bytes(text.encode())
 prepared.update(observerSha256=sha(text.encode()),preparerSha256=sha(Path(__file__).read_bytes()),cameraWriteParentPreparerSha256=sha(parent.read_bytes()),cameraRightDataWriteWatchIncludesUpdate=True,stageVmReturnWatchNotOverwritten=True,actualRepRegistersCaptured=True,originalInstructionsPatched=False,nativeValuesProvidedToEngine=False)
 (out/'prepared.json').write_bytes((json.dumps(prepared,indent=2)+'\n').encode());print(json.dumps(prepared),flush=True)
if __name__=='__main__':main()
