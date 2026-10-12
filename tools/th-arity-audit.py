"""Audit binding arity: a call with fewer arguments than the binding has parameters passes zero.

Section 88's defect was a three-argument call to a four-parameter binding, and the missing argument
was the archive generation: the compiler could not complain, the call succeeded, and the wrong cipher
table was used 184 times before anything refused. That class is mechanical, so it is worth finding by
machine rather than by reading: this parses the API table in the runtime's test bindings and compares
each binding's parameter count with the argument count of every call in every suite.

It reports candidates, not defects: a trailing parameter is only a defect when zero is a wrong value
for it, and that judgement needs the binding. What the audit removes is the possibility of never
noticing.
"""
import io
import json
import os
import re

BINDINGS = os.environ.get('TH_BINDINGS', 'runtimes/th12/th12_web/tests/cpp/core-exports.cpp')
SUITES = os.environ.get('TH_SUITES', 'runtimes/th12/th12_web/tests/cpp')
NATIVE = {'c': 'core, helpers', 'm': 'oracle'}


def split_arguments(text):
    """Split a call's argument list on top-level commas."""
    if not text.strip():
        return []
    parts, depth, current, quote = [], 0, [], None
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in '"\'`':
            quote = ch
            current.append(ch)
        elif ch in '([{':
            depth += 1
            current.append(ch)
        elif ch in ')]}':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(ch)
    parts.append(''.join(current))
    return [part.strip() for part in parts if part.strip()]


def bindings():
    text = io.open(BINDINGS, encoding='utf-8').read()
    table = {}
    for match in re.finditer(r'API\((\w+)\)\s+[\w:<>\*&\s]+?\b(\w+)\s*\(([^)]*)\)\s*\{', text):
        name, parameters = match.group(2), split_arguments(match.group(3))
        table[name] = len([p for p in parameters if p not in ('void', '')])
    # a second form: the API macro on the same line, as in `API(x) int x(...)`
    for match in re.finditer(r'API\((\w+)\)([^\n{]*?)\(([^)]*)\)\s*\{', text):
        if match.group(1) in table:
            continue
        parameters = split_arguments(match.group(3))
        table[match.group(1)] = len([p for p in parameters if p not in ('void', '')])
    return table


def main():
    table = bindings()
    print('  bindings parsed: %d' % len(table))
    rows = []
    for name in sorted(os.listdir(SUITES)):
        if not name.endswith('.test.mjs'):
            continue
        path = os.path.join(SUITES, name)
        text = io.open(path, encoding='utf-8').read()
        for match in re.finditer(r'\b([cm])\.(\w+)\s*\(', text):
            owner, function = match.group(1), match.group(2)
            if function not in table:
                continue
            depth, cursor = 1, match.end()
            while cursor < len(text) and depth:
                ch = text[cursor]
                if ch in '([{':
                    depth += 1
                elif ch in ')]}':
                    depth -= 1
                elif ch in '"\'`':
                    quote = ch
                    cursor += 1
                    while cursor < len(text) and text[cursor] != quote:
                        if text[cursor] == '\\':
                            cursor += 1
                        cursor += 1
                cursor += 1
            arguments = split_arguments(text[match.end():cursor - 1])
            if len(arguments) < table[function]:
                line = text[:match.start()].count('\n') + 1
                rows.append({'suite': name, 'line': line, 'owner': owner,
                             'binding': function, 'needs': table[function],
                             'passed': len(arguments),
                             'call': re.sub(r'\s+', ' ', match.group(0) +
                                           text[match.end():cursor - 1] + ')')[:110]})
    print('  calls with fewer arguments than the binding has parameters: %d' % len(rows))
    by_binding = {}
    for row in rows:
        by_binding.setdefault(row['binding'], []).append(row)
    for binding in sorted(by_binding, key=lambda b: (-len(by_binding[b]), b)):
        group = by_binding[binding]
        print('    %-28s needs %d, short calls %3d  suites %s'
              % (binding, group[0]['needs'], len(group),
                 ', '.join(sorted({row['suite'] for row in group})[:3])))
    io.open('tools/tmp/arity-310.json', 'w', encoding='utf-8').write(
        json.dumps({'bindings': table, 'count': len(rows), 'calls': rows}, indent=2) + '\n')
    for row in rows[:12]:
        print('    e.g. %s:%d %s' % (row['suite'], row['line'], row['call']))


main()
