"""Causal component control using observed original resource availability.

Only the standalone test host's callback delivery changes. The profile comes
from original hardware observations, never VM/pixel expectations. This is not a
production timing policy, physical scheduling reproduction or game acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','baseline-command','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();home=a.output.resolve();native=a.native.resolve(strict=True)
    assert home.is_relative_to(ROOT/'artifacts/th14')and not home.exists()
    assert native.is_relative_to(ROOT/'artifacts/th14')
    raw=(native/'report.json').read_bytes();r=json.loads(raw)
    assert r['childExited']and r['frameReadbackCompleted']and not r['error']
    assert r['originalCodeWrites']==r['gameStateWrites']==0 and not r['inputInjection']
    assert r['inlineEclAnmBoundariesComplete']and r['stageWorkerBoundariesComplete']
    assert r['sourceSha256']==SHA((native/'run-tool.py').read_bytes())
    before=next(x for x in r['stageWorkerBoundaries']if x['pc']==0x435e17)
    player=next(x for x in r['stageWorkerBoundaries']if x['pc']==0x435e22)
    assert not before['optionVms']and len(player['optionVms'])==4
    assert all(x['ageCurrent']==1 for x in player['optionVms'])
    origin=player['precedingPresentEntries'];first={};order=[]
    for row in r['mainResourcePumpEntries']:
        for slot in row['slots']:
            file=slot['file'];cursor=slot['words128Through134'][0]
            if cursor and file!=9 and row['precedingPresentEntries']>=origin and file not in first:
                assert cursor==1
                first[file]=row['precedingPresentEntries'];order.append(file)
    assert order and len(order)<=8
    profile=dict(schema='th14/observed-initial-resource-availability/1',
        nativeReport=dict(path=str((native/'report.json').relative_to(ROOT)),sha256=SHA(raw)),
        sourceToolSha256=SHA(Path(__file__).read_bytes()),
        originalPlayerConstructionPresent=origin,
        deliveries=[dict(resourceFile=file,mainPumpOffsetFromPlayer=first[file]-origin)for file in order],
        timebase='Original main resource pump Present-entry offsets, mapped to fixed component frame starts',
        hardwareObservationPerturbsScheduling=True,physicalCpuDurationsReproduced=False,
        noVmRngPixelOrGameStateOverrides=True,productionSchedulingChanged=False,
        completeGame=False,nativeEquivalent=False)
    home.mkdir(parents=True);profile_path=home/'availability.json'
    profile_raw=(json.dumps(profile,indent=2)+'\n').encode();profile_path.write_bytes(profile_raw)
    source=ROOT/'tools/th14-native-application-process-host-oct27.py';code=source.read_text()
    def replace(before,after):
        nonlocal code
        assert code.count(before)==1,before
        code=code.replace(before,after)
    replace('R=Path(__file__).resolve().parents[1]',f'R=Path({str(ROOT)!r})')
    replace('    due,_,function,argument=heapq.heappop(callbacks)',
        '    due,callback_sequence,function,argument=heapq.heappop(callbacks)')
    replace(' frame_index=0;wall_started=time.monotonic();actions=[];captures=[];application_ticks=0',
        f''' availability_profile=json.loads(Path({str(profile_path)!r}).read_bytes())
 availability_anchor=None;availability_events=[];availability_seen=set()
 frame_index=0;wall_started=time.monotonic();actions=[];captures=[];application_ticks=0''')
    replace('    clock_ns=due\n    paused_this_callback=False',
        '''    observed_before=initial_loading_state()
    if availability_anchor is not None and observed_before[0]==6 and observed_before[1]==3 and observed_before[12] and observed_before[3] and observed_before[5]==1:
     index=observed_before[7]-1
     if 0<=index<len(availability_profile['deliveries']):
      entry=availability_profile['deliveries'][index]
      ready_frame=availability_anchor+entry['mainPumpOffsetFromPlayer']
      ready_ns=ready_frame*1000000000//60
      if index not in availability_seen:
       availability_seen.add(index)
       availability_events.append(dict(index=index,resourceFile=entry['resourceFile'],requestedFrame=frame_index,originalDueNs=due,observedReadyFrame=ready_frame,observedReadyNs=ready_ns))
      if due<ready_ns:
       heapq.heappush(callbacks,(ready_ns,callback_sequence,function,argument));continue
    clock_ns=due
    paused_this_callback=False''')
    replace("    observe_initial_loading('callback')",'''    observe_initial_loading('callback')
    observed_after=initial_loading_state()
    if availability_anchor is None and not observed_before[11] and observed_after[11] and observed_after[12]:
     availability_anchor=frame_index''')
    replace("  result['applicationTicks']=application_ticks",'''  result['applicationTicks']=application_ticks
  result['observedResourceAvailabilityControl']=dict(profile=availability_profile,
   anchorFrame=availability_anchor,events=availability_events,
   standaloneCallbackDeliveryOnly=True,productionSchedulingChanged=False,
   gameStateAndRngNeverReplaced=True,notPhysicalSchedulingAcceptance=True)''')
    replace(" api['component_audio_close'](store);completed=True;report()",''' assert availability_anchor is not None and len(availability_seen)==len(availability_profile['deliveries'])
 api['component_audio_close'](store);completed=True;report()''')
    private_host=home/'host.py';compile(code,str(private_host),'exec');private_host.write_text(code,encoding='utf8')
    cmd=json.loads(a.baseline_command.read_bytes());assert str(source)in cmd
    assert '--observe-initial-loading'in cmd and '--initial-worker-pause-kind'not in cmd
    cmd[cmd.index(str(source))]=str(private_host)
    cmd[cmd.index('--output')+1]=str(home/'run')
    (home/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    (home/'preparation.json').write_text(json.dumps(dict(sourceHostSha256=SHA(source.read_bytes()),
        profileSha256=SHA(profile_raw),privateHostSha256=SHA(private_host.read_bytes()),
        originalCodeWrites=0,productionSourcesChanged=False,completeGame=False,nativeEquivalent=False),indent=2)+'\n')
    raise SystemExit(subprocess.call(cmd,cwd=ROOT))


if __name__=='__main__':main()
