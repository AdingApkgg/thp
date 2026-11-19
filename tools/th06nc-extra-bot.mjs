// Read-only observations drive ordinary input masks for the browser acceptance run.
// The game remains responsible for movement, collisions, stocks and progression.
const directions = [
  [0, 0, 0], [16, 0, -1], [32, 0, 1], [64, -1, 0], [128, 1, 0],
  [80, -.707, -.707], [144, .707, -.707],
  [96, -.707, .707], [160, .707, .707],
];
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

function chooseInput(hazards, state) {
  const baseSpeed = hazards.focusSpeed || 2;
  const position = hazards.position;
  // Discard only trajectories whose swept box cannot approach any candidate.
  // This bounds expensive distance calculations without changing the game.
  const reach = baseSpeed * 2 * 24 + 100;
  const bullets = hazards.bullets.filter(bullet => {
    const x = bullet.position[0], y = bullet.position[1];
    const endX = x + bullet.velocity[0] * 24;
    const endY = y + bullet.velocity[1] * 24;
    const radius = Math.max(...bullet.size) * .5;
    return Math.min(x,endX) - radius <= position[0] + reach &&
      Math.max(x,endX) + radius >= position[0] - reach &&
      Math.min(y,endY) - radius <= position[1] + reach &&
      Math.max(y,endY) + radius >= position[1] - reach;
  });
  const item = hazards.items
    .filter(item => item.type !== 6 && item.type !== 1 &&
      (state.playerPower < 128 || ![0,2,4].includes(item.type)) &&
      item.position[1] > 150 && item.position[1] < 420)
    .sort((a, b) => Math.hypot(a.position[0] - position[0], a.position[1] - position[1]) -
      Math.hypot(b.position[0] - position[0], b.position[1] - position[1]))[0];
  const target = hazards.boss && state.playerPower >= 64 && ![3,5].includes(item?.type)
    ? [hazards.boss[0],400] : item?.position ?? [hazards.boss?.[0] ?? 192,380];
  let bestScore = -Infinity;
  let bestMask = 13;
  let bestClearance = 0;

  for (const [mask, dx, dy, focus] of directions.flatMap(row => [[...row,true],[...row,false]])) {
    const speed = baseSpeed * (focus ? 1 : 2);
    let clearance = 24;
    for (const bullet of bullets) {
      for (const time of [1, 2, 4, 8, 12, 18, 24]) {
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
    const score = clearance - Math.abs(x - target[0]) * .12 -
      Math.abs(y - target[1]) * .05 - (mask ? 1 : 0) - (focus ? 0 : 1.5);
    if (score > bestScore) {
      bestScore = score;
      bestMask = (focus ? 13 : 9) | mask;
      bestClearance = clearance;
    }
  }
  // Keep bombs for actual deathbomb windows, sampled every two ticks.
  // Long-horizon proximity alone should not spend a limited Extra stock.
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
    let mask = hazards && state.dialog < 0 ? chooseInput(hazards, state) : 9;
    if (hazards && state.dialog < 0 && state.playerPower < 64 &&
        state.bombs === 3 && !state.bombActive && hazards.bullets.length >= 30) mask |= 2;
    state = await game.advance(2, mask);
    advanced += 2;
  }
  return {...state, botTicks: advanced};
}
