// Original Requiem Waltz PixelFX effects. ABGR colors are opaque unless blended.
const mint = 0xffbbf8ab;
const teal = 0xff9e8e42;
const violet = 0xffb67791;
const white = 0xffeafff0;
const gold = 0xff6ac1ff;
const ivory = 0xffccedff;

export const swing = {
  meta: { name: "Greatsword crescent", size: [156, 156], origin: [78, 78], fps: 60, duration: 0.25, loop: false },
  draw(p, t) {
    const tick = Math.round(t * 60);
    if (tick === 0 || tick >= 15) return;
    const head = -1.38 + 2.70 * Math.min(1, tick / 6);
    const tail = -1.38 + 2.70 * Math.max(0, (tick - 6) / 9);
    const fade = 1 - Math.max(0, tick - 6) / 9;
    for (let a = tail; a < head; a += 0.012) {
      const u = (a - tail) / (head - tail);
      const belly = Math.sin(Math.PI * u ** 1.5) ** 0.74;
      const ray = [Math.cos(a), Math.sin(a)];
      const radius = 65 + 5 * belly;
      const width = 15 * belly * (0.48 + fade * 0.52);
      for (let depth = 0; depth <= width; depth++) {
        const ink = depth < 2 ? white : depth < 5 ? mint : depth < 9 ? teal : violet;
        const r = radius - depth;
        p.blend(ray[0] * r, ray[1] * r, ink, fade * Math.min(1, 0.26 + u * 1.4));
      }
      if (Math.round(a * 1100) % 9 === 0) {
        const r = radius + 3 + 2 * Math.sin(a * 17);
        p.blend(ray[0] * r, ray[1] * r, mint, fade * (0.44 + u * 0.5));
        const echo = radius - 21 - 2 * belly;
        p.blend(ray[0] * echo, ray[1] * echo, violet, fade * belly * 0.72);
      }
    }
  },
};

export const impact = {
  meta: { name: "Bell strike", size: [126, 106], origin: [52, 53], fps: 60, duration: 0.3, loop: false },
  draw(p, t) {
    const u = t / this.meta.duration;
    if (u >= 1) return;
    const fade = (1 - u) ** 1.5;
    const expansion = 1 - (1 - u) ** 3;
    const rayCount = 18;
    for (let i = 0; i < rayCount; i++) {
      const angle = i * 2.39996;
      const length = 18 + (i * 23 % 31);
      const vx = Math.cos(angle) * length + 11;
      const vy = Math.sin(angle) * length * 0.76;
      const head = 0.26 + 0.70 * expansion;
      const tail = Math.max(0.02, head - 0.33 * (1 - u));
      p.line(vx * tail, vy * tail + 9 * u * u, vx * head, vy * head + 9 * u * u,
        i % 4 === 0 ? mint : gold, fade);
      if (i % 2 === 0) p.blend(vx * head, vy * head + 9 * u * u, ivory, fade);
    }
    const ring = 8 + 38 * expansion;
    for (let a = -1.55; a < 1.6; a += 0.025) {
      if (Math.cos(a * 8) < -0.25) continue;
      p.blend(Math.cos(a) * ring + 3, Math.sin(a) * ring * 0.77, gold, fade * 0.80);
    }
    if (u < 0.28) {
      const decay = 1 - u / 0.28;
      p.glow(0, 0, 19, gold, decay * 0.65);
      p.line(-16 * decay, 1, 21 * decay, -1, ivory);
      p.line(-4 * decay, -15 * decay, 3 * decay, 14 * decay, white);
      p.line(-8 * decay, -7 * decay, 7 * decay, 5 * decay, gold);
      p.line(-8 * decay, 3 * decay, 13 * decay, -5 * decay, ivory);
    }
  },
};
