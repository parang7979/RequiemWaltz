import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const forms = JSON.parse(readFileSync(resolve(root, "assets/actors/requiem_forms/clips.json"), "utf8"));
const pommel = [3, forms.clips.sword.pivot[1]];
const tip = forms.sword_tip[0] + forms.clips.sword.pivot[0] - pommel[0];
const edge = forms.sword_edge_from + forms.clips.sword.pivot[0] - pommel[0];

const timing = {
  windup: .24, launch: .40, fullReach: .60, pull: .68, hit: .78, catch: .94, settle: 1.18,
};
const meta = {
  name: "Requiem chain return", size: [350, 144], origin: [0, 0],
  fps: 50, duration: 1.4, loop: false, bg: "none",
};
const waltzFeet = [54, 107];
const targetFeet = [218, 114];
const ink = 0xff311b2a;
const shadow = 0xff62325b;
const violet = 0xffa7599e;
const orchid = 0xffdf9fe2;
const light = 0xfff5cafa;
const white = 0xffffeaff;

const clamp = (value) => Math.max(0, Math.min(1, value));
const progress = (time, start, end) => clamp((time - start) / (end - start));
const mix = (start, end, u) => start + (end - start) * u;
const smooth = (u) => u * u * (3 - 2 * u);
const wave = (u) => Math.sin(Math.PI * u);

function pose(time) {
  const { windup, launch, fullReach, pull, catch: catchTime, settle } = timing;
  if (time < launch) {
    const u = smooth(progress(time, windup, launch));
    return {
      x: mix(108, 95, u), y: mix(86, 87, u), angle: mix(-15, -30, u),
      sag: mix(13, 24, u), ripple: 0, lean: -2 * u,
    };
  }
  if (time < fullReach) {
    const u = progress(time, launch, fullReach);
    const flight = 1 - (1 - u) ** 1.7;
    return {
      x: mix(95, 262, flight), y: mix(87, 67, u) - 7 * wave(u),
      angle: mix(-30, -4, smooth(u)), sag: 24 * (1 - u) ** 1.5,
      ripple: 3 * wave(u), lean: mix(-2, 1, Math.sin(u * Math.PI / 2)),
    };
  }
  if (time < pull) {
    const u = progress(time, fullReach, pull);
    return {
      x: mix(262, 267, 1 - (1 - u) ** 2), y: mix(67, 70, smooth(u)),
      angle: mix(-4, -24, u ** 2), sag: 0, ripple: 1.5 * wave(u), lean: mix(1, 0, u),
    };
  }
  if (time < catchTime) {
    const u = progress(time, pull, catchTime);
    return {
      x: mix(267, 111, smooth(u)), y: mix(70, 88, u) + 18 * wave(u),
      angle: mix(-24, -30, u) - 77 * wave(u) ** .9, sag: 3 * u ** 2,
      ripple: 2.5 * wave(u), lean: -3 * wave(u),
    };
  }
  const u = progress(time, catchTime, settle);
  const recoil = Math.sin(Math.PI * 2 * u) * (1 - u);
  return {
    x: mix(111, 108, smooth(u)) - 5 * recoil, y: mix(88, 86, u) + 3 * recoil,
    angle: mix(-30, -15, smooth(u)), sag: mix(3, 13, u) + 7 * recoil, ripple: 0,
    lean: -1.4 * recoil,
  };
}

function bladePoint(current, distance) {
  const radians = current.angle * Math.PI / 180;
  return [current.x + Math.cos(radians) * distance, current.y + Math.sin(radians) * distance];
}

function chainPath(current, time) {
  const startX = waltzFeet[0] + 12 + current.lean;
  const startY = waltzFeet[1] - 21;
  const snap = progress(time, timing.fullReach, timing.pull + .12);
  const snapCenter = 1 - snap;
  let length = 0;
  const points = Array.from({ length: 65 }, (_, i) => {
    const u = i / 64;
    const buckle = (u - snapCenter) * 13;
    const tension = 4 * wave(snap) * Math.sin(buckle * 1.8) * Math.exp(-buckle * buckle);
    return {
      x: mix(startX, current.x, u),
      y: mix(startY, current.y, u) + wave(u) * (
        current.sag + current.ripple * Math.sin(u * 9 - time * 41) + tension
      ),
    };
  });
  return points.map((entry, i) => {
    if (i > 0) length += Math.hypot(entry.x - points[i - 1].x, entry.y - points[i - 1].y);
    return { ...entry, length };
  });
}

const linkOutline = [
  [-5.9, -1.5], [-3.5, -3.4], [2.7, -3.4], [5.7, -2], [5.9, 1.2],
  [3.4, 3.0], [-3.5, 3.0], [-5.9, 1.0], [-5.9, -1.5],
];

