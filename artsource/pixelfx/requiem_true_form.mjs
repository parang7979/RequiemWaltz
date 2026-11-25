import { spectralColors } from "./requiem_chain_spirit.mjs";

const tau = Math.PI * 2;
const cycle = 1.6;
const clamp = (u) => Math.max(0, Math.min(1, u));
const mix = (a, b, u) => a + (b - a) * u;
const smooth = (value) => {
  const u = clamp(value);
  return u * u * (3 - 2 * u);
};
const shade = (u) => spectralColors[Math.round(clamp(u) * (spectralColors.length - 1))];
const mask = 0xff2b0919;
const eyeLight = 0xffecc2f2;

// Each knot gives the center of an ectoplasm fold and its cross-section radius.
const tail = [
  [6, 10, 17], [8, 22, 14], [1, 32, 10], [-11, 41, 7], [-15, 49, 4],
  [-8, 56, 3], [3, 56, 2.2], [12, 51, 1.4], [18, 53, 0],
];
const body = [
  [8, -30, 0], [0, -24, 13], [-3, -13, 23], [1, -1, 25],
  [5, 10, 23], [6, 19, 18], [1, 28, 10], [-4, 34, 3],
];
const hood = [
  [-30, -37, 0], [-27, -30, 3], [-18, -22, 7], [-13, -12, 8],
  [-5, -8, 8], [8, -14, 10], [20, -23, 6], [26, -31, 3],
  [23, -40, 1.4], [27, -44, 0],
];
const cheek = [
  [-34, -13, 0], [-28, -13, 3], [-20, -8, 5], [-16, 1, 6],
  [-7, 7, 6.6], [4, 8, 6.5], [16, 1, 4.5], [21, -7, 0],
];
const waist = [
  [-18, 14, 0], [-13, 17, 3.7], [-4, 20, 5.5], [6, 19, 5.5],
  [16, 13, 4], [22, 8, 0],
];
const farArm = [
  [-15, 6, 9], [-23, 9, 7.5], [-30, 17, 5.8], [-38, 14, 4.5],
  [-42, 9, 4.9], [-49, 9, 1.5],
];
const nearArm = [
  [13, 4, 10], [21, 9, 8.3], [31, 16, 6.3], [39, 12, 4.5],
  [44, 5, 5.1], [50, 5, 1.2],
];
const farPalm = [[-39, 14, 3.2], [-43, 9, 3.9], [-48, 5, 1.9], [-53, 6, 0]];
const nearPalm = [[39, 12, 3.5], [45, 5, 4.4], [49, 0, 2.1], [53, 0, 0]];

function spline(a, b, c, d, u) {
  return b + .5 * u * (c - a + u * (2 * a - 5 * b + 4 * c - d
    + u * (3 * b - 3 * c + d - a)));
}

function place(x, y, radius, pose, phase, drop) {
  const tailWeight = clamp((y + 5) / 64);
  const side = clamp(Math.abs(x) / 50);
  const drift = Math.sin(phase - y * .095) * (1.2 + 5.6 * tailWeight + 1.8 * side);
  const hover = 1.3 * Math.sin(phase);
  const nod = pose.nod * clamp((22 - y) / 40);
  const arm = pose.nod * side * clamp((y + 4) / 20);
  const squash = mix(1, .27, pose.collapse);
  const twist = Math.sin(y * .093 + 7 * pose.collapse) * 8 * pose.collapse * side;
  const peel = pose.peel * side;
  return {
    x: (x + drift + twist + 4 * peel * Math.sign(x)) * squash + nod * 2.6,
    y: (y + hover + drop + arm * 10) * squash + 2 * pose.collapse - 14 * peel,
    radius: Math.max(.12, radius * squash * (1 + .09 * Math.sin(phase * 2 - y * .11))),
  };
}

function drawFold(p, keys, pose, material) {
  const { phase, opacity, luster, drop = 0 } = material;
  const last = keys.length - 1;
  const points = [];
  for (let i = 0; i <= last * 9; i++) {
    const seg = Math.min(last - 1, Math.floor(i / 9));
    const u = i / 9 - seg;
    const a = keys[Math.max(0, seg - 1)];
    const b = keys[seg];
    const c = keys[seg + 1];
    const d = keys[Math.min(last, seg + 2)];
    const [x, y, radius] = b.map((_, axis) => spline(a[axis], b[axis], c[axis], d[axis], u));
    points.push(place(x, y, radius, pose, phase, drop));
  }

  const pixels = new Map();
  for (const [i, point] of points.entries()) {
    const { x, y, radius } = point;
    const before = points[Math.max(0, i - 1)];
    const after = points[Math.min(points.length - 1, i + 1)];
    const dx = after.x - before.x;
    const dy = after.y - before.y;
    const tangent = Math.hypot(dx, dy) || 1;
    const u = i / (points.length - 1);
    p.each(x - radius, y - radius, x + radius, y + radius, (lx, ly, sx, sy) => {
      const distance = Math.hypot(lx - x, ly - y) / radius;
      if (distance >= 1) return;
      const key = sx + sy * p.w;
      if ((pixels.get(key)?.distance ?? 1) <= distance) return;
      const across = ((lx - x) * dy - (ly - y) * dx) / (tangent * radius);
      const ridge = .51 + .30 * Math.sin(phase * 2 - 8.4 * u);
      const fold = Math.exp(-((across - ridge) ** 2) / .062);
      const reflected = Math.exp(-((across + .76) ** 2) / .036);
      const glint = Math.exp(-((across - ridge - .17) ** 2) / .014)
        * (.5 + .5 * Math.sin(phase * 2 - u * 14)) ** 2;
      const brightness = (.17 + .39 * fold + .14 * reflected + .11 * across + .19 * glint) * luster;
      const skin = clamp((1 - distance) * radius / 1.8);
      const alpha = opacity * pose.opacity * (.77 + .23 * Math.sin(Math.PI * u)) * skin;
      pixels.set(key, { sx, sy, distance, color: shade(brightness), alpha });
    });
  }
  for (const { sx, sy, color, alpha } of pixels.values()) p.blendPx(sx, sy, color, alpha);
}

