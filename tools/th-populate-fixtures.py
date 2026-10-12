#!/usr/bin/env python3
"""Populate a runtime's oracle fixture directory from the data that runtime already extracted.

The oracle differential tests under `tests/cpp` read original game files by name from
`runtimes/<title>/<title>_web/reference/assets` (`text.anm`, `st01_00a.msg`, `demo0.rpy`, ...),
and that directory is gitignored because the bytes belong to the game. The same files are already
staged by the port's own build under `artifacts/cpp/<title>-data`, so the fixtures can be made from
the port's extraction instead of a separate one.

Usage: th-populate-fixtures.py th12 [th13 ...]
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    for title in sys.argv[1:]:
        source = os.path.join(ROOT, 'runtimes', title, '%s_web' % title, 'artifacts', 'cpp',
                              '%s-data' % title)
        target = os.path.join(ROOT, 'runtimes', title, '%s_web' % title, 'reference', 'assets')
        if not os.path.isdir(source):
            print('  %s: no staged data at %s' % (title, source))
            continue
        os.makedirs(target, exist_ok=True)
        copied = 0
        for name in sorted(os.listdir(source)):
            path = os.path.join(source, name)
            if os.path.isfile(path):
                shutil.copyfile(path, os.path.join(target, name))
                copied += 1
        print('  %s: %d fixture file(s) -> %s' % (title, copied, target))


if __name__ == '__main__':
    main()
