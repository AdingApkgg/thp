"""Prepare indexed, independently compressed game content for Package Store.

Input is the output of the TH06nc asset preparers, never a user's save folder.
Music stays in the Launcher's separate OGG component.
"""
import argparse,gzip,hashlib,json,shutil,struct,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
files=[];offset=0
with tempfile.TemporaryFile() as payload:
 for source in sorted(args.artifacts.rglob('*')):
  if not source.is_file():continue
  name=source.relative_to(args.artifacts).as_posix()
  if name.startswith(('audio/bgm/','audio/bgm2/')):
   parts=Path(name).parts;target=args.output/'music'/(parts[1]+'_'+parts[2]);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);continue
  raw=source.read_bytes();compressed=gzip.compress(raw,compresslevel=6,mtime=0)
  files.append(dict(path=name,offset=offset,bytes=len(compressed),decodedBytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()));offset+=len(compressed);payload.write(compressed)
 header=json.dumps(dict(schema='th06nc/content/1',files=files),separators=(',',':')).encode()
 with (args.output/'th06nc.data').open('wb') as target:
  target.write(struct.pack('<I',len(header)));target.write(header);payload.seek(0);shutil.copyfileobj(payload,target)
print(json.dumps(dict(files=len(files),compressedBytes=offset+len(header)+4,decodedBytes=sum(f['decodedBytes']for f in files))))
