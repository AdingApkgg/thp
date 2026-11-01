"""Read only the isolated capture's accepted config and native master levels."""
from pathlib import Path
import argparse, ctypes as C, datetime, hashlib, json, struct, time
from ctypes import wintypes as W

R = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
EXPECTED = 'f08e885e28d2e0fc8c579e88034dd7de8f2a648d8f08ce781cf08eadc9ffe353'


def observe(home):
    home = home.resolve(strict=True)
    assert home.is_relative_to(R / 'artifacts/th14')
    start_path = home / 'process-start.json'
    started = json.loads(start_path.read_bytes())
    executable = (home / 'work/th14.exe').resolve(strict=True)
    assert Path(started['exe']).resolve(strict=True) == executable and started['onlyOwnCreatedProcess']
    assert SHA(executable.read_bytes()) == EXPECTED
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = W.BOOL
    kernel.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    kernel.ReadProcessMemory.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    # PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ. No write, injection,
    # thread-context or suspension privileges are requested.
    handle = kernel.OpenProcess(0x1010, False, started['pid'])
    assert handle, C.get_last_error()
    try:
        path, capacity = C.create_unicode_buffer(32768), W.DWORD(32768)
        assert kernel.QueryFullProcessImageNameW(handle, 0, path, C.byref(capacity)), C.get_last_error()
        assert Path(path.value).resolve(strict=True) == executable

        def read(address, length):
            data, count = C.create_string_buffer(length), C.c_size_t()
            assert kernel.ReadProcessMemory(handle, address, data, length, C.byref(count)), C.get_last_error()
            assert count.value == length
            return data.raw

        samples = []
        for index in range(2):
            config = read(0x4d9134, 0x5c)
            masters = struct.unpack('<2i', read(0x4fd1ac, 8))
            assert struct.unpack_from('<I', config)[0] == 0x140002
            assert list(config[0x22:0x24]) == [0, 0] and masters == (0, 0)
            samples.append(dict(hostMonotonicNs=time.monotonic_ns(), musicConfig=config[0x22],
                                effectsConfig=config[0x23], musicMaster=masters[0], effectsMaster=masters[1]))
            if index == 0:
                time.sleep(.05)
    finally:
        kernel.CloseHandle(handle)
    return dict(verifiedActualNativeMasterLevelsZero=True, nativePid=started['pid'],
                nativeExecutableSha256=EXPECTED, ownIsolatedExecutablePathVerified=True,
                processStartSha256=SHA(start_path.read_bytes()), samples=samples,
                readOnlyAddresses=[dict(address=0x4d9134, bytes=0x5c), dict(address=0x4fd1ac, bytes=8)],
                processAccessMask=0x1010, gameOrConfigOrAudioValuesWritten=False,
                instructionsPatched=False, threadsSuspended=False, valuesProvidedToEngine=False,
                physicalEndpointOrPcmMeasurementAccepted=False, completeGame=False, nativeEquivalent=False,
                utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), toolSha256=SHA(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') and not output.exists()
    result = observe(args.native)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({key: value for key, value in result.items() if key not in ['samples', 'readOnlyAddresses']}))
