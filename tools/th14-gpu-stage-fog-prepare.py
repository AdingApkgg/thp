"""Prepare actual STD fog settings and independent scaled world fixtures.

All original assets remain read-only. Generated source is saved for review.
"""
import json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'artifacts/th14/native-campaign-assets/57d84a5cbe82-cd2f2e3549c0'
OUT=ROOT/'artifacts/th14/gpu-stage-fog';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((SOURCE/'manifest.json').read_text())
entries={e['name']:e for e in manifest['originalEntries']}
commands=[];profiles=[];seen=set();sources={}
for stage in range(1,8):
    name=f'st{stage:02}.std';p=SOURCE/'entries'/name;b=p.read_bytes();assert sha(b)==entries[name]['sha256'];sources[str(p.relative_to(ROOT)).replace('\\','/')]=sha(b)
    offset=struct.unpack_from('<I',b,8)[0];terminated=False
    while offset+8<=len(b):
        time,opcode,size=struct.unpack_from('<ihh',b,offset)
        if (time,opcode,size)==(-1,-1,-1):terminated=True;break
        assert size>=8 and offset+size<=len(b)
        if opcode in (8,9):
            arg=offset+8+(8 if opcode==9 else 0);color,near,far=struct.unpack_from('<Iff',b,arg)
            assert size>=(20 if opcode==8 else 28) and 0<=near<far
            key=(color,near,far)
            if key not in seen:
                seen.add(key);profiles.append(dict(color=color,near=near,far=far,density=1,scale=struct.unpack('<f',struct.pack('<f',(near+far)/3))[0]))
            commands.append(dict(stage=stage,time=time,offset=offset,opcode=opcode,profile=profiles.index(next(r for r in profiles if (r['color'],r['near'],r['far'])==key))))
        offset+=size
    assert terminated
assert len(profiles)==37
(OUT/'profiles.json').write_text(json.dumps(dict(originalArchiveSha256=manifest['originalArchiveSha256'],sources=sources,profiles=profiles,commands=commands,completeGame=False,nativeEquivalent=False,limits='STD fog endpoints only; scaled independent geometry exercises near/far clipping and fog. Does not execute native stage draw loop or enumerate every interpolation frame.'),indent=2)+'\n',encoding='utf8')
cpp_path=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-world-profiles-fixture.cpp'
cpp=cpp_path.read_text()
def replace_one(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b)
cpp=replace_one(cpp,'gpu_world_profile_case','gpu_stage_fog_case');cpp=replace_one(cpp,'profile>4','profile>=37')
for array in ['worlds','views','projections']:cpp=replace_one(cpp,'const float '+array+'[][16]','float '+array+'[][16]')
params='const float profiles[][3]={{.75f,2.5f,.6f},{0,1,.1f},{1,5,.5f},{2,3.25f,.9f},{.125f,10,1}};'
rows=','.join('{'+f"{r['near']}f,{r['far']}f,1.0f"+'}' for r in profiles)
scales=','.join(repr(r['scale'])+'f' for r in profiles)
colors=','.join(hex(r['color'])+'u' for r in profiles)
cpp=replace_one(cpp,params,'const float profiles[][3]={'+rows+'};')
cpp=replace_one(cpp,'p.fogColor=0xffa0b8d0;','const u32 fogColors[]={'+colors+'};p.fogColor=fogColors[profile];')
anchor='r.transform(MatrixKind::World,worlds[world]);'
setup='const float scales[]={'+scales+'};const float scale=scales[profile];for(auto& matrix:worlds)for(int col=0;col<4;col++)for(int row=0;row<3;row++)matrix[col*4+row]*=scale;for(auto& matrix:views)for(int row=0;row<3;row++)matrix[12+row]*=scale;projections[0][0]=projections[0][5]=1.f/scale;projections[0][10]=1.f/(9.9f*scale);projections[1][14]=-scale/9.9f;\n    '
cpp=replace_one(cpp,anchor,setup+anchor)
fixture=ROOT/'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-fog-fixture.cpp';fixture.write_text(cpp,encoding='utf8')
native_path=ROOT/'tools/th14-gpu-world-profiles-native.py';native=native_path.read_text(encoding='utf-8-sig')
native=replace_one(native,"artifacts/th14/gpu-world-profiles'","artifacts/th14/gpu-stage-fog'")
native=replace_one(native,'profiles=[(.75,2.5,.6),(0,1,.1),(1,5,.5),(2,3.25,.9),(.125,10,1)]',"profiles=json.loads((OUT/'profiles.json').read_text())['profiles']")
native=replace_one(native,'itertools.product(range(5),range(3),range(2),range(2),range(2),range(4),range(2),range(2))','itertools.product(range(len(profiles)),range(3),range(2),range(2),range(2),(0,3),range(2),range(2))')
native=replace_one(native,'near,far,density=profiles[profile]','near,far,density=(profiles[profile][k] for k in ("near","far","density"));scale=profiles[profile]["scale"]\n            scaledworlds=[[f32(v*scale) if i%4<3 else v for i,v in enumerate(m)] for m in worlds];scaledviews=[[f32(v*scale) if i in (12,13,14) else v for i,v in enumerate(m)] for m in views];scaledprojections=[m.copy() for m in projections];scaledprojections[0][0]=scaledprojections[0][5]=f32(1/scale);scaledprojections[0][10]=f32(1/f32(f32(9.9)*scale));scaledprojections[1][14]=f32(-scale/f32(9.9))')
native=replace_one(native,'((256,worlds[world]),(2,views[view]),(3,projections[projection]),(16,texmatrix))','((256,scaledworlds[world]),(2,scaledviews[view]),(3,scaledprojections[projection]),(16,texmatrix))')
native=replace_one(native,'(34,0xffa0b8d0)','(34,profiles[profile]["color"])')
native=replace_one(native,'cases.append(dict(profile=profile,near=near,far=far,density=density,','cases.append(dict(profile=profile,near=near,far=far,density=density,color=profiles[profile]["color"],scale=scale,')
native=replace_one(native,'report=dict(generated=True,behaviorFlags=','report=dict(generated=True,profilesSha256=sha((OUT/"profiles.json").read_bytes()),behaviorFlags=')
(ROOT/'tools/th14-gpu-stage-fog-native.py').write_text(native,encoding='utf8')
(OUT/'prepared.json').write_text(json.dumps(dict(profiles=37,commands=len(commands),cases=37*192,fixtureSha256=sha(fixture.read_bytes()),nativeToolSha256=sha(native.encode()),prepareToolSha256=sha(Path(__file__).read_bytes()),sources=sources),indent=2)+'\n',encoding='utf8')
print(f'Prepared {len(commands)} original STD fog commands, 37 endpoint settings, {37*192} actual GPU scenarios')
