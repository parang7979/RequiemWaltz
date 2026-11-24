import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { drawSpectralLink, drawSpectralSpirit } from "./requiem_chain_spirit.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const forms = JSON.parse(readFileSync(resolve(root, "assets/actors/requiem_forms/clips.json"), "utf8"));
const pommel = [3, forms.clips.sword.pivot[1]];
const tip = forms.sword_tip[0] + forms.clips.sword.pivot[0] - pommel[0];
const edge = forms.sword_edge_from + forms.clips.sword.pivot[0] - pommel[0];

const spectral = process.argv[3] === "v004";
const floating = spectral || process.argv[3] === "v003";
const timing = { windup: .24, launch: .40, fullReach: .60, pull: .68, catch: .94, settle: 1.18 };
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

const path = floating ? {
  guardX: 147, windupX: 132, catchX: 154, farY: 84, turnY: 84, castArc: 3,
  castTravel: smooth, castPitch: (u) => 1 - (1 - u) ** 3,
} : {
  guardX: 108, windupX: 95, catchX: 111, farY: 67, turnY: 70, castArc: 7,
  castTravel: (u) => 1 - (1 - u) ** 1.7, castPitch: smooth,
};

function pose(time) {
  const { windup, launch, fullReach, pull, catch: catchTime, settle } = timing;
  if (time < launch) {
    const u = smooth(progress(time, windup, launch));
    return {
      x: mix(path.guardX, path.windupX, u), y: mix(86, 87, u), angle: mix(-15, -30, u),
      sag: mix(13, 24, u), ripple: 0, lean: -2 * u,
    };
  }
  if (time < fullReach) {
    const u = progress(time, launch, fullReach);
    return {
      x: mix(path.windupX, 262, path.castTravel(u)),
      y: mix(87, path.farY, u) - path.castArc * wave(u),
      angle: mix(-30, -4, path.castPitch(u)), sag: 24 * (1 - u) ** 1.5,
      ripple: 3 * wave(u), lean: mix(-2, 1, Math.sin(u * Math.PI / 2)),
    };
  }
  if (time < pull) {
    const u = progress(time, fullReach, pull);
    return {
      x: mix(262, 267, 1 - (1 - u) ** 2), y: mix(path.farY, path.turnY, smooth(u)),
      angle: mix(-4, -24, u ** 2), sag: 0, ripple: 1.5 * wave(u), lean: mix(1, 0, u),
    };
  }
  if (time < catchTime) {
    const u = progress(time, pull, catchTime);
    return {
      x: mix(267, path.catchX, smooth(u)), y: mix(path.turnY, 88, u) + 18 * wave(u),
      angle: mix(-24, -30, u) - 77 * wave(u) ** .9, sag: 3 * u ** 2,
      ripple: 2.5 * wave(u), lean: -3 * wave(u),
    };
  }
  const u = progress(time, catchTime, settle);
  const recoil = Math.sin(Math.PI * 2 * u) * (1 - u);
  return {
    x: mix(path.catchX, path.guardX, smooth(u)) - 5 * recoil, y: mix(88, 86, u) + 3 * recoil,
    angle: mix(-30, -15, smooth(u)), sag: mix(3, 13, u) + 7 * recoil, ripple: 0,
    lean: -1.4 * recoil,
  };
}

function bladePoint(current, distance) {
  const radians = current.angle * Math.PI / 180;
  return [current.x + Math.cos(radians) * distance, current.y + Math.sin(radians) * distance];
}

function spiritAnchor(time) {
  const recoil = wave(progress(time, timing.pull, timing.catch));
  const reach = smooth(progress(time, timing.launch, timing.fullReach))
    * (1 - smooth(progress(time, timing.pull, timing.catch)));
  const hover = Math.sin(2 * Math.PI * time / meta.duration);
  const idleX = spectral ? 122 : 109;
  return [idleX + 4 * reach - 3 * recoil, 86 - 2 * hover - 3 * reach + recoil];
}

