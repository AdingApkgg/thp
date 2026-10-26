"""Bounded TH14 test storage; original game files are never hardlinked."""
from pathlib import Path
import hashlib,json,os,shutil,stat,time

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'artifacts/th14/shared-immutable-native-cache'

def sha256_file(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def clone_immutable(source,target):
    source=Path(source).resolve(strict=True);target=Path(target).resolve()
    assert target.is_relative_to((ROOT/'artifacts/th14').resolve()) and not target.exists()
    digest=sha256_file(source);CACHE.mkdir(parents=True,exist_ok=True);canonical=CACHE/(digest+'.bin')
    if not canonical.exists():
        temporary=CACHE/(digest+'.'+str(os.getpid())+'.tmp')
        assert not temporary.exists();shutil.copyfile(source,temporary)
        try:
            assert sha256_file(temporary)==digest
            os.replace(temporary,canonical)
        finally:
            if temporary.exists():temporary.unlink()
    else:assert sha256_file(canonical)==digest
    os.chmod(canonical,stat.S_IREAD);os.link(canonical,target)
    assert os.path.samefile(canonical,target)
    return digest

def check_budget(directory,minimum_free=100*1024**3,maximum_case=2*1024**3):
    directory=Path(directory).resolve();assert directory.is_relative_to((ROOT/'artifacts/th14').resolve())
    used=0
    for current,folders,files in os.walk(directory,followlinks=False):
        folders[:]=[name for name in folders if not (Path(current)/name).is_junction() and not (Path(current)/name).is_symlink() and not(Path(current)==directory and name=='work')]
        for name in files:
            path=Path(current)/name
            # Active compilers atomically rename/unlink temporary objects after
            # os.walk lists them. Only an already-removed entry may be skipped;
            # permission, I/O and other errors must still stop the operation.
            try:metadata=path.lstat()
            except FileNotFoundError:continue
            if not stat.S_ISLNK(metadata.st_mode):used+=metadata.st_size
    free=shutil.disk_usage(directory).free
    if free<minimum_free or used>maximum_case:
        result=dict(storageBudgetExceeded=True,freeBytes=free,minimumFreeBytes=minimum_free,caseObservationBytes=used,maximumCaseBytes=maximum_case,checkedUnixSeconds=time.time(),originalGameInputsOrCodeChanged=False)
        (directory/'storage-limit.json').write_text(json.dumps(result,indent=2)+'\n')
        raise RuntimeError('TH14 capture storage budget exceeded; preserve disk reserve and retained observations')
    return used
