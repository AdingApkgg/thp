"""Fetch the pinned MIT Zstandard decoder, verifying npm's SHA-512 digest.

No package lifecycle scripts are executed. Only the ESM source and license are
copied from the archive. Re-run to reproduce shared/vendor/fzstd/ exactly.
"""
import base64
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
URL='https://registry.npmjs.org/fzstd/-/fzstd-0.1.1.tgz'
INTEGRITY='dkuVSOKKwh3eas5VkJy1AW1vFpet8TA/fGmVA5krThl8YcOVE/8ZIoEA1+U1vEn5ckxxhLirSdY837azmbaNHA=='


def main():
    with urllib.request.urlopen(URL,timeout=30) as response:data=response.read()
    if base64.b64encode(hashlib.sha512(data).digest()).decode()!=INTEGRITY:
        raise ValueError('fzstd package integrity mismatch')
    out=ROOT/'shared/vendor/fzstd';out.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as package:
        for source,destination in [('package/esm/index.mjs','index.mjs'),('package/LICENSE','LICENSE')]:
            (out/destination).write_bytes(package.extractfile(source).read())
    (out/'provenance.json').write_text(json.dumps({'name':'fzstd','version':'0.1.1','license':'MIT',
      'repository':'https://github.com/101arrowz/fzstd','tarball':URL,'integrity':'sha512-'+INTEGRITY},indent=2)+'\n')
    print('Vendored fzstd 0.1.1, integrity verified.')


if __name__=='__main__':main()
