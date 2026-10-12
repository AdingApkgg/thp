#!/usr/bin/env python3
"""Print the one-line summary of a browser-run record. Usage: read-boot.py <record.json> [label]"""
import io
import json
import sys

label = sys.argv[2] if len(sys.argv) > 2 else ''
record = json.load(io.open(sys.argv[1], encoding='utf-8'))
health = (record.get('dom') or {}).get('health')
print('  %s click=%s started=%s clicks=%s stageMax=%s phaseMax=%s %ss frames=%s '
      'errors %s/%s consoleMessages=%d' % (
          label, record.get('clicked'), record.get('started'), record.get('clicks'),
          record.get('stageMax'), record.get('phaseMax'), record.get('seconds'),
          record.get('framesServed'), record.get('pageErrors'), record.get('consoleErrors'),
          len(record.get('console') or [])))
print('  %s health=%s  unmet=%s' % (label, health, record.get('required')))
