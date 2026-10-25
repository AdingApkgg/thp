"""Compare one bounded capture as it becomes available; never launch a next case."""
import argparse
import datetime
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ['native','assets','build','output','selection']:parser.add_argument('--'+key,required=True)
    parser.add_argument('--prefixes',default='1000');args=parser.parse_args()
    native=(ROOT/args.native).resolve();out=(ROOT/args.output).resolve()
    assert native.is_relative_to(ROOT/'artifacts/th14')and out.is_relative_to(ROOT/'artifacts/th14');out.mkdir(exist_ok=False)
    checked=set();prefixes=sorted(set(int(value)for value in args.prefixes.split(',')if value));assert all(value>0 for value in prefixes)
    def load(path):
        try:return json.loads(path.read_text())
        except(FileNotFoundError,json.JSONDecodeError):return None
    def compare(prefix):
        label='prefix-'+str(prefix)if prefix else'full'
        command=['C:/nvm4w/nodejs/node.exe',str(ROOT/'tools/th14-compare-native-campaign.mjs'),'--native',str(native),'--assets',args.assets,'--build',args.build,'--output',str(out/label),'--selection',args.selection,'--prefix',str(prefix)]
        with(out/(label+'.log')).open('w',encoding='utf8')as log:result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prefix=prefix,exitCode=result.returncode,scope='All enabled comparison gates; inspect independent reports.')),flush=True)
    while True:
        report=load(native/'report.json');progress=report or load(native/'progress.json')
        if progress:
            for limit in prefixes:
                if limit not in checked and progress['callbacks']>=limit+(0 if report else 300):checked.add(limit);compare(limit)
        if report:
            if report['childExited']and report['observedForcedReplayEndMenu']and not report['error']:compare(0)
            print(json.dumps(dict(finished=True,callbacks=report['callbacks'],error=report['error'],automaticNextNativeCase=False,wholeGameComplete=False)),flush=True);break
        time.sleep(10)

if __name__=='__main__':main()