function chainPath(current, time) {
  const [startX, startY] = floating ? spiritAnchor(time) : [
    waltzFeet[0] + 12 + current.lean, waltzFeet[1] - 21,
  ];
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

function drawChain(p, chain, phase) {
  const total = chain.at(-1).length;
  // Measure from the sword so the last link stays on the pommel through the turn.
  let segment = chain.length - 1;
  for (let offset = 3, link = 0; offset < total; offset += 8.25, link++) {
    const distance = total - offset;
    while (chain[segment - 1].length > distance) segment--;
    const from = chain[segment - 1];
    const to = chain[segment];
    const u = (distance - from.length) / (to.length - from.length);
    const angle = Math.atan2(to.y - from.y, to.x - from.x);
    const x = mix(from.x, to.x, u);
    const y = mix(from.y, to.y, u);
    const strength = mix(.52, 1, clamp(distance / 13));
    const faceOn = link % 2 === 0;
    if (spectral) drawSpectralLink(p, x, y, angle, faceOn, strength, phase * 3 - link * .53);
    else drawLink(p, x, y, angle, faceOn, strength);
  }
}

function drawSpirit(p, chain, time) {
  const { x, y } = chain[0];
  const bend = Math.sin(2 * Math.PI * time / meta.duration);
  const local = ([dx, dy]) => [x + dx, y + dy + bend * Math.max(0, -dx - 7) * .14];
  const fill = (points, color) => p.poly(points.map(local), color);
  const ridge = (points, color) => p.polyline(points.map(local), color);

  // Preserve Requiem's two horns, bright eyes and grin in the fluid silhouette.
  fill([
    [-29, 5], [-24, 1], [-22, -5], [-24, -14], [-20, -12], [-16, -7],
    [-10, -8], [-6, -12], [-3, -18], [-2, -12], [-4, -7], [-1, -4],
    [3, -2], [5, 1], [2, 4], [-3, 5], [-8, 10], [-15, 11], [-22, 9],
    [-25, 10], [-31, 9], [-26, 7],
  ], ink);
  fill([
    [-28, 5], [-23, 1], [-21, -5], [-23, -13], [-19, -10], [-16, -6],
    [-9, -7], [-5, -12], [-3, -16], [-3, -11], [-5, -6], [0, -3],
    [4, 1], [0, 3], [-5, 4], [-10, 8], [-16, 9], [-23, 7], [-27, 9], [-29, 8],
  ], shadow);
  fill([
    [-29, 8], [-24, 4], [-21, 0], [-20, -3], [-20, 2], [-18, 5],
    [-13, 7], [-8, 6], [-4, 3], [3, 0], [3, 2], [-4, 5], [-10, 9],
    [-17, 9], [-23, 7], [-27, 9],
  ], 0xff874c76);
  ridge([[-27, 5], [-23, 2], [-20, -3], [-21, -8], [-23, -12]], violet);
  ridge([[-17, -6], [-13, -6], [-9, -7], [-5, -11], [-3, -15]], violet);
  ridge([[-27, 8], [-23, 6], [-17, 8], [-13, 8], [-8, 6]], violet);
  fill([[-19, -4], [-10, -6], [-4, -3], [-5, 2], [-10, 6], [-15, 6], [-20, 2]], ink);
  fill([[-18, -3], [-13, -1], [-13, 1], [-17, 0]], light);
  fill([[-11, -1], [-6, -4], [-7, -1], [-10, 1]], light);
  ridge([[-16, 2], [-13, 3], [-10, 3], [-8, 1]], orchid);
  p.blend(...local([-15, -1]), white, .85);
  p.blend(...local([-8, -2]), white, .85);

  // Taper the fluid along the chain itself so the join follows the first links.
  for (const point of chain) {
    if (point.length > 13) break;
    const thin = 1 - point.length / 13;
    const flow = .55 + .45 * Math.sin(point.length * .58 - time * 8 * Math.PI / meta.duration);
    p.disc(point.x, point.y, .65 + 2.25 * thin, shadow, .3 + .58 * thin);
    p.blend(point.x, point.y - thin, orchid, thin * flow * .73);
  }
}

function drawCastTrail(p, current, time) {
  const u = progress(time, timing.launch, timing.fullReach);
  if (u <= 0 || u >= 1) return;
  const size = 11 + 13 * wave(u);
  const a = .58 * wave(u);
  const [x, y] = bladePoint(current, edge + 5);
  p.line(x - size, y + 1, x - 2, y + 1, orchid, a);
  p.line(x - size * .65, y + 4, x - 5, y + 4, violet, a * .7);
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

function drawContact(p, time, hit) {
  const u = progress(time, hit.time, hit.time + .14);
  if (time < hit.time || u >= 1) return;
  const [x, y] = hit.point;
  const fade = (1 - u) ** 1.5;
  const forward = hit.push > 0 ? 6 : 0;
  p.glow(x, y, 9, violet, fade * .52);
  p.blend(x, y, white, fade);
  for (let i = 0; i < 7; i++) {
    const angle = .18 + i * 2.4;
    const dx = (Math.cos(angle) * (12 + i) + forward) * (.25 + u);
    const dy = Math.sin(angle) * (8 + i) * (.25 + u);
    p.line(x + dx * .62, y + dy * .62, x + dx, y + dy,
      i % 3 === 0 ? white : orchid, fade * .85);
  }
}

const hits = [];
if (floating) {
  const cast = pose(.46);
  const depth = (targetFeet[0] - 6 - cast.x) / Math.cos(cast.angle * Math.PI / 180);
  hits.push({ time: .46, point: bladePoint(cast, depth), push: 7, holdMs: 20 });
}
const returnTime = floating ? .80 : .78;
const returning = pose(returnTime);
const returnY = targetFeet[1] - (floating ? 38 : 44);
const returnDepth = (returnY - returning.y) / Math.sin(returning.angle * Math.PI / 180);
hits.push({
  time: returnTime, point: bladePoint(returning, returnDepth),
  push: floating ? -8 : -6, holdMs: floating ? 20 : 0,
});

const effect = {
  meta,
  draw(p, time) {
    const current = pose(time);
    const chain = chainPath(current, time);
    const phase = 2 * Math.PI * time / meta.duration;
    if (floating) drawCastTrail(p, current, time);
    drawReturnTrail(p, time);
    drawChain(p, chain, phase);
    if (spectral) drawSpectralSpirit(p, chain, phase);
    else if (floating) drawSpirit(p, chain, time);
    for (const hit of hits) drawContact(p, time, hit);
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
  atlas: atlas.json, pommel, tip, edge, timing, hits, waltzFeet, targetFeet,
  frames: rendered.frames.map(({ t }) => ({ t, ...pose(t), spirit: floating ? spiritAnchor(t) : null })),
}));