function drawLink(p, x, y, angle, face, alpha) {
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const flatten = face ? 1 : .52;
  const point = ([along, across]) => [
    x + along * cos - across * flatten * sin,
    y + along * sin + across * flatten * cos,
  ];
  const rim = linkOutline.map(point);
  p.polyline(rim.map(([px, py]) => [px, py + 1.3]), ink, alpha);
  p.polyline(rim, shadow, alpha);
  p.polyline(rim.slice(0, 5), face ? orchid : violet, alpha);
  p.polyline(rim.slice(4), violet, alpha * .85);
  p.line(...point([-3.1, -3.6]), ...point([.8, -3.6]), light, alpha * (face ? .78 : .38));
  p.blend(...point([3.7, 2.6]), orchid, alpha * .65);
}

function drawChain(p, current, time) {
  const path = chainPath(current, time);
  const total = path.at(-1).length;
  // Measure from the sword so the last link stays on the pommel through the turn.
  let segment = path.length - 1;
  for (let offset = 3, link = 0; offset < total; offset += 8.25, link++) {
    const distance = total - offset;
    while (path[segment - 1].length > distance) segment--;
    const from = path[segment - 1];
    const to = path[segment];
    const u = (distance - from.length) / (to.length - from.length);
    const angle = Math.atan2(to.y - from.y, to.x - from.x);
    drawLink(p, mix(from.x, to.x, u), mix(from.y, to.y, u), angle, link % 2 === 0,
      mix(.52, 1, clamp(distance / 13)));
  }
}

function drawReturnTrail(p, time) {
  const lifespan = .075;
  const head = Math.min(time, .9);
  const tail = Math.max(timing.pull, time - lifespan);
  if (head <= tail) return;
  const pixels = new Map();
  for (let step = tail; step < head; step += .0008) {
    const current = pose(step);
    const age = clamp((time - step) / lifespan);
    const envelope = smooth(progress(step, timing.pull, timing.pull + .055))
      * (1 - smooth(progress(step, .83, .9)));
    const width = mix(7, 31, envelope);
    const strength = envelope * (1 - age) ** 1.4;
    for (let depth = 0; depth < width; depth += .8) {
      const [px, py] = bladePoint(current, Math.max(edge, tip - depth));
      const x = Math.round(px);
      const y = Math.round(py);
      const alpha = strength * (1 - depth / width) ** .75 * .82;
      const key = x + y * meta.size[0];
      // Keep the strongest sample so oversampling preserves the shading of the blade.
      if ((pixels.get(key)?.alpha ?? 0) >= alpha) continue;
      const color = depth < 1.6 ? light : depth < 7 ? orchid : violet;
      pixels.set(key, { x, y, color, alpha });
    }
  }
  for (const { x, y, color, alpha } of pixels.values()) p.blend(x, y, color, alpha);
}

function drawContact(p, time) {
  const u = progress(time, timing.hit, timing.hit + .14);
  if (time < timing.hit || u >= 1) return;
  const [x, y] = hitPoint;
  const fade = (1 - u) ** 1.5;
  p.glow(x, y, 9, violet, fade * .52);
  p.blend(x, y, white, fade);
  for (let i = 0; i < 7; i++) {
    const angle = .18 + i * 2.4;
    const dx = Math.cos(angle) * (12 + i) * (.25 + u);
    const dy = Math.sin(angle) * (8 + i) * (.25 + u);
    p.line(x + dx * .62, y + dy * .62, x + dx, y + dy,
      i % 3 === 0 ? white : orchid, fade * .85);
  }
}

const hitPose = pose(timing.hit);
const hitRadians = hitPose.angle * Math.PI / 180;
const hitDepth = (targetFeet[1] - 44 - hitPose.y) / Math.sin(hitRadians);
const hitPoint = bladePoint(hitPose, hitDepth);

const effect = {
  meta,
  draw(p, time) {
    drawReturnTrail(p, time);
    drawChain(p, pose(time), time);
    drawContact(p, time);
  },
};

const shared = resolve(root, process.env.PIXELFX_ROOT ?? "../pixelfx");
const { renderFrames, spriteSheet } = await import(pathToFileURL(resolve(shared, "tools/lib/fxlib.mjs")));
const output = resolve(process.argv[2]);
const fx = { id: "requiem/forms-chain-preview", meta, mod: effect };
const rendered = renderFrames(fx, { actor: false });
const atlas = spriteSheet(fx, rendered, "effects");
writeFileSync(resolve(output, "effects.png"), atlas.png);
writeFileSync(resolve(output, "preview.json"), JSON.stringify({
  atlas: atlas.json, pommel, tip, edge, timing, hitPoint, waltzFeet, targetFeet,
  frames: rendered.frames.map(({ t }) => ({ t, ...pose(t) })),
}));
