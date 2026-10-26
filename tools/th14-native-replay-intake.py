"""Intake one intact Royalflare recording and validate its original x86 codec.

The source page supplies a label, not a playback/clear assertion. Only original
4028e0/465840 bytes decode the file; CRT services and dictionary startup are
declared boundaries. No original process, game state or input is modified.
"""
import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
from html.parser import HTMLParser
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
TOOL_SOURCE=Path(__file__).read_bytes()


class Rows(HTMLParser):
    def __init__(self):
        super().__init__();self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr':self.row=dict(cells=[],links=[])
        if self.row is not None:
            if tag in ('td','th'):self.cell=[]
            if tag=='a':self.row['links'].append(dict(attrs).get('href',''))
    def handle_data(self,text):
        if self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ('td','th')and self.row is not None and self.cell is not None:
            self.row['cells'].append(''.join(self.cell).strip());self.cell=None
        if tag=='tr'and self.row is not None:
            self.rows.append(self.row);self.row=None;self.cell=None


def download(url,limit):
    assert url.startswith('https://maribelhearn.com/')
    # Use the platform TLS client, with HTTPS and size limits retained. Python
    # OpenSSL on this host timed out during its independent TLS handshake.
    with tempfile.NamedTemporaryFile(dir=ROOT/'artifacts/th14',suffix='.download',delete=False)as stream:
        temporary=Path(stream.name)
    try:
        result=subprocess.run(['curl.exe','-q','--silent','--show-error','--fail','--location',
            '--proto','=https','--proto-redir','=https','--max-redirs','3','--connect-timeout','10',
            '--max-time','30','--max-filesize',str(limit),'--user-agent','TH14-reference-verification/1.0',
            '--output',str(temporary),'--write-out','%{json}',url],check=True,capture_output=True,text=True)
        headers=json.loads(result.stdout);assert headers['http_code']==200
        assert headers['url_effective'].startswith('https://maribelhearn.com/')
        assert temporary.stat().st_size<=limit
        return temporary.read_bytes(),headers['url_effective'],headers.get('content_type')
    finally:
        temporary.unlink(missing_ok=True)


