"""Compile the changed Stage implementation for each shared title variant."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
R=Path(__file__).resolve().parents[1];sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();home=a.candidate.resolve(strict=True)
    assert home.is_relative_to(R/'artifacts/th14');out=home/'stage-syntax';out.mkdir()
    base=json.loads((home/'build/ordinary/observer-build.json').read_bytes());source=Path(base['sourceSnapshotRoot'])/'th12_web/cpp/game/Stage.cpp'
    compiler=R/'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe';assert sha(compiler.read_bytes())==base['compilerSha256'];rows=[]
    for title in(12,13,14,16):
        flags=[x for x in base['flags']if not x.startswith('-DPORT_TITLE=')]
        command=[str(compiler),*flags,'-DPORT_TITLE='+str(title),'-fsyntax-only',str(source)]
        result=subprocess.run(command,cwd=R,env={**os.environ,'TEMP':str(out),'TMP':str(out)},capture_output=True,timeout=60)
        (out/f'th{title}.log').write_bytes(result.stdout+result.stderr);assert result.returncode==0,result.stderr.decode(errors='replace')[-2000:]
        rows.append(dict(title=title,exitCode=0,sourceSha256=sha(source.read_bytes()),argv=command))
    report=dict(passed=True,cases=rows,toolSha256=sha(Path(__file__).read_bytes()),completeGame=False)
    (out/'report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print('PASS four shared-title Stage syntax checks',flush=True)


if __name__=='__main__':main()
