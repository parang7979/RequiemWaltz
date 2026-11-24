import { spectralColors } from "./requiem_chain_spirit.mjs";

const tau = Math.PI * 2;
const clamp = (u) => Math.max(0, Math.min(1, u));
const smooth = (u) => { u = clamp(u); return u * u * (3 - 2 * u); };
const shade = (u) => spectralColors[Math.round(clamp(u) * (spectralColors.length - 1))];
const blackViolet = 0xff2c091a;
const eyeLight = 0xfff9d7f6;
const gold = 0xffb2d0fa;

// Control points are x, y and the radius of that cross-section.
const tail = [
  [4, 6, 20], [7, 19, 16], [1, 31, 11], [-10, 40, 7], [-14, 48, 4.5],
  [-8, 55, 3], [4, 57, 2.2], [14, 51, 1.2], [19, 54, 0],
];
const body = [
  [9, -30, 1], [1, -24, 14], [-4, -13, 24], [-1, 0, 25],
  [6, 11, 20], [8, 18, 13], [5, 25, 7], [1, 30, 1],
];
const hornLeft = [
  [-11, 4, 8], [-19, -6, 10], [-21, -18, 7], [-27, -25, 4.5],
  [-34, -29, 2.9], [-38, -36, 1.3], [-34, -43, 0],
];
const hornRight = [
  [5, -4, 12], [13, -14, 11], [22, -23, 7.2], [28, -32, 4],
  [24, -38, 2], [28, -45, 0],
];
const backCurl = [
  [9, 6, 13], [24, 10, 8], [34, 3, 5], [39, -5, 2.5], [45, -6, 0],
];
const foreCurl = [
  [-33, 17, 0], [-28, 11, 3.2], [-22, 10, 4.7], [-15, 14, 7],
  [-4, 21, 7], [8, 21, 6], [17, 13, 4], [22, 9, 0],
];

function cubic(a, b, c, d, u) {
  return b + .5 * u * (c - a + u * (2 * a - 5 * b + 4 * c - d
    + u * (3 * b - 3 * c + d - a)));
}

function plumePoints(keys, phase, lean, flutter) {
  const last = keys.length - 1;
  const points = [];
  for (let i = 0; i <= last * 9; i++) {
    const segment = Math.min(last - 1, Math.floor(i / 9));
    const fraction = i / 9 - segment;
    const a = keys[Math.max(0, segment - 1)];
    const b = keys[segment];
    const c = keys[segment + 1];
    const d = keys[Math.min(last, segment + 2)];
    const [x, y, radius] = b.map((_, axis) => cubic(a[axis], b[axis], c[axis], d[axis], fraction));
    const tailWeight = clamp((y + 8) / 67);
    const edgeWeight = clamp(Math.abs(x) / 40);
    const shift = (2 + 6 * tailWeight + 2 * edgeWeight) * Math.sin(phase - y * .09) * flutter;
    points.push({
      x: x + shift + lean * clamp((22 - y) / 42),
      y: y + (.8 + 2.3 * edgeWeight) * Math.sin(phase + x * .12) * flutter,
      radius: Math.max(.2, radius * (1 + .11 * Math.sin(phase * 2 - y * .11))),
      u: i / (last * 9),
    });
  }
  return points;
}

function drawPlume(p, keys, phase, lean, flutter, opacity, luster) {
  const points = plumePoints(keys, phase, lean, flutter);
  // Pick the deepest sample so layered smoke stays translucent where ribbons cross.
  const pixels = new Map();
  for (let i = 0; i < points.length; i++) {
    const current = points[i];
    const { x, y, radius, u } = current;
    const before = points[Math.max(0, i - 1)];
    const after = points[Math.min(points.length - 1, i + 1)];
    const dx = after.x - before.x;
    const dy = after.y - before.y;
    const length = Math.hypot(dx, dy) || 1;
    p.each(x - radius, y - radius, x + radius, y + radius, (lx, ly, sx, sy) => {
      const distance = Math.hypot(lx - x, ly - y) / radius;
      if (distance >= 1) return;
      const key = sx + sy * p.w;
      if ((pixels.get(key)?.distance ?? 1) <= distance) return;
      const across = ((lx - x) * dy - (ly - y) * dx) / (length * radius);
      const fold = .55 + .28 * Math.sin(phase * 2 - u * 7);
      const crest = Math.exp(-((across - fold) ** 2) / .045);
      const bounce = Math.exp(-((across + .78) ** 2) / .046);
      const shimmer = (.5 + .5 * Math.sin(u * 15 - phase * 2)) ** 3;
      const glaze = Math.exp(-((across - fold - .16) ** 2) / .012) * shimmer;
      const light = (.22 + .28 * crest + .14 * bounce + .12 * across + .23 * glaze) * luster;
      const fade = .75 + .25 * Math.sin(Math.PI * u);
      const alpha = opacity * fade * clamp((1 - distance) * radius / 2);
      pixels.set(key, { sx, sy, distance, color: shade(light), alpha });
    });
  }
  for (const { sx, sy, color, alpha } of pixels.values()) p.blendPx(sx, sy, color, alpha);
}

