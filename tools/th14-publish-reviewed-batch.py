"""Publish a hash-reviewed TH14 source/metadata plan and its existing progress PR.

One invocation groups the authorized GitHub operations. Raw evidence and assets
are never included. The plan is prepared locally before networking is requested.
"""
from pathlib import Path
import argparse,ast,base64,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];GH=R/'tools/tmp/ghcli/bin/gh.exe'
SHA=lambda data:hashlib.sha256(data).hexdigest()

def section(data):
    end=data.index(b'## [th15]')
    start=data.index(b'## [th14]')if b'## [th14]'in data else end
    return start,end,data[start:end]

def main(path):
    path=path.resolve();assert path.is_relative_to(R/'artifacts/th14')and path.name=='reviewed-plan.json'
    home=path.parent;plan=json.loads(path.read_bytes());assert plan['publicEvidenceAuthorized']and not plan['rawAssetsOrObservationsIncluded']
    entries=[]
    for row in plan['files']:
        name=row['path'];p=(R/name).resolve();assert p.is_relative_to(R)and not any(part.startswith('.')for part in Path(name).parts)
        observer_cpp = name == 'runtimes/th12/th12_web/tests/cpp/th14-shot-lifetime-observer-nov05.cpp'
        assert observer_cpp or name.startswith(('tools/th14-','docs/porting/TH14_','docs/porting/th14-'))
        assert (observer_cpp and p.suffix == '.cpp') or p.suffix in ['.py','.mjs','.md','.json']
        data=p.read_bytes();assert len(data)==row['bytes']and SHA(data)==row['sha256']and len(data)<200000
        text=data.decode('utf8');assert '\0'not in text
        if p.suffix=='.py':ast.parse(text)
        if p.suffix=='.json':json.loads(text)
        entries.append(dict(path=name,mode='100644',type='blob',content=text))
    def api(endpoint,method='GET',body=None):
        argv=[str(GH),'api',endpoint,'--method',method]
        if body is not None:
            target=home/'request.json';target.write_text(json.dumps(body,ensure_ascii=False),encoding='utf8');argv+=['--input',str(target)]
        return json.loads(subprocess.check_output(argv,cwd=R,env={**os.environ,'GH_PROMPT_DISABLED':'1'},timeout=60))
    def put(name,value):(home/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    def contents(repo,ref):
        item=api(f'repos/{repo}/contents/docs/TOUHOU_PROGRESS.md?ref={ref}')
        return item,base64.b64decode(item['content'])
    upstream_repo='Ritosa2333/eagler-touhou';fork_repo='AdingApkgg/eagler-touhou';source_repo='AdingApkgg/thp'
    pr=api(f'repos/{upstream_repo}/pulls/130');assert pr['state']=='open'and pr['head']['repo']['full_name']==fork_repo
    ref=pr['head']['ref'];up_item,up=contents(upstream_repo,'main');fork_item,old=contents(fork_repo,ref)
    assert fork_item['sha']==plan['expectedForkFileSha']
    start,end,current_upstream_section=section(up);assert SHA(current_upstream_section)==plan['expectedUpstreamTh14SectionSha256']
    published_path=home/'published.json'
    if published_path.exists():
        published=json.loads(published_path.read_bytes());assert api(f'repos/{source_repo}/commits/main')['sha']==published['commit']
    else:
        head=api(f'repos/{source_repo}/commits/main');assert head['sha']==plan['previousHead']
        tree=api(f'repos/{source_repo}/git/trees','POST',dict(base_tree=head['commit']['tree']['sha'],tree=entries))
        commit=api(f'repos/{source_repo}/git/commits','POST',dict(message=plan['commitMessage'],tree=tree['sha'],parents=[head['sha']]))
        assert api(f'repos/{source_repo}/commits/main')['sha']==head['sha']
        api(f'repos/{source_repo}/git/refs/heads/main','PATCH',dict(sha=commit['sha'],force=False))
        assert api(f'repos/{source_repo}/commits/main')['sha']==commit['sha']
        remote=api(f'repos/{source_repo}/git/trees/'+tree['sha']+'?recursive=1');assert not remote.get('truncated')
        actual={row['path']:row.get('sha')for row in remote['tree']}
        for row in plan['files']:
            data=(R/row['path']).read_bytes();assert actual[row['path']]==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        published=dict(commit=commit['sha'],url=commit['html_url'],files=len(entries),allPublishedBlobHashesVerified=True,rawAssetsOrObservationsUploaded=False,completeGame=False)
        put('published.json',published);print(json.dumps(published),flush=True)
    commit=published['commit'];_,_,target=section(old);split=target.index(b'\n')+1
    for replacement in plan.get('th14LinkReplacements',[]):
        before=replacement['before'].encode();after=replacement['after'].replace('{commit}',commit).encode()
        assert target.count(before)==1;target=target.replace(before,after)
    addition=plan['progressAddition'].replace('{commit}',commit).encode('utf8')
    assert plan['progressMarker'].encode()not in target
    desired=up[:start]+target[:split]+addition+target[split:]+up[end:]
    a,b,_=section(desired);assert desired[:a]+desired[b:]==up[:start]+up[end:]
    (home/'progress-desired.md').write_bytes(desired)
    body=plan['progressBody'].replace('{commit}',commit);(home/'progress-body.md').write_text(body,encoding='utf8')
    response=api(f'repos/{fork_repo}/contents/docs/TOUHOU_PROGRESS.md','PUT',dict(message=plan['progressMessage'],branch=ref,sha=fork_item['sha'],content=base64.b64encode(desired).decode()))
    api(f'repos/{upstream_repo}/pulls/130','PATCH',dict(title=plan['progressTitle'],body=body))
    after_item,after=contents(fork_repo,ref);assert after==desired
    after_up,_=contents(upstream_repo,'main');assert after_up['sha']==up_item['sha']
    result=dict(sourceCommit=commit,pullRequest=pr['html_url'],forkCommit=response['commit']['sha'],forkFileSha=after_item['sha'],upstreamFileSha=up_item['sha'],onlyTh14=True,otherSectionsAndTableByteIdenticalToCurrentUpstream=True,publicEvidenceAuthorized=True,completeGame=False)
    put('progress-published.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);main(p.parse_args().plan)
