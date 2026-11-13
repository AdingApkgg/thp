"""Link a silent mixer fixture with the verified current TH14 providers."""
from pathlib import Path
import hashlib
import argparse
import json
import os
import subprocess

R=Path(__file__).resolve().parents[1]
base=R/'artifacts/th14/beam-length-guard-nov14/component'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,default=R/'artifacts/th14/current-audio-mixer-nov14/component')
args=parser.parse_args()
out=args.out.resolve();assert out.is_relative_to(R/'artifacts/th14')
assert not out.exists();out.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((base/'build.json').read_bytes())
for name,digest in {**j['sourceBindingsByMode']['candidate'],**j['objectBindings']}.items():assert sha(R/name)==digest,name
original=R/j['sourceFixture'];fixture=out/'fixture.cpp'
include=(R/'runtimes/th12/th12_web/tests/cpp/th14-audio-mixer-fixture.cpp').as_posix()
fixture.write_text('#include "'+include+'"\n'+'''
API(sfx_master) void sfx_master(i32 level){audio.effects.master_volume=level;}
API(sfx_pause) void sfx_pause(i32 paused){audio.pause_sounds(paused!=0);}
API(audio_close) void audio_close(){audio.close();}
#include "MusicCatalog.hpp"
API(music_info) const u32* music_info(i32 cue){
 static u32 info[3];info[0]=info[1]=info[2]=0;std::vector<u8> formats;
 if(!source.read("thbgm.fmt",formats))return info;
 const char* name=nullptr;for(const auto& t:music_tracks)if(t.cue==cue){name=t.file;break;}
 if(!name)return info;const auto expected=std::string(name)+".wav";
 for(u32 i=0;i+52<=formats.size();i+=52){const auto* p=formats.data()+i;
  if(std::strncmp(reinterpret_cast<const char*>(p),expected.c_str(),16))continue;
  u32 total,intro,rate;u16 align;std::memcpy(&total,p+28,4);std::memcpy(&intro,p+24,4);
  std::memcpy(&rate,p+36,4);std::memcpy(&align,p+44,2);
  if(align){info[0]=total/align;info[1]=intro/align;info[2]=rate;}break;
 }return info;
}
''',encoding='utf-8')
cmd=json.loads((base/'command.json').read_bytes())
assert cmd.count(str(original))==1
cmd=[str(fixture) if x==str(original) else str(out/'candidate.wasm') if x==str(base/'candidate.wasm') else x for x in cmd]
(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with(out/'build.log').open('wb') as log:
    result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'TEMP':str(out),'TMP':str(out)})
assert result.returncode==0,(out/'build.log').read_text(errors='replace')[-4000:]
bindings={**j['sourceBindingsByMode']['candidate']}
for p in (fixture,R/'runtimes/th12/th12_web/tests/cpp/th14-audio-mixer-fixture.cpp',R/'runtimes/th12/th12_web/tests/cpp/th14-music-restore-fixture.cpp'):
    bindings[p.relative_to(R).as_posix()]=sha(p)
j.update(sourceBindingsByMode={'candidate':bindings},sourceFixture=fixture.relative_to(R).as_posix(),
         outputs={'candidate':{'wasmSha256':sha(out/'candidate.wasm')}},
         onlyMixerFixtureLinked=True,providerObjectsReused=145,productionGameCodeChanged=False,
         builderSha256=sha(Path(__file__)))
(out/'build.json').write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps(dict(compiled=True,objectsVerified=145,wasmSha256=sha(out/'candidate.wasm'))),flush=True)
