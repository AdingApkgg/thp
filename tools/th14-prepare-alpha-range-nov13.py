"""Isolate Goan114's alpha comparison optimization from deferred clearing."""
from pathlib import Path
import hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];O=R/'artifacts/th14/alpha-range-current-nov13'
assert not O.exists();O.mkdir();S=O/'source';S.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=R/'runtimes/th12/portable/sdl';source=root/'Renderer.cpp'
before=source.read_text();candidate=(R/'artifacts/th14/helper-clear-oracle-nov13/v4-candidate/source/Renderer.cpp').read_text()
text=before
a=text.index('  // Match byte alpha after');b=text.index('  if(version==8)',a)
c=candidate.index('  // Byte alpha is monotonic');d=candidate.index('  if(version==8)',c)
text=text[:a]+candidate[c:d]+text[b:]
line='  if(version==10){glUseProgram(p.id);glUniform4fv(glGetUniformLocation(p.id,"alphaBoundary[0]"),64,alphaBoundaries.data());glUseProgram(currentProgram);}'
assert text.count(line)==1
text=text.replace(line,'#if !defined(PORT_TITLE) || PORT_TITLE != 14\n'+line+'\n#endif')
anchor='  for(int i=0;i<28;i++)p.uniforms[i].location='
assert text.count(anchor)==1
text=text.replace(anchor,'  if(version==10)names[22]="alphaRange";\n'+anchor)
anchor='else if(n==3)glUniform3fv(u.location,1,p);else glUniform1f'
assert text.count(anchor)==1
text=text.replace(anchor,'else if(n==3)glUniform3fv(u.location,1,p);else if(n==2)glUniform2fv(u.location,1,p);else glUniform1f')
anchor='float alpha=float(p.alphaReference)/255;uniform(22,1,&alpha);'
assert text.count(anchor)==1
text=text.replace(anchor,'''\n#if defined(PORT_TITLE) && PORT_TITLE == 14
 if(version==10){
  const auto threshold=[&](u32 n){return n<256?alphaBoundaries[n]:2.f;};
  const u32 ref=std::min(p.alphaReference,256u);
  const float range[]{threshold(ref),threshold(ref+1)};
  uniform(22,2,range);
 }else
#endif
 {const float alpha=float(p.alphaReference)/255;uniform(22,1,&alpha);}
 ''')
assert 'resolve_color_clear'not in text and text.count('bind_texture(0);')==before.count('bind_texture(0);')
(O/'Renderer.before.cpp').write_bytes(source.read_bytes())
(O/'Renderer.candidate.cpp').write_text(text,encoding='utf8',newline='\n')
bindings={}
for p in [*root.glob('*.hpp'),source]:
 q=S/p.name;q.write_bytes((O/'Renderer.candidate.cpp').read_bytes()if p==source else p.read_bytes());bindings[p.relative_to(R).as_posix()]=sha(p)
old=R/'artifacts/th14/helper-clear-oracle-nov13/v4-candidate/source'
for name in ['raster-fixture.cpp','alpha-fixture.cpp','fixture.cpp']:
 p=old/name;(S/name).write_bytes(p.read_bytes());bindings[p.relative_to(R).as_posix()]=sha(p)
cc=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'
flags=['--target=wasm32-wasip1-threads','-pthread','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-D__EMSCRIPTEN__=1','-I'+str(R/'artifacts/th14/boot-main-intake-nov07/application-component/include'),'-I'+str(S)]
exports=['gpu_initialize','gpu_error','gpu_alpha_case','gpu_alpha_texture','gpu_alpha_boundaries','clear_case','gpu_close','allocated','released']
cmd=[str(cc),*flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--import-memory','-Wl,--export-memory','-Wl,--allow-undefined','-Wl,--initial-memory=67108864','-Wl,--max-memory=1073741824','-Wl,-z,stack-size=1048576',*['-Wl,--export='+x for x in exports],str(S/'Renderer.cpp'),str(S/'fixture.cpp'),'-o',str(O/'probe.wasm')]
with(O/'build.log').open('wb')as f:q=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,env=dict(os.environ,TEMP=str(O),TMP=str(O),TMPDIR=str(O)))
assert q.returncode==0,(O/'build.log').read_text(errors='replace')[-3000:]
j=dict(sourceBindings=bindings,generatedSourceBindings={p.relative_to(R).as_posix():sha(p)for p in S.iterdir()},wasmSha256=sha(O/'probe.wasm'),explicitTh14Branch=True,normalRendererAccess=True,normalFixtureAccess=True,alphaOnly=True,deferredClearsIntegrated=False,rootSourceChanged=False,completeGame=False)
(O/'build.json').write_text(json.dumps(j,indent=2)+'\n')
driver=(R/'tools/th14-run-helper-clear-oracle-nov13.mjs').read_text()
driver=driver.replace("const variant=process.argv[2];assert(['baseline','candidate'].includes(variant));","const variant='candidate';")
driver=driver.replace("const attempt=process.argv[3]??'v2';assert(['v2','v3','v4'].includes(attempt));","const attempt='v4';")
driver=driver.replace("const B=resolve(H,attempt+'-'+variant)","const B=resolve(R,'artifacts/th14/alpha-range-current-nov13')")
assert driver.count('alpha-range-current-nov13')==1
begin=driver.index(' const expectedClears=')
end=driver.index('}catch(e)',begin)
driver=driver[:begin]+driver[end:]
driver=driver.replace('assert.equal(clearCases,64);','assert.equal(clearCases,0);')
(R/'tools/th14-run-alpha-range-current-nov13.mjs').write_text(driver,encoding='utf8',newline='\n')
print('Built isolated alpha-only candidate; production source unchanged')
