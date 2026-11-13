from pathlib import Path
import json,re,hashlib
R=Path.cwd();H=R/'artifacts/th14/beam-length-guard-nov14';A=H/'optional-current-source';j=json.loads((R/'artifacts/th14/collaborator-review-cfb777c-nov13/activation-candidate/build.json').read_bytes());nodes={ (A/'core'/n).resolve():('core',n)for n in j['sourceBindings']};nodes.update({(A/'common'/n).resolve():('common',n)for n in j['commonBindings']});byname={}
for p in nodes:byname.setdefault(p.name,[]).append(p)
graph={};fallback=[]
for p in nodes:
 deps=set()
 for quote,n in re.findall(r'^\s*#\s*include\s*([<"])([^>"\r\n]+)[>"]',p.read_text(encoding='utf-8',errors='replace'),re.M):
  direct=(p.parent/n).resolve()
  if direct in nodes:deps.add(direct)
  elif n.split('/')[-1]in byname:
   found=byname[n.split('/')[-1]];deps.update(found);fallback.append(dict(file=str(p.relative_to(A)),include=n,matches=len(found)))
 graph[p]=deps
changed={p for p,(cat,n)in nodes.items()if hashlib.sha256(p.read_bytes()).hexdigest()!=(j['sourceBindings']if cat=='core'else j['commonBindings'])[n]};rt=A/'core/runtimes/th12';sources={}
for p,(cat,n)in nodes.items():
 if p.suffix!='.cpp':continue
 key=(p.relative_to(rt).as_posix().replace('/','_')if cat=='core'else p.name)+'.o';sources[key]=p
rows=[]
for obj in j['objects']:
 key=Path(obj).name;assert key in sources,key;p=sources[key];todo=[p];seen=set()
 while todo:
  x=todo.pop()
  if x in seen:continue
  seen.add(x);todo.extend(graph[x]-seen)
 hits=seen&changed;rows.append(dict(object=obj,source=str(p.relative_to(A)),rebuild=bool(hits),changedDependencies=[str(x.relative_to(A))for x in sorted(hits)]))
q=dict(units=len(rows),recompile=sum(x['rebuild']for x in rows),reuse=sum(not x['rebuild']for x in rows),sourceChanges=[str(p.relative_to(A))for p in sorted(changed)],dependencyMethod='Conservative recursive include graph across all bound project and common files; unresolved project basename matches include all candidates, including conditional includes.',basenameResolutions=fallback,rows=rows)
(H/'optional-dependency-plan.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:q[k]for k in ['units','recompile','reuse','sourceChanges']}))
