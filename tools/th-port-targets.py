"""Inventory every missing reference-site title without manufacturing a runtime.

Writes metadata only. Original executables, disk images and archives remain in
--games-root. Existing target.json files are never overwritten.
"""
import argparse
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('survey', ROOT/'tools/th-target-survey.py')
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)
FIGHTERS = {'075', '105', '123'}
PAKS = {'135', '145', '155'}
PC98 = {'01':'reiiden', '02':'humaroku', '03':'yumeziku', '04':'genso', '05':'kaiki'}


def file_record(path):
    with path.open('rb') as stream:
        head = stream.read(32)
    return {'path':path.as_posix(), 'bytes':path.stat().st_size, 'headerHex':head.hex()}


def executable(path):
    record = file_record(path)
    blob = path.read_bytes()
    if blob[:2] != b'MZ' or len(blob)<64:
        raise ValueError(f'{path}: not a DOS/PE executable')
    pe = struct.unpack_from('<I', blob, 0x3c)[0]
    if pe+56>len(blob) or blob[pe:pe+4]!=b'PE\0\0':
        raise ValueError(f'{path}: invalid PE header')
    magic = struct.unpack_from('<H', blob, pe+24)[0]
    base = struct.unpack_from('<I' if magic==0x10b else '<Q', blob, pe+(52 if magic==0x10b else 48))[0]
    record.update(sha256=survey.digest(path), imageBase=f'0x{base:08x}',
                  machine=f'0x{struct.unpack_from("<H",blob,pe+4)[0]:04x}',
                  titleString=survey.title_string(str(path)))
    return record


