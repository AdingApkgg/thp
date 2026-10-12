"""Read TH06 New Classic PKGL archives, transcribed from its x64 executable.

0x140059e20: CRC32 of basename without final extension (case-sensitive).
0x140059cb0: two SplitMix64 outputs form the repeating 16-byte XOR key.
0x140059fb0: directory loader; 0x14005a470: file loader with optional Zstandard.
Original data is read only. Reports contain metadata and digests, not assets.
"""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASK=(1<<64)-1


def archive_seed(name):
    stem=name.replace('\\','/').rsplit('/',1)[-1]
    if '.' in stem:stem=stem.rsplit('.',1)[0]
    return zlib.crc32(stem.encode('utf-8'))


def key_bytes(seed):
    seed&=0xffffffff
    state=((seed<<32)^(seed*0x9e3779b1+1))&MASK
    key=b''
    for _ in range(2):
        state=(state+0x9e3779b97f4a7c15)&MASK
        value=state
        value=((value^(value>>30))*0xbf58476d1ce4e5b9)&MASK
        value=((value^(value>>27))*0x94d049bb133111eb)&MASK
        key+=(value^(value>>31)).to_bytes(8,'little')
    return key


def decrypt(data,seed):
    key=key_bytes(seed)
    # Translation on sixteen strided byte streams keeps full-archive verification
    # in C-backed Python operations instead of a byte-at-a-time Python loop.
    out=bytearray(data)
    for i,k in enumerate(key):
        out[i::16]=out[i::16].translate(bytes(v^k for v in range(256)))
    return bytes(out)


def directory(path):
    size=path.stat().st_size
    with path.open('rb') as stream:
        magic,length=struct.unpack('<4sI',stream.read(8))
        if magic!=b'PKGL' or length>size-8 or length>16*1024*1024:
            raise ValueError('invalid PKGL header')
        raw=stream.read(length)
    data=decrypt(raw,archive_seed(path.name))
    at=0;entries=[]
    while at<len(data):
        if len(data)-at<32:raise ValueError('truncated PKGL entry')
        flags,key,unpacked,packed,offset,n=struct.unpack_from('<HIQQQH',data,at)
        at+=32
        if not 0<n<256 or n>len(data)-at:raise ValueError('invalid PKGL name length')
        name=data[at:at+n].decode('utf-8');at+=n
        if '\0' in name or offset<8+length or offset>size or packed>size-offset:
            raise ValueError('PKGL entry outside archive')
        if flags&~1:raise ValueError(f'unsupported PKGL flags {flags}')
        if not flags and unpacked!=packed:raise ValueError('uncompressed PKGL size mismatch')
        entries.append(dict(name=name,flags=flags,key=key,bytes=unpacked,packed=packed,offset=offset))
    return entries


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-all',action='store_true')
    args=parser.parse_args()
    target=json.loads((ROOT/'runtimes/th06nc/target.json').read_text(encoding='utf-8'))
    data=Path(target['executable']).parent/'data'
    archives=[]
    for path in sorted(data.glob('*.dat')):
        entries=directory(path);decoded=[]
        if args.verify_all:
            from compression import zstd
            with path.open('rb') as stream:
                for row in entries:
                    stream.seek(row['offset']);plain=decrypt(stream.read(row['packed']),row['key'])
                    if row['flags']&1:plain=zstd.decompress(plain)
                    if len(plain)!=row['bytes']:raise ValueError('decoded size mismatch: '+row['name'])
                    decoded.append(dict(name=row['name'],sha256=hashlib.sha256(plain).hexdigest(),prefixHex=plain[:64].hex()))
        archives.append(dict(file=path.name,bytes=path.stat().st_size,entries=entries,decoded=decoded))
        print(path.name,len(entries),'entries;',sum(bool(r['flags']&1) for r in entries),'compressed;',len(decoded),'verified')
    out=ROOT/'artifacts/th06nc';out.mkdir(parents=True,exist_ok=True)
    (out/'pkgl-python.json').write_text(json.dumps({'game':'th06nc','executableSha256':target['sha256'],
         'readerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'archives':archives},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
