// Requiem Waltz original PixelFX art. ABGR palette.
const ink = 0xff882b5e;
const violet = 0xffda548d;
const orchid = 0xfff495dd;
const luminous = 0xfff7caff;
const white = 0xfff9ecff;
const brass = 0xff97c9ff;
const tau = Math.PI * 2;

export const tail = {
  meta: { name: "Requiem spirit tail", size: [82, 50], origin: [55, 27], fps: 30, duration: 0.8, loop: true },
  draw(p, t) {
    const phase = t / 0.8 * tau;
    for (let strand = 0; strand < 3; strand++) {
      const length = [47, 33, 27][strand];
      for (let x = -3; x <= length; x += 0.5) {
        const u = Math.max(0, x / length);
        const curve = (strand - 1) * u * 12 + Math.sin(u * 6.8 - phase + strand * 0.9) * u * 10;
        const y = curve + 7 * u;
        const width = (strand === 0 ? 9 : 4) * (1 - u) ** 1.15;
        for (let d = -width; d <= width; d++) {
          const band = Math.abs(d) / Math.max(1, width);
          const inkChoice = band > .67 ? ink : band > .33 ? violet : orchid;
          p.blend(-x, y + d, inkChoice, (1 - u * .53) * (1 - band * .26));
        }
        if (strand === 0 && x < length - 7) p.blend(-x, y - 1.0, luminous, (1 - u) * .77);
      }
    }
  },
};

const shiftDuration = 15 / 60;
const flameShade = 0xff852836;
const flameViolet = 0xffda4b83;
const flameLight = 0xffff86b9;
const flameRim = 0xffffb8e3;

const shiftFlames = [
  { x: -25, y: 13, reach: 38, width: 12, lag: .095, curl: -1 },
  { x: 26, y: 11, reach: 39, width: 11, lag: .14, curl: 1 },
  // Two overlapping tongues give the center flame a single base and a forked tip.
  { x: -6, y: 15, reach: 45, width: 9, lag: .05, curl: -1 },
  { x: -1, y: 17, reach: 59, width: 22, lag: .01, curl: 1 },
];

function flameEase(value) {
  const u = Math.max(0, Math.min(1, value));
  return u * u * (3 - 2 * u);
}

function drawShiftFlame(p, time, { x: rootX, y: rootY, reach, width, lag, curl }) {
  const growth = flameEase((time - lag) / .36);
  const lift = flameEase((time - .43 - lag * .55) / .43);
  const strength = growth * (1 - lift);
  if (strength <= 0) return;

  const height = reach * (.20 + .80 * growth) * (1 - .63 * lift);
  const base = Math.round(rootY - 25 * lift);
  const sway = time * tau * 1.65 + rootX * .18;
  const root = rootX * (.69 + .31 * growth) + curl * lift * 4;
  p.glow(root, base - height * .30, 7 + width * .55, flameViolet, strength * .24);
  for (let row = 0; row < height; row++) {
    const u = row / height;
    const phase = row * .20 - sway;
    const wave = Math.sin(phase);
    const x = root + u * ((3 + width * .29) * wave + (5 + width * .22) * curl * u);
    const belly = flameEase((row + 2) / 9) * (1 - u) ** .82;
    const half = width * belly * (.58 + .42 * growth) * (.88 + .12 * wave) * (1 - .49 * lift);
    const opacity = strength * (.62 + .38 * (1 - u));
    const ridge = .57 * Math.cos(phase + .85);
    const ridgePower = .60 + .40 * Math.sin(row * .28 - sway + 1);
    for (let px = Math.floor(x - half); px <= Math.ceil(x + half); px++) {
      const offset = px - x;
      const coverage = Math.max(0, Math.min(1, half + .45 - Math.abs(offset)));
      const across = offset / Math.max(1, half);
      const fold = Math.abs(across - ridge);
      let color = flameViolet;
      if (Math.abs(across) > .78) color = flameShade;
      else if (fold < .11 * ridgePower) color = flameRim;
      else if (fold < .39) color = flameLight;
      p.blend(px, base - row, color, coverage * opacity);
    }
  }
}

export const shift = {
  meta: { name: "Requiem rising spirit fire", size: [152, 94], origin: [76, 47], fps: 60, duration: shiftDuration, loop: false },
  draw(p, t) {
    const u = t / shiftDuration;
    if (u <= 0 || u >= 1) return;
    for (const flame of shiftFlames) drawShiftFlame(p, u, flame);
    for (let i = 0; i < 12; i++) {
      const age = (u - (.24 + i * .032)) / (.33 + (i % 3) * .035);
      if (age <= 0 || age >= 1) continue;
      const { x: rootX, reach, width, curl } = shiftFlames[i % shiftFlames.length];
      const x = rootX + Math.sin(i * 2.4 + age * 4) * (2 + age * 4) + curl * 3 * age;
      const y = 8 - reach * .46 - age * (26 - width * .26);
      const alpha = flameEase(age / .17) * (1 - age) * (.68 + (i % 3) * .16);
      p.blend(x, y, flameLight, alpha);
      p.blend(x, y + 1, flameViolet, alpha * .48);
      if (i % 4 === 0) {
        p.blend(x + 1, y + 1, flameViolet, alpha * .55);
        p.glow(x, y, 3, flameViolet, alpha * .22);
      }
    }
  },
};

