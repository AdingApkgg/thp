"""Compare two retained originals without conflating observation profiles or boot inputs."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];H=R/'artifacts/th14/original-pair-audit-nov05'
SHA=lambda data:hashlib.sha256(data).hexdigest();bindings={}

def raw(path):
    path=path.resolve();assert path.is_relative_to(R)
    data=path.read_bytes();bindings[path.relative_to(R).as_posix()]=dict(bytes=len(data),sha256=SHA(data));return data

def main():
    homes=[R/'artifacts/th14/script-rng-read-generation-nov05/prefix-player-pump/native',
        R/'artifacts/th14/supervisor-pass-rng-nov05/prefix-fixed-startup-retry1/native']
    reports=[];arrays=[];initial=[]
    for home in homes:
        report=json.loads(raw(home/'report.json'));data=raw(home/'selected-state.u32')
        assert SHA(data)==report['selectedSha256']and len(data)==report['callbacks']*128
        assert report['childExited']and not report['error']and not report['debugErrors']
        assert report['instructionBytesPatched']==report['rngOrCounterWrites']==0
        assert report['hardwareBreakpointsOnly']and not report['inputInjected']
        assert report['gameStateWordWrites']==1 and report['caseInitialization']['attractBitClearOnly']
        reports.append(report);arrays.append(list(struct.iter_unpack('<32I',data)))
        initial.append(json.loads(raw(home/'untouched-first-player.json')))
    for key in ['sourceFullReplaySha256','executableSha256','referenceArchiveManifestSha256']:
        assert reports[0][key]==reports[1][key]
    assert reports[0]['sourceFullReplaySha256']=='c48412a95f0fe9f685d97574e8ab0655d41e44ff9c41fda7bf788589b1b29c74'
    assert reports[0]['executableSha256']=='f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'
    assert reports[0]['sourceSha256']!=reports[1]['sourceSha256']
    lookup=[];duplicates=[]
    for rows in arrays:
        groups=defaultdict(list)
        for index,row in enumerate(rows):groups[(row[30],row[0])].append((index,row))
        lookup.append({key:items[0]for key,items in groups.items()if len(items)==1})
        duplicates.append(sum(len(items)for items in groups.values()if len(items)!=1))
    keys=sorted(lookup[0].keys()&lookup[1].keys());counts=Counter();first={};shots=[]
    stages=defaultdict(lambda:dict(paired=0,fieldDifferences=Counter()))
    for key in keys:
        (a,x),(b,y)=lookup[0][key],lookup[1][key];stages[key[0]]['paired']+=1
        for field,(u,v)in enumerate(zip(x,y)):
            if u!=v:
                counts[field]+=1;stages[key[0]]['fieldDifferences'][field]+=1
                first.setdefault(field,dict(stage=key[0],stageFrame=key[1],callbackA=a+1,callbackB=b+1))
        if x[26]!=y[26]:shots.append(dict(stage=key[0],stageFrame=key[1],callbackA=a+1,callbackB=b+1,countA=x[26],countB=y[26]))
    assert len(keys)==34429 and duplicates==[415,571]
    assert dict(counts)=={21:34428,22:34429,26:9}
    result=dict(schema='th14/retained-original-pair-audit/2',
        sameExeAndIntactReplayAndArchiveManifest=True,sourceReplaySha256=reports[0]['sourceFullReplaySha256'],
        originalCallbacks=[len(rows)for rows in arrays],observerProfilesDiffer=True,
        initialTimeInputsEqual=initial[0]['actualInitialTimeGetTimeInput']==initial[1]['actualInitialTimeGetTimeInput'],
        initialSecurityCookiesEqual=initial[0]['actualOriginalSecurityCookie']==initial[1]['actualOriginalSecurityCookie'],
        ordinaryGuiNondeterminismProven=False,uniqueStageFramePairs=len(keys),duplicateKeyRowsExcluded=duplicates,
        unpairedUniqueKeys=[len(rows)-len(keys)for rows in lookup],fieldDifferenceCounts=dict(counts),
        fieldRoles={'21':'script RNG seed','22':'script RNG calls','23':'gameplay RNG seed','24':'gameplay RNG calls','26':'active player shots'},
        firstDifferences=first,activeShotDifferences=shots,stageSummary=dict(stages),
        allOtherSelectedFieldsEqual=True,gameplayRngSeedAndCallsEqualAtEveryUniquePair=True,
        bootInputsNotControlledBetweenOriginals=True,observedDifferencesNotAutomaticallyEngineDefects=True,
        fullEquivalenceClaim=False,completeGame=False,evidenceBindings=bindings,
        toolSha256=SHA(Path(__file__).read_bytes()))
    assert not result['initialTimeInputsEqual']and not result['initialSecurityCookiesEqual']
    (H/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key]for key in ['uniqueStageFramePairs','fieldDifferenceCounts','activeShotDifferences','bootInputsNotControlledBetweenOriginals','completeGame']}))

if __name__=='__main__':main()
