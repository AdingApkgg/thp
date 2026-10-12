# The state map of title 16: where the original writes, how many handlers write there, and how many
# distinct delta shapes live in each place. The flag slots are already covered op by op (sections
# 325..328); this orders the rest of the state by how much behaviour is in it, so the port's next
# work is chosen by a number and not by reading around.
import json
from collections import defaultdict, Counter

C = json.load(open(r'artifacts/th16/anm-native-all.json', encoding='utf-8'))['cases']
slots = defaultdict(lambda: {'ops': set(), 'deltas': Counter(), 'mask': 0})
per_op = defaultdict(set)
for x in C:
    a = bytes.fromhex(x['before'])
    b = bytes.fromhex(x['context'])
    for i in range(0, min(len(a), len(b)) - 3, 4):
        d = int.from_bytes(a[i:i + 4], 'little') ^ int.from_bytes(b[i:i + 4], 'little')
        if d:
            s = slots[i]
            s['ops'].add(x['op'])
            s['deltas'][d] += 1
            s['mask'] |= d
            per_op[x['op']].add(i)

order = sorted(slots.items(), key=lambda kv: (-len(kv[1]['ops']), kv[0]))
print('  slots written somewhere: %d; ops: %d; mean slots per op: %.2f'
      % (len(slots), len(per_op), sum(len(v) for v in per_op.values()) / len(per_op)))
print('  the two flag slots, in order of how many handlers write there')
for off, s in order[:18]:
    top = ', '.join('0x%x x%d' % (d, n) for d, n in s['deltas'].most_common(3))
    print('    0x%-6x ops %-4d delta shapes %-4d touch mask 0x%08x   common: %s'
          % (off, len(s['ops']), len(s['deltas']), s['mask'], top))
print('  slots whose deltas are all one shape (one port rule would cover them): %d of %d'
      % (sum(1 for _, s in slots.items() if len(s['deltas']) == 1), len(slots)))
print('  ops touching the most slots: %s'
      % ', '.join('%s:%d' % (op, len(v)) for op, v in sorted(per_op.items(),
                key=lambda kv: -len(kv[1]))[:8]))
