"""Snapshot the supplied sites' published catalogs; never download game data.

HTML mentions are not releases. A title is listed as available only when it
occurs in both release-catalog.json and host-manifest.json with a runtime.
Availability here means published metadata, not a playability assertion.
"""
import argparse
import datetime
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITES = ['https://api.steinsgateon.com/', 'https://touhou.vip/', 'https://beta.touhou.vip/']
SCOPE = ROOT/'docs/porting/port-scope.json'


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent':'thp-reference-survey/1'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def survey(games_root):
    sites = []
    published = set()
    for base in SITES:
        catalog = fetch(base+'release-catalog.json')
        manifest = fetch(base+'host-manifest.json')
        if catalog.get('schema') != 'eagler-touhou/release-catalog/1' or manifest.get('protocol') != 'eagler-touhou/1':
            raise ValueError(f'{base}: unexpected catalog or protocol')
        games = {game:{'revision':entry['revision'], 'descriptor':entry['descriptor'],
                        'runtime':manifest['games'][game]['runtime']}
                 for game,entry in catalog['games'].items()
                 if manifest.get('games',{}).get(game,{}).get('runtime')}
        sites.append({'url':base,'catalog':base+'release-catalog.json',
                      'manifest':base+'host-manifest.json','games':games})
        published.update(games)
    titles = []
    for suffix in json.loads(SCOPE.read_text(encoding='utf-8'))['directories']:
        game='th'+suffix
        folder=games_root/suffix
        local=folder
        titles.append({'game':game,'category':'windows-variant' if suffix=='06nc' else 'windows-mainline',
                       'publishedBy':[site['url'] for site in sites if game in site['games']],
                       'missingFromReferences':game not in published,
                       'localDirectory':str(local) if local.is_dir() else None,
                       'localExecutable':str(folder/(game+'.exe')) if (folder/(game+'.exe')).is_file() else None,
                       'workspaceTarget':(ROOT/'runtimes'/game/'target.json').is_file() or (ROOT/'runtimes'/game/(game+'_web')/'target.json').is_file()})
    return {'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope':'Only user-supplied directories in port-scope.json, excluding published titles; TH06 New Classic is a separate target. Metadata availability only.',
            'sites':sites,'titles':titles,'missing':[row['game'] for row in titles if row['missingFromReferences']]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--games-root',type=Path,default=Path('H:/Games/th'))
    parser.add_argument('--out',type=Path,default=ROOT/'docs/porting/reference-coverage.json')
    args=parser.parse_args()
    result=survey(args.games_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for site in result['sites']:
        print(site['url'], ', '.join(site['games']))
    print('Missing:',', '.join(result['missing']))
    print('Wrote',args.out)


if __name__=='__main__':
    main()