def decode_native(data):
    assert data[:6]==b't13r\x02\x00'
    packed,unpacked=struct.unpack_from('<II',data,0x1c)
    declared=struct.unpack_from('<I',data,0xc)[0]
    assert declared==0x24+packed<=len(data)and 0<packed<0x7f000 and 0<unpacked<0x300000
    img,_,_=importlib.import_module('th-anm-handlers').handlers(14)
    machine=Uc(UC_ARCH_X86,UC_MODE_32)
    for _,address,size,offset,length in img.sections:
        first=address&~4095;machine.mem_map(first,((address+size+4095)&~4095)-first)
        machine.mem_write(address,img.data[offset:offset+length])
    base=0x70000000;machine.mem_map(base,0x800000)
    src,dst,stack=base+0x1000,base+0x80000,base+0x3ff000;heap=[base+0x500000]
    def put(pointer,value):machine.mem_write(pointer,struct.pack('<I',value&0xffffffff))
    def get(pointer):return struct.unpack('<I',machine.mem_read(pointer,4))[0]
    def boundary(machine,address,size,user):
        sp=machine.reg_read(UC_X86_REG_ESP);value=0
        if address==0x485540:
            length=get(sp+4);value=heap[0];heap[0]+=(length+15)&~15
            assert heap[0]<base+0x800000;machine.mem_write(value,bytes(length))
        elif address==0x487620:
            value=get(sp+4);machine.mem_write(value,bytes(machine.mem_read(get(sp+8),get(sp+12))))
        machine.reg_write(UC_X86_REG_EAX,value);machine.reg_write(UC_X86_REG_ESP,sp+4)
        machine.reg_write(UC_X86_REG_EIP,get(sp))
    for address in (0x485540,0x487620,0x4855d2):machine.hook_add(UC_HOOK_CODE,boundary,begin=address,end=address)
    def run(address,args):
        put(stack,base)
        for index,value in enumerate(args):put(stack+4+index*4,value)
        machine.reg_write(UC_X86_REG_ESP,stack);machine.reg_write(UC_X86_REG_ECX,src);machine.reg_write(UC_X86_REG_EDX,packed)
        machine.emu_start(address,base,count=50000000);assert machine.reg_read(UC_X86_REG_EIP)==base
    machine.mem_write(src,data[0x24:declared]);machine.mem_write(0x4f36c8,bytes(8192));machine.mem_write(dst,bytes(unpacked+32))
    run(0x4028e0,(0x5c,0xe1,0x400,packed));run(0x4028e0,(0x7d,0x3a,0x100,packed));run(0x465840,(dst,unpacked))
    decoded=bytes(machine.mem_read(dst,unpacked))
    spec=importlib.util.spec_from_file_location('container',ROOT/'tools/th-replay-container.py')
    mirror=importlib.util.module_from_spec(spec);spec.loader.exec_module(mirror)
    assert decoded==mirror.decode_with(data,packed,unpacked,mirror.TH13)
    count,character,subtype,difficulty=struct.unpack_from('<4I',decoded,0x78)
    assert 1<=count<=7 and character<=2 and subtype<=1 and difficulty<=4
    stages=[];offset=0x94
    for index in range(count):
        stage,seed=struct.unpack_from('<HH',decoded,offset);frames,payload=struct.unpack_from('<II',decoded,offset+4)
        assert 1<=stage<=7 and 0<frames*6<=payload
        stages.append(dict(stage=stage,seed=seed,frames=frames,payloadBytes=payload,headerSha256=SHA(decoded[offset:offset+0xdc])))
        offset+=0xdc+payload
    assert offset==len(decoded)
    return decoded,dict(declaredContainerBytes=declared,trailingBytes=len(data)-declared,
        trailingSha256=SHA(data[declared:]),decodedSha256=SHA(decoded),stageCount=count,
        character=character,subtype=subtype,difficulty=difficulty,stages=stages,
        actualNativeCodecVerified=True,nativeExecutableSha256=SHA(img.data),
        controlledBoundaries=['CRT malloc/free/memcpy','zero-filled codec dictionary at independent file startup'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--expected',required=True,help='character,subtype,difficulty')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();name=args.name
    assert len(name)==11 and name.startswith('th14_ud')and all(c in '0123456789abcdef'for c in name[7:])
    assert out.is_relative_to(ROOT/'artifacts/th14')and not out.exists()
    expected=[int(value)for value in args.expected.split(',')];assert len(expected)==3
    page_url='https://maribelhearn.com/royalflare/th14';link='/replays/royalflare/th14/'+name+'.rpy'
    page,final_page,_=download(page_url,1_000_000);parsed=Rows();parsed.feed(page.decode())
    rows=[row for row in parsed.rows if link in row['links']];assert len(rows)==1
    data,final_url,content_type=download('https://maribelhearn.com'+link,2_000_000)
    decoded,metadata=decode_native(data)
    assert [metadata[key]for key in ['character','subtype','difficulty']]==expected
    out.mkdir(parents=True);(out/'source-page.html').write_bytes(page)
    (out/(name+'.rpy')).write_bytes(data);(out/(name+'-decoded.bin')).write_bytes(decoded)
    metadata.update(status='PARSED_NOT_PLAYBACK_VERIFIED',sourcePage=page_url,sourcePageFinalUrl=final_page,
        sourcePageSha256=SHA(page),sourceUrl='https://maribelhearn.com'+link,finalUrl=final_url,
        contentType=content_type,archiveRow=rows[0],sha256=SHA(data),bytes=len(data),intactOriginalReplay=True,
        originalSuffixRetained=True,toolSha256=SHA(TOOL_SOURCE),
        completeGame=False,nativeEquivalent=False,scope='An intact independently authored public recording, decoded with original x86 instructions and checked against a separate byte-codec implementation. Source labels and six stage headers do not establish original playback, clear or all-stage coverage.')
    (out/(name+'-source.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'intake-source.py').write_bytes(TOOL_SOURCE)
    print(json.dumps({key:metadata[key]for key in ['status','sha256','bytes','stageCount','character','subtype','difficulty']}))


if __name__=='__main__':main()
