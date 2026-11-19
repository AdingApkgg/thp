// Read-only observations drive ordinary input masks for the browser acceptance run.
// The game remains responsible for movement, collisions, stocks and progression.
const directions = [
  [0, 0, 0], [16, 0, -1], [32, 0, 1], [64, -1, 0], [128, 1, 0],
  [80, -.707, -.707], [144, .707, -.707],
  [96, -.707, .707], [160, .707, .707],
];
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

function chooseInput(hazards, state) {
  const speed = hazards.focusSpeed || 2;
  const position = hazards.position;
  const item = hazards.items
    .filter(item => item.type !== 6 && item.type !== 1 &&
      item.position[1] > 150 && item.position[1] < 420)
    .sort((a, b) => Math.hypot(a.position[0] - position[0], a.position[1] - position[1]) -
      Math.hypot(b.position[0] - position[0], b.position[1] - position[1]))[0];
  const target = item?.position ?? [hazards.boss?.[0] ?? 192, 380];
  let bestScore = -Infinity;
  let bestMask = 13;
  let bestClearance = 0;

  for (const [mask, dx, dy] of directions) {
    let clearance = 100;
    for (const bullet of hazards.bullets) {
      for (const time of [3, 6, 12, 18, 24]) {
        const x = clamp(position[0] + dx * speed * time, 8, 376);
        const y = clamp(position[1] + dy * speed * time, 16, 432);
        const bulletX = bullet.position[0] + bullet.velocity[0] * time;
        const bulletY = bullet.position[1] + bullet.velocity[1] * time;
        clearance = Math.min(clearance,
          Math.hypot(x - bulletX, y - bulletY) - Math.max(...bullet.size) * .5);
      }
    }
    if (hazards.boss) {
      clearance = Math.min(clearance, Math.hypot(
        position[0] + dx * speed * 12 - hazards.boss[0],
        position[1] + dy * speed * 12 - hazards.boss[1]) - 45);
    }
    for (const laser of hazards.lasers) {
      if (laser.mode === 2) continue;
      for (const time of [6, 18, 30]) {
        const x = clamp(position[0] + dx * speed * time, 8, 376) - laser.origin[0];
        const y = clamp(position[1] + dy * speed * time, 16, 432) - laser.origin[1];
        const along = Math.cos(laser.angle) * x + Math.sin(laser.angle) * y;
        const across = -Math.sin(laser.angle) * x + Math.cos(laser.angle) * y;
        clearance = Math.min(clearance, Math.hypot(
          Math.max(laser.tail - along, 0, along - laser.head),
          Math.max(Math.abs(across) - laser.width * .25, 0)));
      }
    }
    const x = position[0] + dx * speed * 12;
    const y = position[1] + dy * speed * 12;
    const score = clearance - Math.abs(x - target[0]) * .06 -
      Math.abs(y - target[1]) * .05 - (mask ? 1 : 0);
    if (score > bestScore) {
      bestScore = score;
      bestMask = 13 | mask;
      bestClearance = clearance;
    }
  }
  if (bestClearance < 12 && state.bombs > 0 && !state.bombActive) bestMask |= 2;
  return bestMask;
}

export async function advanceStandardBot() {
  const game = globalThis.th06ncGame;
  let state = game.report();
  let advanced = 0;
  for (let step = 0; step < 60 && state.phase === 'game'; step++) {
    if (state.playerState === 2 && state.bombs > 0) {
      await game.advance(1, 13);
      state = await game.advance(1, 15);
      advanced += 2;
      continue;
    }
    const hazards = game.hazards();
    const mask = hazards && state.dialog < 0 ? chooseInput(hazards, state) : 9;
    state = await game.advance(2, mask);
    advanced += 2;
  }
  return {...state, botTicks: advanced};
}