def inspect(game, games_root):
    suffix = game[2:]
    family = ('zun-th06nc' if suffix=='06nc' else 'pc98' if suffix in PC98 else 'tasofro-dat' if suffix in FIGHTERS
              else 'tasofro-tfpk' if suffix in PAKS else 'tasofro-cg' if suffix=='175' else 'zun-tha1')
    folder = games_root/('01~05/dosbox-x' if family=='pc98' else suffix)
    target = {'game':game, 'engineFamily':family, 'completeGame':False,
              'dataArchives':{}, 'blockers':[]}
    if not folder.is_dir():
        target['blockers'].append('Original installation is missing.')
        return target
    if family=='pc98':
        disk = folder/'jp.hdi'
        if disk.is_file():
            row = file_record(disk)
            head = bytes.fromhex(row['headerHex'])
            _,_,header_size,data_size,sector_size,sectors,heads,cylinders = struct.unpack('<8I',head)
            if header_size+data_size!=row['bytes'] or sector_size*sectors*heads*cylinders!=data_size:
                raise ValueError(f'{disk}: inconsistent HDI geometry')
            row.update(sha256=survey.digest(disk),format='HDI',headerBytes=header_size,
                       diskBytes=data_size,sectorBytes=sector_size,sectorsPerTrack=sectors,
                       heads=heads,cylinders=cylinders)
            target['diskImage']=row
            target['boot']={'config':(folder/(game+'_jp.conf')).as_posix(),
                            'directory':PC98[suffix],'command':'game',
                            'evidence':'Existing local DOSBox-X configuration; browser execution not verified.'}
        else:
            target['blockers'].append('Japanese PC-98 disk image is missing.')
        target['blockers'].append('PC-98 browser runtime and game execution are not implemented.')
        return target
    exe = folder/('th123_beta.exe' if suffix=='123' else 'game.exe' if suffix=='175' else game+'.exe')
    if exe.is_file():
        record=executable(exe)
        target.update(executable=record['path'],sha256=record['sha256'],size=record['bytes'],
                      imageBase=record['imageBase'],machine=record['machine'],
                      evidence='Executable title string: '+repr(record['titleString']))
    else:
        target['blockers'].append('Original executable is missing.')
    if family=='zun-th06nc':
        archives=sorted((folder/'data').glob('*.dat'))
        target['resourceReader']='shared/th06nc/pkgl.mjs'
        target['blockers'].append('New Classic x64 gameplay, ECL/ANM semantics, DDS rendering and custom audio remain unverified.')
        if not archives:
            target['blockers'].append('PKGL archives are missing.')
    elif family=='zun-tha1':
        archives=[folder/(game+'.dat')]
    elif family=='tasofro-dat':
        archives=sorted(folder.glob(game+'*.dat'))
    elif family=='tasofro-tfpk':
        archives=sorted(folder.glob(game+'*.pak'))
    else:
        archives=[folder/'data.cga',folder/'data.cgb']
    for path in archives:
        if not path.is_file():
            target['blockers'].append('Archive missing: '+path.name)
            continue
        row=file_record(path)
        head=bytes.fromhex(row['headerHex'])
        if family=='zun-th06nc':
            pkgl_spec=importlib.util.spec_from_file_location('pkgl',ROOT/'tools/th06nc-pkgl.py')
            pkgl=importlib.util.module_from_spec(pkgl_spec)
            pkgl_spec.loader.exec_module(pkgl)
            row.update(format='PKGL',entries=len(pkgl.directory(path)))
        elif family=='zun-tha1':
            row.update(format='THA1',pbgVersion=int(suffix),entries=survey.archive_header(str(path)),
                       sha256=survey.digest(path))
        elif family=='tasofro-dat':
            count=struct.unpack_from('<H',head)[0]
            length=count*108 if suffix=='075' else struct.unpack_from('<I',head,2)[0]
            fixed=2 if suffix=='075' else 6
            if not count or length+fixed>row['bytes']:
                raise ValueError(f'{path}: invalid DAT directory size')
            row.update(format='Tasofro DAT',pbgVersion=int(suffix),entries=count,directoryBytes=length+fixed)
        elif family=='tasofro-tfpk':
            if head[:4]!=b'TFPK':
                raise ValueError(f'{path}: expected TFPK signature')
            row.update(format='TFPK',formatVersion=head[4])
        else:
            row.update(format='unidentified CG archive')
        target['dataArchives'][path.name]=row
    if family=='zun-tha1' and (folder/'thbgm.dat').is_file():
        target['dataArchives']['thbgm.dat']=file_record(folder/'thbgm.dat')
    target['blockers'].append('Per-title instruction semantics, gameplay and browser acceptance remain unverified.')
    if family in ('tasofro-tfpk','tasofro-cg') and not (ROOT/'shared/tasofro/archives.mjs').is_file():
        target['blockers'].append('This archive format does not yet have a runtime decoder.')
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games-root',type=Path,default=Path('H:/Games/th'))
    parser.add_argument('--write-targets',action='store_true')
    parser.add_argument('--refresh-missing-targets',action='store_true',help='Replace only missing-installation placeholders when an original executable is now present.')
    args=parser.parse_args()
    coverage=json.loads((ROOT/'docs/porting/reference-coverage.json').read_text(encoding='utf-8'))
    rows=[]
    for game in coverage['missing']:
        target=inspect(game,args.games_root)
        path=ROOT/'runtimes'/game/('th12_web/target.json' if game=='th12' else 'target.json')
        created=False
        refresh=False
        if args.refresh_missing_targets and path.exists() and target.get('executable'):
            previous=json.loads(path.read_text(encoding='utf-8'))
            refresh=not previous.get('executable') and previous.get('blockers')==['Original installation is missing.']
        if (args.write_targets and not path.exists()) or refresh:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(target,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            created=True
        rows.append({'game':game,'family':target['engineFamily'],
                     'target':path.relative_to(ROOT).as_posix() if path.exists() else None,
                     'originalAvailable':bool(target.get('executable') or target.get('diskImage')),
                     'archives':target['dataArchives'],'diskImage':target.get('diskImage'),
                     'blockers':target['blockers']})
        print(game,target['engineFamily'],'original='+str(rows[-1]['originalAvailable']),
              'archives='+str(len(target['dataArchives'])),'created' if created else '')
    out=ROOT/'docs/porting/port-targets.json'
    out.write_text(json.dumps({'scopeSource':'reference-coverage.json','titles':rows},
                             ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
