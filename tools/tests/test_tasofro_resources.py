"""Compare JS Tasofro results with independent Python integer/cipher execution.

Run node tools/th-tasofro-resources.mjs first. The public-domain upstream source
in reference/135tk supplies the public RSA moduli; no game bytes are fixtures.
"""
import json
import hashlib
import re
import struct
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MASK=0xffffffff


def cg_decode(data,offset,total_size=None):
    out=bytearray(data)
    key=(len(out) if total_size is None else total_size)^offset
    for pos in range(0,len(out),4):
        state=(key+pos//4)&MASK
        word=0
        for _ in range(4):
            product=state*0x5e4789c9
            quotient=((product>>46)+(product>>63))&MASK
            state=((state-quotient*0xadc8)*0xbc8f+quotient*0xfffff2b9)&MASK
            if state==0 or state&0x80000000:
                state=(state+0x7fffffff)&MASK
            word=((word<<8)|(state&255))&MASK
        for j in range(min(4,len(out)-pos)):
            out[pos+j]^=(word>>(j*8))&255
    return bytes(out)


def tfpk_directory(stream):
    header=stream.read(5)
    assert header[:4]==b'TFPK'
    version=header[4]
    source=(ROOT/'reference/135tk/th135arc-alt/Rsa.cpp').read_text().split('}; // In Big Endian')[0]
    keys=[int.from_bytes(bytes(int(n,16) for n in re.findall(r'0x([\da-fA-F]{2})',row)),'big')
          for row in re.findall(r'\{([^{}]+)\}',source)]
    selected=None
    def field(size):
        nonlocal selected
        result=b''
        for n in range(0,size,32):
            encrypted=stream.read(64)
            assert len(encrypted)==64
            if encrypted[32:]==bytes(32):
                plain=encrypted[:32]
            else:
                plain=None
                for modulus in ([selected] if selected else keys):
                    block=pow(int.from_bytes(encrypted,'big'),65537,modulus).to_bytes(64,'big')
                    match=re.match(b'\x00\x01\xff{29,}\x00',block)
                    if match:
                        selected=modulus
                        plain=block[match.end():]
                        break
                assert plain is not None
            length=min(32,size-n)
            assert len(plain)>=length
            result+=plain[:length]
        return result
    def words(size):return struct.unpack('<'+'I'*(size//4),field(size))
    directories=words(4)[0]
    for _ in range(directories):field(8)
    if directories:
        compressed,unpacked,blocks=words(12)
        assert len(zlib.decompress(field(blocks*32)[:compressed]))==unpacked
    count=words(4)[0]
    rows=[]
    for _ in range(count):
        size,offset=words(8)
        hash_=words(4 if version==0 else 8)[0]
        key=words(16)
        if version:
            size^=key[0];offset^=key[1];hash_^=key[2]
            key=tuple((-k)&MASK for k in key)
        rows.append({'bytes':size,'offset':offset,'hash':hash_,'key':struct.pack('<4I',*key)})
    base=stream.tell()
    for row in rows:row['offset']+=base
    return version,rows


class TasofroReference(unittest.TestCase):
    def test_original_directories_and_decoded_prefixes(self):
        total_entries=total_samples=0
        expected_archives=successful_archives=0
        reader_sha=hashlib.sha256((ROOT/'shared/tasofro/archives.mjs').read_bytes()).hexdigest()
        for title in ('135','145','155','175'):
            proof=json.loads((ROOT/f'artifacts/tasofro/th{title}.json').read_text())
            self.assertEqual(proof['readerSha256'],reader_sha,'JS report must match the current reader')
            expected_archives+=len(proof['archives'])
            target=json.loads((ROOT/f'runtimes/th{title}/target.json').read_text())
            for archive in proof['archives']:
                with self.subTest(game=title,file=archive['file']):
                    record=target['dataArchives'][archive['file']]
                    with open(record['path'],'rb') as stream:
                        if title=='175':
                            end=record['bytes']-32
                            stream.seek(end)
                            footer=struct.unpack('<8I',cg_decode(stream.read(32),end))
                            self.assertEqual((footer[5],footer[7]),(24,32))
                            at=end-footer[6]*24
                            stream.seek(at)
                            rows=[{'hash':f'{h:016x}','offset':o,'bytes':s}
                                  for h,o,s in struct.iter_unpack('<3Q',cg_decode(stream.read(footer[6]*24),at))]
                        else:
                            version,rows=tfpk_directory(stream)
                            self.assertEqual(version,archive['version'])
                        self.assertEqual(len(rows),len(archive['entries']))
                        for actual,expected in zip(archive['entries'],rows):
                            for key in ('hash','offset','bytes'):self.assertEqual(actual[key],expected[key])
                        for sample in archive['decoded']:
                            row=rows[sample['index']]
                            stream.seek(row['offset'])
                            raw=stream.read(min(64,row['bytes']))
                            if title=='175':
                                plain=raw if row['hash']=='000000001f47c0c8' else cg_decode(raw,row['offset'],row['bytes'])
                            else:
                                key=row['key']
                                plain=bytes(b^key[i%16]^(key[i%4] if i<4 else raw[i-4]) for i,b in enumerate(raw)) if version else bytes(b^key[i%16] for i,b in enumerate(raw))
                            self.assertEqual(plain.hex(),sample['prefixHex'])
                            total_samples+=1
                        total_entries+=len(rows)
                        successful_archives+=1
        self.assertEqual(successful_archives,expected_archives,'do not write a passing report after a failed subtest')
        print(f'Compared {total_entries} directory entries and {total_samples} decoded prefixes.')
        (ROOT/'artifacts/tasofro/python-comparison.json').write_text(json.dumps({
            'passed':True,'readerSha256':reader_sha,'entries':total_entries,
            'decodedPrefixes':total_samples})+'\n')


if __name__=='__main__':unittest.main()
