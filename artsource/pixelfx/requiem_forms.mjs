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

export const shift = {
  meta: { name: "Spirit reformation", size: [152, 94], origin: [76, 47], fps: 60, duration: 15 / 60, loop: false },
  draw(p, t) {
    const u = t * 4;
    if (u >= 1) return;
    const envelope = Math.sin(Math.PI * u) ** 0.68;
    const spread = 13 + 46 * envelope;
    for (let strand = 0; strand < 3; strand++) {
      const yScale = [10, 18, 24][strand];
      const start = -0.55 + strand * 0.29 - u * 2.4;
      const end = start + 4.40;
      for (let a = start; a < end; a += 0.025) {
        const phase = (a - start) / (end - start);
        const thick = 9 * Math.sin(Math.PI * phase) ** .7 * envelope;
        const x = Math.cos(a) * (spread - strand * 6);
        const y = Math.sin(a) * yScale * envelope + Math.sin(a * 2 + u * 5) * 4;
        for (let i = 0; i <= thick; i++) {
          const color = i < 2 ? luminous : i < 4 ? orchid : i < 7 ? violet : ink;
          p.blend(x, y - i, color, envelope * (.38 + .55 * phase));
        }
      }
    }
    p.glow(0, 0, 18, violet, envelope * .55);
    p.line(-8 * envelope, 0, 8 * envelope, 0, luminous, envelope);
    p.line(0, -5 * envelope, 0, 4 * envelope, white, envelope);
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
