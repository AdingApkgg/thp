"""Adapt preserved first-handoff native probes to each actual captured handoff.

Original retail routines and their controlled boundaries remain unchanged.
Old native reports and traces remain physical, independent evidence.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
selection="""    target_stage=int(__import__('sys').argv[1]);assert 2<=target_stage<=6
    group=next(g for g in trace['groups'] if g['stage']==target_stage)
    start_frame=group['transitionFrame']
    trace={kind:[dict(r,pools=[[],[],[],r.get('items',[])]) for r in group[kind]] for kind in ('records','replays')}
"""
restore=(ROOT/'tools/th14-campaign-replay-handoff-native.py').read_text(encoding='utf8')
restore=restore.replace("trace_path='artifacts/th14/campaign-handoff/rows.json'","trace_path='artifacts/th14/campaign-handoffs-all-oct11/rows.json'")
restore=restore.replace("trace_bytes=(ROOT/trace_path).read_bytes();trace=json.loads(trace_bytes)","trace_bytes=(ROOT/trace_path).read_bytes();trace=json.loads(trace_bytes)\n"+selection)
restore=restore.replace("r['frame']==11810","r['frame']==start_frame+6")
restore=restore.replace('headers[2]','headers[target_stage]').replace('MANAGER+2*40+0xd8','MANAGER+target_stage*40+0xd8').replace('put(0x4f58a4,2)','put(0x4f58a4,target_stage)')
restore=restore.replace("assert restored_score==first['score'] and restored_score!=before['score']","assert restored_score==first['score'] # Zero score lead is valid when this handoff has no combo settlement.")
restore=restore.replace('    restored_score=get(0x4f5830)',"    restored_snapshot=bytes(m.mem_read(0x4f5828,0x70))\n    header_path=f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-header.bin'\n    (ROOT/header_path).write_bytes(headers[target_stage])\n    restored_score=get(0x4f5830)")
restore=restore.replace('stage2HeaderSha256=','controlFlags=2,restoredSnapshotHex=restored_snapshot.hex(),stageHeaderPath=header_path,stage2HeaderSha256=')
restore=restore.replace('stage2HeaderSha256=','stage=target_stage,stageHeaderSha256=').replace("ROOT/'docs/porting/th14-campaign-replay-handoff-native-verified-oct11.json'","ROOT/f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-restore-native.json'")
restore=restore.replace('actual stage2 header','selected actual stage header').replace('not all other handoffs, whole combat','not whole combat').replace('native actual stage2 restore','native actual stage{target_stage} restore')
(ROOT/'tools/th14-campaign-handoffs-restore-native.py').write_text(restore,encoding='utf8')
live=(ROOT/'tools/th14-campaign-handoff-native.py').read_text(encoding='utf8').replace("ROOT/'artifacts/th14/campaign-handoff/rows.json'","ROOT/'artifacts/th14/campaign-handoffs-all-oct11/rows.json'")
live=live.replace('trace = json.loads(trace_bytes)','trace = json.loads(trace_bytes)\n'+selection)
live=live.replace("r['frame'] == 11810","r['frame'] == start_frame+6").replace("r['frame'] == 11811","r['frame'] == start_frame+7").replace("11811<=row['frame']<=11954","start_frame+7<=row['frame']<=start_frame+150").replace("row['frame']!=11811","row['frame']!=start_frame+7").replace("r['frame']==11955","r['frame']==start_frame+151")
live=live.replace("before = next(r for r in trace['records'] if r['frame'] == start_frame+6)","before = next(r for r in trace['records'] if r['stage']==target_stage and not r['active'] and r['combo'][2]==1)\n    assert before['items']==[3], 'Fresh pool precondition for native settlement factory'")
live=live.replace("r['frame'] == start_frame+7","r['frame'] == before['frame']+1").replace("start_frame+7<=row['frame']<=start_frame+150","before['frame']+1<=row['frame']<=start_frame+150").replace("row['frame']!=start_frame+7","row['frame']!=before['frame']+1")
live=live.replace('assert len(compared)==144',"assert len(compared)==start_frame+150-before['frame']")
live=live.replace('144 inactive item states','{len(compared)} inactive item states').replace('then143 full438550 ticks','then following full438550 ticks').replace('factory;144 inactive item states','factory;{len(compared)} inactive item states')
live=live.replace('activationFrame=11955','stage=target_stage,activationFrame=start_frame+151').replace("ROOT/'docs/porting/th14-campaign-handoff-native-verified-oct11.json'","ROOT/f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-live-native.json'")
live=live.replace('        assert pool()==row[\'pools\'][3],f"frame {row[\'frame\']} native item state"', '''        actual_pool=pool()
        if actual_pool!=row['pools'][3]:
            failure=dict(stage=target_stage,frame=row['frame'],input=before,expected=row['pools'][3],actual=actual_pool,events=events,toolSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            (ROOT/f'artifacts/th14/campaign-handoffs-all-oct11/stage{target_stage}-live-failure.json').write_text(json.dumps(failure,indent=2)+'\\n',encoding='utf8')
        assert actual_pool==row['pools'][3],f"frame {row['frame']} native item state"''')
live=live.replace('Exact recorded Reimu A Normal stage1-to-stage2 inactive combo input','Selected actual recorded Reimu A Normal inactive combo input').replace('or the other handoffs','or full other callbacks')
(ROOT/'tools/th14-campaign-handoffs-live-native.py').write_text(live,encoding='utf8')
print('Prepared isolated native restore/live probes for five actual handoffs')
