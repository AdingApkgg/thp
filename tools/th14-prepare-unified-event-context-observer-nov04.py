"""Prepare a bounded original observer with one clock per received debug event."""
from pathlib import Path
import argparse,hashlib,importlib,json,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();O=a.output.resolve();assert O.is_relative_to(R/'artifacts/th14')and not O.exists()
 parent=R/'tools/th14-prepare-camera-source-read-observer-nov04.py'
 subprocess.run([sys.executable,'-X','utf8',str(parent),'--output',str(O)],cwd=R,capture_output=True,check=True)
 prior=(O/'prepared.json').read_bytes();prep=json.loads(prior);(O/'camera-read-parent-prepared.json').write_bytes(prior);source=O/'observer.py';text=source.read_text();assert SHA(source.read_bytes())==prep['observerSha256']
 sys.path.insert(0,str(R/'tools'));dll=importlib.import_module('th12-pe').Image('C:/Windows/SysWOW64/d3dx9_43.dll')
 assert SHA(dll.data)=='0b28546be22c71834501f7d7185ede5d79742457331c7ee09efc14490dd64f5f'
 pe=struct.unpack_from('<I',dll.data,0x3c)[0];export_dir=dll.image_base+struct.unpack_from('<I',dll.data,pe+0x78)[0]
 funcs,names,ords=[dll.image_base+dll.u32(export_dir+off)for off in(28,32,36)];export_rva=None
 for i in range(dll.u32(export_dir+24)):
  name=dll.read(dll.image_base+dll.u32(names+i*4),128).split(b'\0')[0].decode()
  if name=='D3DXVec3Normalize':export_rva=dll.u32(funcs+struct.unpack('<H',dll.read(ords+i*2,2))[0]*4)
 assert export_rva is not None;image_size=struct.unpack_from('<I',dll.data,pe+0x50)[0]
 def replace(old,new,count=1):
  nonlocal text
  assert text.count(old)==count,(old,text.count(old));text=text.replace(old,new)
 clock_calls=text.count('time.monotonic_ns()');assert clock_calls>=20
 text=text.replace('time.monotonic_ns()','observation_clock_ns()')
 replace('choices=(64,256,512)','choices=(64,256,512,1024,2048)')
 marker='stage_object_vm_window_tid=None;stage_object_vm_active=None;stage_object_vm_closing_restore=None;stage_object_vm_events=[]'
 helper="""
debug_event_sequence=0;debug_event_receipt_ns=0;debug_event_clock_active=False;debug_event_clock_rows=0
def observation_clock_ns():
    return debug_event_receipt_ns if debug_event_clock_active else time.monotonic_ns()
def event_json(row):
    if debug_event_clock_active:
        row.setdefault('debugEventSequence',debug_event_sequence)
        row.setdefault('debugEventReceiptHostNs',debug_event_receipt_ns)
        row.setdefault('hostClockSharedAtDebugEventReceipt',True)
        if 'hostMonotonicNs'in row:assert row['hostMonotonicNs']==debug_event_receipt_ns
    return json.dumps(row)
def d3dx_context_metadata(registers):
    target=u32(0x4b12b8);base=target-D3DX_NORMALIZE_EXPORT_RVA
    result=dict(normalizeImportAddress=target,expectedNormalizeExportRva=D3DX_NORMALIZE_EXPORT_RVA,
        candidateModuleBase=base,readOnly=True,originalInstructionBytesPatched=False)
    try:
        result['candidateHasMzHeader']=read(base,2)==b'MZ'
        if result['candidateHasMzHeader']:
            header=read(base,0x1000);offset=struct.unpack_from('<I',header,0x3c)[0]
            result['modulePeSignatureMatches']=header[offset:offset+4]==b'PE\\0\\0'
            result['moduleImageSize']=struct.unpack_from('<I',header,offset+0x50)[0]
            result['moduleTimestamp']=struct.unpack_from('<I',header,offset+8)[0]
            pc=registers['eip'];rva=pc-base
            if 0<=rva<D3DX_IMAGE_SIZE:result.update(mainPcWithinCandidateD3dx=True,mainPcRva=rva,mainInstructionHex=read(pc,16).hex())
    except(OSError,AssertionError,struct.error)as exc:result['diagnosticReadError']=repr(exc)
    return result
"""
 helper='\nD3DX_NORMALIZE_EXPORT_RVA='+repr(export_rva)+';D3DX_IMAGE_SIZE='+repr(image_size)+'\n'+helper
 replace(marker,marker+helper)
 json_rows=text.count('json.dumps(row)');assert json_rows>10
 # Keep the new serializer's final call as JSON itself, replace preexisting row writers.
 head,tail=text.split('def event_json(row):',1);fn_end=tail.index('def d3dx_context_metadata')
 tail=tail[:fn_end]+tail[fn_end:].replace('json.dumps(row)','event_json(row)')
 text=head.replace('json.dumps(row)','event_json(row)')+'def event_json(row):'+tail
 replace('        status=0x10002\n        try:','        debug_event_sequence+=1;debug_event_receipt_ns=time.monotonic_ns();debug_event_clock_active=True\n        status=0x10002\n        try:')
 replace('        finally:checked(k.ContinueDebugEvent(ev.pid,ev.tid,status))','        finally:\n            debug_event_clock_active=False\n            checked(k.ContinueDebugEvent(ev.pid,ev.tid,status))')
 marker="                    b=context(threads[ev.tid]);pc=struct.unpack_from('<I',b,184)[0]"
 journal="""
                    clock_row=dict(debugEventSequence=debug_event_sequence,hostMonotonicNs=debug_event_receipt_ns,
                        threadId=ev.tid,pc=pc,exceptionAddress=int(x.address),exceptionCode=int(x.code),
                        precedingPlayerCallbacks=callback_count,debugStatus=struct.unpack_from('<I',b,20)[0],
                        receiptClockNotOriginalInstructionExecutionTime=True)
                    with(home/'debug-event-clock.jsonl').open('a',encoding='utf8')as clock_stream:clock_stream.write(event_json(clock_row)+'\\n')
                    debug_event_clock_rows+=1
"""
 replace(marker,marker+journal.rstrip())
 replace("    row['stageObjectVmCallAtWorkerStore']=dict(observedCall=stage_object_vm_active,","    row['mainThreadD3dxAtWorkerStore']=d3dx_context_metadata(main_regs)\n    row['stageObjectVmCallAtWorkerStore']=dict(observedCall=stage_object_vm_active,")
 replace("                                mainThreadRegisters=main_regs,lastMainCameraRightWrite=latest_camera_right_write,","                                mainThreadRegisters=main_regs,mainThreadD3dx=d3dx_context_metadata(main_regs),lastMainCameraRightWrite=latest_camera_right_write,")
 marker="    (home/'report.json').write_text(json.dumps(report,indent=2)+'\\n');print("
 replace(marker,"    report.update(debugEventReceiptClockShared=True,debugEventClockRows=debug_event_clock_rows,debugEventClockSha256=sha((home/'debug-event-clock.jsonl').read_bytes()),maxMainStackCaptureBytes=opt.worker_main_stack_bytes,d3dxNormalizeExportRva=D3DX_NORMALIZE_EXPORT_RVA,d3dxExpectedImageSize=D3DX_IMAGE_SIZE,oldRecordingExactScheduleRecovered=False)\n"+marker)
 compile(text,str(source),'exec');assert 'SuspendThread'not in text and 'ResumeThread'not in text
 source.write_bytes(text.encode())
 prep.update(preparerSha256=SHA(Path(__file__).read_bytes()),observerSha256=SHA(text.encode()),sharedClockParentPreparerSha256=SHA(parent.read_bytes()),sharedClockParentPreparationSha256=SHA(prior),sameReceivedDebugEventUsesOneClock=True,clockRowsCarryDebugEventSequence=True,originalMonotonicClockCallSitesReplaced=clock_calls,maximumStackCaptureChoiceBytes=2048,nativeD3dxSha256=SHA(dll.data),d3dxNormalizeExportRva=export_rva,d3dxImageSize=image_size,rootProductionSourcesModified=False,oldFailureClosed=False)
 (O/'prepared.json').write_bytes((json.dumps(prep,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in prep.items()if k not in('baseObserver',)},indent=2))
if __name__=='__main__':main()