function swordSweep(name, size, origin, degrees, reach, extension, strike, duration, thickness) {
  return {
    meta: { name, size, origin, fps: 60, duration, loop: false },
    draw(p, t) {
      // Match the sweep angles and the sword's 47.34px reach from its grip.
      if (t <= 0 || t >= duration) return;
      const phase = Math.min(1, t / strike);
      const front = phase * phase * (3 - 2 * phase);
      const fading = Math.max(0, (t - strike) / (duration - strike));
      const tail = front * Math.min(.74, fading * .74);
      const fade = (1 - fading) ** 2;
      for (let u = tail; u < front; u += .003) {
        const a = (u * 2 - 1) * degrees * Math.PI / 180;
        const radius = reach + 47.34 - 9 * (1 - u) + extension * Math.sin(Math.PI * u);
        const curve = (u - tail) / (front - tail);
        const belly = Math.sin(Math.PI * curve) ** .7;
        const width = (2 + thickness * belly) * (.56 + fade * .44);
        const alpha = fade * (.26 + .74 * curve);
        for (let depth = 0; depth < width; depth++) {
          const r = radius - depth;
          const color = depth < 2 ? white : depth < 5 ? luminous : depth < 10 ? orchid : violet;
          p.blend(Math.cos(a) * r, Math.sin(a) * r, color, alpha);
        }
        if (Math.round(u * 1000) % 17 < 3) {
          const r = radius + 3 + Math.sin(u * 83) * 3;
          p.blend(Math.cos(a) * r, Math.sin(a) * r, brass, alpha * .74);
        }
      }
    },
  };
}

export const handCut = swordSweep("Waltz-centered sword sweep", [170, 300], [4, 150], 64, 92, 12, .118, .23, 14);
export const counterCut = swordSweep("Requiem dodge counter", [240, 392], [56, 196], 105, 106, 22, .15, .28, 22);

function release(name, power, duration) {
  return {
    meta: { name, size: [128, 100], origin: [42, 50], fps: 60, duration, loop: false },
    draw(p, t) {
      const u = t / duration;
      if (u >= 1) return;
      const fade = (1 - u) ** 1.7;
      const swell = 1 - (1 - u) ** 3;
      for (let i = 0; i < 14; i++) {
        const ray = i * 2.39996;
        const vx = (21 + Math.cos(ray) * (12 + i % 13)) * power;
        const vy = Math.sin(ray) * (10 + i % 8) * power;
        const head = .25 + swell * .95;
        const start = Math.max(0, head - .52 * fade);
        p.line(vx * start, vy * start, vx * head, vy * head, i % 3 ? orchid : brass, fade);
      }
      const ring = 6 + 26 * swell;
      for (let a = 0; a < tau; a += .035) {
        if (Math.cos(a * 9) > -.5)
          p.blend(4 + Math.cos(a) * ring * .38, Math.sin(a) * ring * power, violet, fade);
      }
      if (u < .30) {
        const len = (1 - u / .30) * power;
        p.glow(4, 0, 19 * power, violet, fade * .7);
        p.line(-12 * len, 0, 25 * len, 0, white);
        p.line(0, -12 * len, 0, 12 * len, luminous);
      }
    },
  };
}

export const bowRelease = release("Bow snap", .70, .18);
export const cannonRelease = release("Cannon flash", 1.40, .30);

export const disperse = {
  meta: { name: "Requiem's severed tether", size: [144, 132], origin: [72, 86], fps: 60, duration: .54, loop: false },
  draw(p, t) {
    const u = t / .54;
    if (u <= 0 || u >= 1) return;
    const expand = 1 - (1 - u) ** 2;
    const fade = Math.min(1, u * 10) * (1 - u) ** 1.5;
    for (let strand = 0; strand < 3; strand++) {
      const side = strand - 1;
      for (let j = 2; j < 34; j++) {
        const segment = j / 34;
        const split = 8 + expand * 34;
        const x = side * split * segment + Math.sin(segment * 5 - u * 5 + strand) * (3 + u * 9);
        const y = 15 - expand * 47 - segment * (20 + expand * 12);
        const alpha = fade * Math.sin(Math.PI * segment);
        p.blend(x, y, luminous, alpha);
        p.blend(x + 1, y + 1, orchid, alpha * .78);
        if (j % 3 !== 0) p.blend(x - 1, y + 1, violet, alpha * .7);
      }
    }
    for (let i = 0; i < 26; i++) {
      const angle = i * 2.39996;
      const x = Math.cos(angle) * (6 + expand * (10 + i % 28));
      const y = Math.sin(angle) * (9 + expand * 15) - expand * (20 + i % 23);
      p.blend(x, y, i % 5 ? orchid : white, fade * (.45 + .07 * (i % 7)));
    }
  },
};
