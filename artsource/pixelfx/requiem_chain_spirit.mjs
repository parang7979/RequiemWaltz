// Indigo shadows and lavender folds taken from Requiem's other forms.
const colors = [
  0xff330d20, 0xff491732, 0xff642348, 0xff7d335c, 0xffa44878,
  0xffbf6095, 0xffdc82b3, 0xfff5b5de,
];
const eyeLight = 0xfffbd7f0;
const clamp = (n) => Math.max(0, Math.min(1, n));
const lerp = (a, b, t) => a + (b - a) * t;
const shade = (value) => colors[Math.round(clamp(value) * (colors.length - 1))];

// Each strip is a cross-section of one fold, from the loose plume into the chain.
const upperFold = [
  [-43, -17, 0], [-36, -18, 2], [-31, -16, 4], [-24, -12, 6],
  [-17, -11, 7], [-10, -8, 5], [-4, -3, 2], [2, 0, 0],
];
const core = [
  [-44, 5, 0], [-38, 4, 4], [-33, 1, 9], [-26, -2, 13],
  [-19, -3, 13], [-12, -1, 10], [-6, 1, 7], [1, 1, 4], [10, 2, 0],
];
const horn = [
  [-25, -9, 0], [-19, -14, 3], [-13, -17, 3.5], [-7, -19, 2.5], [-3, -25, 0],
];
const lowerFold = [
  [-40, 14, 0], [-34, 14, 2], [-27, 14, 4], [-21, 14, 4],
  [-15, 11, 4], [-8, 7, 3], [2, 4, 2], [9, 2, 0],
];

function ribbon(p, origin, keys, phase, opacity, brightness) {
  const first = keys[0][0];
  const last = keys.at(-1)[0];
  let segment = 1;
  for (let x = first; x <= last; x++) {
    while (keys[segment][0] < x) segment++;
    const [ax, ay, ar] = keys[segment - 1];
    const [bx, by, br] = keys[segment];
    const u = (x - ax) / (bx - ax);
    const sway = Math.sin(phase + x * .14) * clamp(-x / 39) * 2.1;
    const center = lerp(ay, by, u) + sway;
    const width = lerp(ar, br, u) * (1 + .1 * Math.sin(phase * 2 + x * .19));
    if (width < .35) continue;
    const ridge = -.4 + .25 * Math.sin(phase * 2 + x * .24);
    const reflected = .61 + .1 * Math.cos(phase + x * .2);
    for (let y = Math.ceil(center - width); y <= center + width; y++) {
      const v = (y - center) / width;
      const skin = Math.exp(-((v - ridge) ** 2) / .07);
      const rim = Math.exp(-((v - reflected) ** 2) / .035);
      const fold = .19 + .55 * skin + .15 * rim - .13 * v;
      const alpha = opacity * clamp((1 - Math.abs(v)) * width / 1.5);
      p.blend(origin.x + x, origin.y + y, shade(fold * brightness), alpha);
    }
  }
}

function face(p, origin, phase) {
  const cx = origin.x - 24;
  const cy = origin.y + 2 + .7 * Math.sin(phase);
  p.each(cx - 11, cy - 7, cx + 11, cy + 8, (x, y, sx, sy) => {
    const dx = x - cx;
    const dy = y - cy;
    const radius = Math.hypot(dx / 10.6, (dy + dx * .14) / 6.8);
    if (radius >= 1) return;
    p.blendPx(sx, sy, shade(dy > 4 ? .18 : .03), .91 * clamp((1 - radius) * 2.6));
  });
  const glimmer = .86 + .09 * Math.sin(phase * 2);
  p.polyline([[cx - 7, cy - 2], [cx - 4, cy], [cx - 2, cy]], colors[5]);
  p.polyline([[cx + 2, cy - 1], [cx + 4, cy - 2], [cx + 6, cy - 4]], colors[6]);
  p.blend(cx - 4, cy - 1, eyeLight, glimmer);
  p.blend(cx + 4, cy - 2, eyeLight, glimmer);
  p.polyline([[cx - 2, cy + 4], [cx + 1, cy + 4], [cx + 3, cy + 2]], colors[4]);
}

function wisps(p, origin, phase) {
  for (let i = 0; i <= 60; i++) {
    const u = i / 60;
    const fade = Math.sin(Math.PI * u) ** 1.8;
    const coil = Math.sin(u * 6 - phase);
    const upper = lerp(-17, -4, u) - 8 * fade + 2.2 * coil;
    const lower = lerp(13, 5, u) + 7 * fade - 2.5 * coil;
    p.blend(origin.x - 42 + 43 * u, origin.y + upper, colors[5], fade * .34);
    p.blend(origin.x - 38 + 48 * u, origin.y + lower, colors[4], fade * .44);
  }
}

export function drawSpectralSpirit(p, chain, phase) {
  const origin = chain[0];
  wisps(p, origin, phase);
  ribbon(p, origin, upperFold, phase, .73, .83);
  ribbon(p, origin, horn, phase + .8, .84, 1.02);
  ribbon(p, origin, core, phase, .94, 1);
  ribbon(p, origin, lowerFold, phase - .85, .80, .93);
  face(p, origin, phase);

  // The first rings emerge from this taper rather than docking to a hard clasp.
  for (const point of chain) {
    if (point.length > 22) break;
    const taper = 1 - point.length / 22;
    const flow = .5 + .5 * Math.cos(point.length * .34 - phase * 2);
    const y = point.y - taper * Math.sin(point.length * .34 - phase * 2);
    p.disc(point.x, y, .8 + 3.7 * taper, colors[2], .19 + .34 * taper);
    p.blend(point.x, y - 1, shade(.52 + .27 * flow), .59 * taper);
  }
  for (const point of chain) {
    if (point.length > 38) break;
    const u = point.length / 38;
    const light = Math.sin(Math.PI * u) ** 1.7;
    const curl = Math.sin(u * 8 - phase * 2);
    p.blend(point.x, point.y + light * curl * 5, colors[6], light * .42);
  }
}

export function drawSpectralLink(p, x, y, angle, faceOn, strength, phase) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const width = faceOn ? 4.9 : 2.8;
  const twist = Math.sin(phase);
  p.each(x - 10, y - 10, x + 10, y + 10, (px, py, sx, sy) => {
    const dx = px - x;
    const dy = py - y;
    const u = (dx * cos + dy * sin) / 6.7;
    const v = (-dx * sin + dy * cos) / width - .14 * Math.sin(u * 3 + phase);
    const radius = Math.hypot(u, v);
    const inner = .52 + .08 * twist * u;
    if (radius < inner || radius >= 1.05) return;
    const rounded = Math.sin(Math.PI * clamp((radius - inner) / (1.05 - inner)));
    const vein = Math.exp(-((radius - (.73 + .07 * twist)) ** 2) / .017);
    const sheen = (.5 + .5 * Math.cos(u * 2.2 + phase)) * (.54 - v * .46);
    const color = shade(.16 + .25 * rounded - .15 * v + vein * (.12 + .37 * sheen));
    p.blendPx(sx, sy, color, strength * (.33 + .60 * rounded));
  });
}
