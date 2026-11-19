"""Decode every reframed Ogg with independent FFmpeg, preserving sample counts.

No Opus packets were transcoded. This proves container/decoder interoperability;
it does not compare FFmpeg PCM with the original embedded Opus decoder.
"""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    manifest=ROOT/'runtimes/th06nc/artifacts/audio/music-manifest.json';raw=manifest.read_bytes();files=json.loads(raw);results=[]
    for c in files:
        path=ROOT/'runtimes/th06nc/artifacts/audio'/c['directory']/c['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==c['sha256']
        result=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-c:a','pcm_f32le','-f','framemd5','-'],capture_output=True,check=True);assert not result.stderr,result.stderr.decode();lines=result.stdout.decode().splitlines();samples=sum(int(line.split(',')[3])for line in lines if line and not line.startswith('#'));assert samples==c['samples'],(c['directory'],c['file'],samples,c['samples']);results.append(dict(directory=c['directory'],file=c['file'],samples=samples,frameDigestSha256=hashlib.sha256(result.stdout).hexdigest()));print(c['directory'],c['file'],samples,flush=True)
    assert manifest.read_bytes()==raw
    report=dict(scope=__doc__,ffmpeg=subprocess.check_output(['ffmpeg','-version']).decode().splitlines()[0],manifestSha256=hashlib.sha256(raw).hexdigest(),files=results,passed=True,completeGame=False,nativeEquivalent=False);(ROOT/'docs/porting/th06nc-music-decode-verified.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,files=len(results))))
if __name__=='__main__':main()
