"""Compare actual Application outputs from the two native graphics backends.

By default both runs must be terminal successes. A running-prefix comparison
requires an explicit flag and never accepts the full flow or original imagery.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--allow-running-prefix',action='store_true')
    args=parser.parse_args();home=args.home.resolve();output=args.output.resolve()
    assert home.is_relative_to(ROOT/'artifacts/th14')
    assert output.is_relative_to(ROOT/'artifacts/th14')or output.is_relative_to(ROOT/'docs/porting')
    bindings={};runs={};actions={};captures={}
    def read(path):
        raw=path.read_bytes();bindings[path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=SHA(raw));return raw
    for backend in ['webgpu','gles']:
        folder=home/backend;report=folder/'report.json'
        if report.exists():
            run=json.loads(read(report));runs[backend]=run
            assert run['completed']and not run['error'],backend+' is a terminal failure, not an accepted pair'
            actions[backend]=run['actions'];captures[backend]={row['label']:row for row in run['captures']}
        else:
            assert args.allow_running_prefix,'A completed report is required without the explicit prefix flag'
            rows=[]
            for line in read(home/(backend+'-command.log')).decode('utf-8').splitlines():
                try:row=json.loads(line)
                except ValueError:continue
                if isinstance(row,dict)and {'frame','state','capture','pcmFrames','pendingCallbacks'}<=set(row):rows.append(row)
            actions[backend]=[dict(endFrame=row['frame'],state=row['state'])for row in rows]
            captures[backend]={row['capture']['label']:row['capture']for row in rows if row['capture']is not None}
    prefix=args.allow_running_prefix or len(runs)!=2
    if not prefix:
        assert runs['webgpu']['scenarioSha256']==runs['gles']['scenarioSha256']
        assert runs['webgpu']['toolSha256']==runs['gles']['toolSha256']
        assert runs['webgpu']['metadataEpochAtFrameZero']==runs['gles']['metadataEpochAtFrameZero']
        assert runs['webgpu']['frames']==runs['gles']['frames']
        assert runs['webgpu']['checks']==runs['gles']['checks']
    shared_actions=min(len(rows)for rows in actions.values());state_differences=[]
    for index in range(shared_actions):
        left,right=actions['webgpu'][index],actions['gles'][index]
        if (left['endFrame'],left['state'])!=(right['endFrame'],right['state']):
            state_differences.append(dict(action=index,webgpu=dict(frame=left['endFrame'],state=left['state']),gles=dict(frame=right['endFrame'],state=right['state'])))
    labels=[name for name in captures['webgpu']if name in captures['gles']];assert labels
    pairs=[]
    for label in labels:
        buffers=[];frames=[]
        for backend in ['webgpu','gles']:
            row=captures[backend][label];assert Path(row['file']).name==row['file']
            raw=read(home/backend/row['file']);assert len(raw)==640*480*4 and SHA(raw)==row['sha256']
            buffers.append(raw);frames.append(row['frame'])
        assert frames[0]==frames[1],label+' is not the same Application frame'
        indices=[index for index,(left,right)in enumerate(zip(*buffers))if left!=right]
        first=indices[0]if indices else None
        pairs.append(dict(label=label,frame=frames[0],bytes=len(buffers[0]),differentBytes=len(indices),
            differentPixels=len({index//4 for index in indices}),firstDifference=None if first is None else
            dict(x=first//4%640,y=first//4//640,channel='BGRA'[first%4],webgpu=buffers[0][first],gles=buffers[1][first])))
    all_buffers=all(row['differentBytes']==0 for row in pairs);same_states=not state_differences
    if not prefix:
        assert len(actions['webgpu'])==len(actions['gles'])
        assert set(captures['webgpu'])==set(captures['gles'])
        pcm=dict(framesEqual=runs['webgpu']['pcmFrames']==runs['gles']['pcmFrames'],
            reportedHashEqual=runs['webgpu']['pcmSha256']==runs['gles']['pcmSha256'])
        assert runs['webgpu']['rows']==runs['gles']['rows'],'Full journal state differs'
        assert all(pcm.values()),'Actual silent PCM sink hashes differ'
        pcm.update(framesPerBackend=runs['webgpu']['pcmFrames'],reportedSha256=runs['webgpu']['pcmSha256'],rawPcmIndependentlyRetained=False)
    else:pcm=None
    result=dict(schema='th14/application-native-render-pair/1',runningPrefixOnly=prefix,
        completedRuns=sorted(runs),sharedCompletedActions=shared_actions,pairedImages=len(pairs),
        framesPerBackend=None if prefix else runs['webgpu']['frames'],
        assertionsPerBackend=None if prefix else len(runs['webgpu']['checks']),
        pairedJournalRows=None if prefix else len(runs['webgpu']['rows']),
        comparedImageBytes=sum(row['bytes']for row in pairs),pairs=pairs,
        allPairedCapturedBuffersEqual=all_buffers,allSharedActionStatesEqual=same_states,stateDifferences=state_differences,
        silentPcmSinkComparison=pcm,fullFlowAccepted=False,originalApplicationPixelsEqualNotAsserted=True,
        browserAcceptance=False,completeGame=False,nativeEquivalent=False,
        verifierSha256=SHA(Path(__file__).read_bytes()),bindings=bindings,
        scope='Byte comparison of retained actual C++ Application images and action states between native WebGPU and GLES. An explicit running prefix is limited to the common completed captures. Each full-flow and original-image claim still needs separate authoritative evidence.')
    assert all_buffers and same_states,'Retained native backend differences; do not waive pixels or state'
    if args.check:assert json.loads(output.read_bytes())==result
    else:
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['runningPrefixOnly','sharedCompletedActions','pairedImages','comparedImageBytes','allPairedCapturedBuffersEqual','allSharedActionStatesEqual']}))


if __name__=='__main__':main()