function face(p, pose) {
  const opacity = pose.opacity * (1 - smooth(pose.collapse * 1.75));
  const { phase, nod } = pose;
  const center = place(1.7, -10, 0, pose, phase, nod * 5);
  const x = center.x;
  const y = center.y;
  p.each(x - 14, y - 10, x + 14, y + 12, (lx, ly, sx, sy) => {
    const dx = lx - x;
    const v = ly - y - dx * .11;
    const distance = Math.hypot(dx / 13.8, v / 10.3);
    p.blendPx(sx, sy, mask, opacity * .95 * clamp((1 - distance) * 2.35));
  });

  const squint = smooth((Math.sin(phase - 1.4) - .93) / .07);
  const eyeAlpha = opacity * (1 - .85 * squint) * (1 - .30 * nod);
  for (const side of [-1, 1]) {
    const cx = x + side * 5.7;
    const cy = y + side * .9 + nod;
    for (let i = 0; i < 5; i++) {
      const u = i / 4;
      const bend = (1 - u) * (2.1 - 2.5 * nod);
      const light = mix(.38, .94, Math.sin(Math.PI * u));
      p.blend(cx + side * mix(3, -2, u), cy - bend, i === 2 ? eyeLight : shade(.81), eyeAlpha * light);
      p.blend(cx + side * mix(3, -2, u), cy - bend + 1, shade(.54), eyeAlpha * light * .47);
    }
  }
  for (let i = -3; i <= 3; i++) {
    const smile = (1 - (i / 3) ** 2) * (1.3 - 2.1 * nod);
    p.blend(x + i + 1, y + 5 + smile, shade(i === 0 ? .73 : .53), opacity * .72);
  }
}

function form(p, pose) {
  const phase = pose.phase;
  const draw = (keys, shift, opacity, luster, drop = 0) =>
    drawFold(p, keys, pose, { phase: phase + shift, opacity, luster, drop });
  draw(tail, -.08, .94, 1.08);
  draw(farArm, .80, .80, 1.08, pose.nod * 2);
  draw(farPalm, .80, .79, 1.14, pose.nod * 2);
  draw(body, 0, .95, 1.04);
  draw(hood, .44, .89, 1.20, pose.nod * 4);
  draw(cheek, -.24, .83, 1.16, pose.nod * 5);
  draw(waist, .52, .71, 1.06);
  face(p, pose);
  draw(nearArm, -.60, .94, 1.18, pose.nod * 2.8);
  draw(nearPalm, -.60, .88, 1.23, pose.nod * 2.8);
}

function neutral(p, strength, phase) {
  if (strength <= 0) return;
  const drift = Math.sin(phase) * 1.8;
  p.disc(drift, 2, 15, (d) => shade(.31 + .16 * (1 - d)), (d) => strength * (1 - d ** 1.5) * .91);
  p.disc(-drift * .55, 2.3, 7.4, shade(.46), (d) => strength * (1 - d) * .70);
  for (let strip = 0; strip < 3; strip++) {
    for (let i = 0; i < 54; i++) {
      const u = i / 53;
      const angle = phase + strip * 2.09 + u * 4.5;
      const radius = 4.5 + 10 * u + 1.6 * Math.sin(angle * 2 + phase);
      const fade = Math.sin(Math.PI * u) * strength;
      const x = Math.cos(angle) * radius + drift;
      const y = 2 + Math.sin(angle) * radius * .62;
      p.disc(x, y, 1.8 + 1.3 * u, shade(.45 + .27 * u), fade * .59);
      p.blend(x, y - 1, shade(.74 + .13 * u), fade * .76);
    }
  }
}

function shards(p, u) {
  const life = Math.sin(Math.PI * clamp(u)) ** 1.15;
  for (let i = 0; i < 17; i++) {
    const angle = i * 2.399963 + u * 1.8;
    const reach = 12 + 37 * u + i % 7;
    const x = Math.cos(angle) * reach;
    const y = -5 - 22 * u + Math.sin(angle) * (15 + 4 * u);
    const light = life * (.35 + .58 * (i % 5) / 4);
    p.blend(x, y, shade(.72 + (i % 4) * .045), light);
    p.blend(x + 1, y + 1, shade(.48), light * .57);
  }
}

function pose(time, nod = 0, collapse = 0, peel = 0, opacity = 1) {
  return { phase: tau * time / cycle, nod, collapse, peel, opacity };
}

function clip(name, duration, loop, draw) {
  return {
    meta: { name, size: [128, 128], origin: [64, 50], fps: 30, duration, loop, bg: "none" },
    draw,
  };
}

export const idle = clip("Requiem idle", cycle, true, (p, time) => {
  form(p, pose(time));
});

export const liquefy = clip("Requiem liquefies", .30, false, (p, time) => {
  const u = smooth(time / .30);
  form(p, pose(time, 0, u, 0, 1 - smooth((u - .59) / .41)));
  neutral(p, smooth((u - .37) / .63), tau * (time * 2 + u * .7));
});

export const concern = clip("Requiem concern", 1.3, false, (p, time) => {
  form(p, pose(time, smooth((time - .09) / .42)));
});

export const vanish = clip("Requiem vanishes", .40, false, (p, time) => {
  const u = clamp(time / .40);
  form(p, pose(.86 + time, 1, .37 * smooth(u), smooth(u), 1 - smooth(u)));
  shards(p, u);
});
