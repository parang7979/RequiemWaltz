import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spectralColors } from "./requiem_chain_spirit.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const shared = resolve(root, process.env.PIXELFX_ROOT ?? "../pixelfx");
const { blend, composite, createFrame, mix: mixColor, painterFor } = await import(
  pathToFileURL(resolve(shared, "src/core/index.js"))
);

const tau = Math.PI * 2;
const clamp = (v) => Math.max(0, Math.min(1, v));
const mix = (a, b, u) => a + (b - a) * u;
const tint = (level) => blend(spectralColors, level);
const eyeLight = 0xfff8d0f0;

function onShell(bytes, w, h, draw) {
  const opacityAt = (x, y) => x >= 0 && y >= 0 && x < w && y < h ? bytes[(y * w + x) * 4 + 3] / 255 : 0;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      const alpha = bytes[i + 3] / 255;
      if (alpha < .015) continue;
      const rim = 1 - Math.min(opacityAt(x - 2, y), opacityAt(x + 2, y),
        opacityAt(x, y - 2), opacityAt(x, y + 2));
      const value = bytes[i] * .53 + bytes[i + 1] * .16 + bytes[i + 2] * .31;
      const color = 0xff000000 | (bytes[i + 2] << 16) | (bytes[i + 1] << 8) | bytes[i];
      draw(x, y, alpha, rim, value, color);
    }
  }
}

const forms = {
  hand: {
    // Light wraps around the wrist before advancing to the clenched fingers.
    wave: (x, y) => (x - 28) / 39 + .13 * Math.sin(y * .19),
    face: [0, 21],
    wisps: [
      ["tail", [[5, -7], [-5, -13], [-20, -14], [-18, -24]]],
      ["tail", [[13, 4], [6, 18], [-16, 12], [-22, 17]]],
      ["socket", [[-1, -10], [3, -18], [13, -17], [16, -25]]],
    ],
  },
  bow: {
    // The same pulse splits at the throat and reaches both tips.
    wave: (x, y) => Math.abs(y - 54) / 43 + .09 * Math.sin((x - 42) * .18),
    face: [1, 10],
    wisps: [
      ["upper", [[8, 5], [1, -4], [-17, -1], [-15, -10]]],
      ["lower", [[10, -5], [1, 6], [-17, 1], [-17, 10]]],
      ["tail", [[6, 5], [19, 14], [23, 1], [29, -4]]],
    ],
  },
  cannon: {
    // The broad fold coils down the barrel and compresses at the muzzle.
    wave: (x, y) => (x - 18) / 53 + .19 * Math.sin((y - 48) * .14),
    face: [-23, 8],
    wisps: [
      ["tail", [[15, -13], [11, -26], [-14, -23], [-20, -30]]],
      ["tail", [[22, 12], [12, 25], [-10, 18], [-18, 27]]],
      ["socket", [[-8, 10], [-1, 14], [9, 10], [12, 16]]],
    ],
  },
};

function trace(p, points, phase, strength) {
  const [start, a, b, finish] = points;
  for (let i = 0; i <= 56; i++) {
    const u = i / 56;
    const v = 1 - u;
    const position = (axis) => v ** 3 * start[axis] + 3 * v ** 2 * u * a[axis]
      + 3 * v * u ** 2 * b[axis] + u ** 3 * finish[axis];
    const coil = Math.sin(u * 6 - phase);
    const x = position(0);
    const y = position(1) + u * coil * 4;
    const fade = strength * Math.sin(Math.PI * u) ** .8 * (1 - .46 * u);
    p.disc(x, y, .55 + (1 - u) * 1.45, tint(.43 + .11 * coil), fade * .38);
    p.blend(x, y - 1, tint(.74 + .14 * coil), fade * .68);
  }
}

function render(job) {
  const { width, height, kind, points, phase, load } = job;
  const original = Buffer.from(job.rgba, "base64");
  const form = forms[kind];
  const frame = createFrame(width, height);
  const p = painterFor(frame);
  for (const [index, [anchor, shape]] of form.wisps.entries()) {
    const [ax, ay] = points[anchor];
    trace(p, shape.map(([x, y]) => [ax + x, ay + y]),
      phase * 2 + index * 1.6, .66 + .27 * load);
  }
  const [faceX, faceY] = form.face.map((offset, i) => offset + points.pivot[i]);
  onShell(original, width, height, (x, y, alpha, rim, value, color) => {
    const relief = clamp((value - 22) / 134);
    const flow = Math.cos(form.wave(x, y) * tau - phase * 2);
    const narrow = (.5 + .5 * flow) ** 5;
    const hollow = 1 - clamp(Math.hypot((x - faceX) / 12, (y - faceY) / 8));
    const glow = narrow * (.13 + .22 * load) * (.22 + .78 * relief);
    const level = .10 + relief * .64 + glow - hollow * .12;
    const dissolve = (.25 + .16 * Math.sin(x * .43 + y * .21 - phase * 3)) * rim;
    const interior = narrow * .07 * (1 - hollow);
    p.blend(x, y, mixColor(color, tint(level), .83), alpha * (.97 - dissolve - interior));
    // Preserve the painted face and let only its existing highlights catch the light.
    if (hollow > .18 && relief > .32) {
      p.blend(x, y, eyeLight, alpha * hollow * relief * (.33 + .43 * narrow));
    }
  });
  return composite(frame, Buffer.alloc(width * height * 4), null);
}

const [inputPath, outputPath] = process.argv.slice(2);
const jobs = JSON.parse(readFileSync(inputPath, "utf8"));
writeFileSync(outputPath, Buffer.concat(jobs.map(render)));
