import os, sys, zipfile, traceback

zip_path = r"H:\code\thp\tools\emsdk\downloads\666337b525e673e769121856d175f6f52b8ead64-wasm-binaries.zip"
dest = r"H:\code\thp\tools\emsdk\upstream"

os.makedirs(dest, exist_ok=True)
ok = 0
failed = []
with zipfile.ZipFile(zip_path) as z:
    names = z.namelist()
    print("entries:", len(names))
    for name in names:
        try:
            z.extract(name, dest)
            ok += 1
        except Exception as e:
            failed.append((name, repr(e)))

print("extracted:", ok, "failed:", len(failed))
for n, e in failed[:40]:
    print("FAIL", n, e)
