// Print the port's own LaserState offsets so the four groups of offsets the 0x25c..0x262 family writes can be named
// instead of guessed. The original's id is at +0x80, which the port's declaration order does not predict, so the
// numbers have to come from the compiler.
import {core} from './helpers.mjs';

const c = await core();
const names = ['dispatch', 'previous', 'next', 'state', 'type', 'position', 'velocity', 'angle', 'length', 'width',
    'speed', 'offset', 'marked', 'id', 'motion', 'offscreen_timer', 'transform_index', 'active_transforms'];
console.log('sizeof(LaserState) = 0x' + c.laser_size().toString(16));
const rows = names.map((name, i) => name + '=+0x' + c.laser_offset(i).toString(16));
for (let i = 0; i < rows.length; i += 3) console.log('  ' + rows.slice(i, i + 3).join('  '));
