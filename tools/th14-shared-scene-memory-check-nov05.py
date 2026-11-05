"""Inspect actual Wasm memory types, not only build flags or JS buffers."""
from pathlib import Path
import argparse, hashlib, json
R = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()


def memories(data):
    assert data[:8] == b'\0asm\x01\0\0\0'
    position = 8

    def number():
        nonlocal position
        value, shift = 0, 0
        while True:
            byte = data[position]
            position += 1
            value |= (byte & 127) << shift
            if not byte & 128:
                return value
            shift += 7
            assert shift <= 63

    def name():
        nonlocal position
        size = number()
        result = data[position:position+size].decode('utf8')
        position += size
        return result

    def limits():
        flags = number()
        assert not flags & 4, 'Expected wasm32'
        minimum = number()
        maximum = number() if flags & 1 else None
        return dict(flags=flags, minimumPages=minimum, maximumPages=maximum, shared=bool(flags & 2))

    result = []
    while position < len(data):
        section = data[position]
        position += 1
        size = number()
        end = position + size
        if section == 2:
            for _ in range(number()):
                module, field = name(), name()
                kind = data[position]
                position += 1
                if kind == 0:
                    number()
                elif kind == 1:
                    assert data[position] in [0x70, 0x6f]
                    position += 1
                    limits()
                elif kind == 2:
                    result.append(dict(imported=True, module=module, name=field, **limits()))
                elif kind == 3:
                    position += 2
                elif kind == 4:
                    position += 1
                    number()
                else:
                    raise AssertionError('Unknown import kind')
        elif section == 5:
            for _ in range(number()):
                result.append(dict(imported=False, **limits()))
        assert position <= end
        position = end
    return result


def main(output):
    output = output.resolve()
    assert output.is_relative_to(R / 'artifacts/th14') and not output.exists()
    rows = []
    for path, shared in [('artifacts/th14/stage-restore-delivery-nov05/browser-build/th14-sdl.wasm', False),
                         ('artifacts/th14/shared-scene-copy-nov05/session-build/session.wasm', True),
                         ('artifacts/th14/shared-scene-copy-nov05/browser-build/th14-sdl.wasm', True)]:
        data = (R / path).read_bytes()
        types = memories(data)
        assert len(types) == 1 and types[0]['shared'] is shared
        assert types[0]['maximumPages'] == 16384
        rows.append(dict(path=path, sha256=SHA(data), memories=types))
    output.write_text(json.dumps(dict(actualMemoryTypesVerified=True, unsharedControlPreserved=True, rows=rows,
                                     toolSha256=SHA(Path(__file__).read_bytes()), ordinaryBrowserAccepted=False, completeGame=False), indent=2) + '\n')
    print(json.dumps(dict(actualSharedMemoryTypes=2, unsharedControls=1, completeGame=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