function drawFace(p, phase, lean, concern, withdrawn) {
  const x = lean - 2 + Math.sin(phase + .3) * 1.4;
  const y = -3 + 6 * concern + Math.sin(phase - .8) * .8;
  p.each(x - 16, y - 12, x + 16, y + 13, (lx, ly, sx, sy) => {
    const dx = lx - x;
    const dy = ly - y;
    const hollow = Math.hypot(dx / 15, (dy - dx * .14) / 11);
    if (hollow >= 1) return;
    p.blendPx(sx, sy, blackViolet, (.90 - .2 * withdrawn) * clamp((1 - hollow) * 2.4));
  });

  const eyeAngle = 3 - 4 * concern;
  const blink = Math.max(.16, 1 - 1.5 * Math.exp(-((Math.cos(phase) + 1) ** 2) / .00055));
  for (const side of [-1, 1]) {
    const eyeX = x + side * 6;
    const eyeY = y + side * 1.1;
    const corner = eyeX + side * 3.7;
    p.line(eyeX - side * 2, eyeY + 1, corner, eyeY - eyeAngle, shade(.72));
    p.line(eyeX, eyeY + blink, eyeX + side * 2, eyeY - eyeAngle * .62, eyeLight);
    p.blend(eyeX, eyeY + 1.6, shade(.86), blink * .55);
  }
  const mouth = y + 7;
  p.polyline([[x - 3, mouth - 1 + concern], [x, mouth + 1 - 2 * concern],
    [x + 3, mouth - 1 + concern]], shade(.56));
  p.blend(x, y - 11, gold, (.52 + .13 * Math.sin(phase * 2)) * (1 - withdrawn * .45));
  p.blend(x + 1, y - 10, gold, .35);
}

function smallWisps(p, phase, lean, flutter) {
  for (let i = 0; i < 4; i++) {
    const angle = phase + i * 1.6;
    const x = (i % 2 === 0 ? -1 : 1) * (27 + i * 3) + lean + 3 * Math.sin(angle);
    const y = -31 + i * 14 + 5 * Math.cos(angle);
    const opacity = (.09 + .21 * Math.sin(angle) ** 2) * flutter;
    p.blend(x, y, shade(.69), opacity);
    p.blend(x + 1.5, y + 1.6, shade(.43), opacity * .74);
  }
}

export const concern = {
  meta: {
    name: "Requiem concern", size: [128, 128], origin: [64, 50],
    fps: 30, duration: 1.3, loop: false, bg: "none",
  },
  draw(p, time) {
    const phase = tau * time / 1.5;
    const reveal = smooth(time / .18);
    const concern = smooth((time - .08) / .39);
    const withdrawn = smooth((time - .83) / .45);
    const lean = concern * 5 - (1 - reveal) * 4;
    const flutter = 1 + .22 * (1 - reveal) + .36 * withdrawn;
    smallWisps(p, phase, lean, flutter);
    drawPlume(p, tail, phase, 0, flutter, .89, 1.02);
    drawPlume(p, backCurl, phase + .55, lean * .3, flutter, .67, 1.07);
    drawPlume(p, body, phase, lean, flutter, .94, .92);
    drawPlume(p, hornLeft, phase + .45, lean, flutter * 1.22, .85 - concern * .09, 1.08);
    drawPlume(p, hornRight, phase - .34, lean, flutter * .85, .90, 1.12);
    drawPlume(p, foreCurl, phase + .84, lean * .45, flutter, .81, 1.18);
    drawFace(p, phase, lean, concern, withdrawn);
  },
};
