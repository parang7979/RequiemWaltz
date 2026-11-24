// Original Requiem Waltz effects. Packed colors use PixelFX's ABGR order.
const violet = 0xffba5989;
const lilac = 0xffeb98db;
const blush = 0xffe4b6ff;
const gold = 0xff85caff;
const white = 0xffe9f1ff;

export const arc = {
  meta: { name: "Familiar's blade", size: [200, 200], origin: [100, 100], fps: 60, duration: 0.30, loop: false },
  draw(p, time) {
    const tick = Math.round(time * 60);
    if (tick <= 0 || tick >= 18) return;
    const upper = -1.45 + 2.82 * Math.min(1, tick / 6);
    const lower = -1.45 + 2.82 * Math.max(0, (tick - 7) / 11);
    const life = 1 - Math.max(0, tick - 6) / 12;
    for (let a = lower; a <= upper; a += 0.012) {
      const fraction = (a - lower) / (upper - lower);
      const swell = Math.sin(Math.PI * fraction ** 1.5) ** 0.64;
      const radius = 88 + 5 * swell;
      const x = Math.cos(a), y = Math.sin(a);
      const width = (3 + 15 * swell) * (0.38 + 0.62 * life);
      const alpha = life * (0.35 + 0.65 * fraction);
      for (let b = 0; b < width; b++) {
        const r = radius - b;
        const ink = b < 1 ? gold : b < 4 ? white : b < 8 ? blush : b < 13 ? lilac : violet;
        p.blend(x*r, y*r, ink, alpha);
      }
      if (Math.round(a * 1400) % 8 === 0) {
        p.blend(x*(radius+3), y*(radius+3), gold, alpha);
        p.blend(x*(radius-26), y*(radius-26), lilac, alpha * swell);
      }
      if (Math.round(a * 1400) % 25 === 0) p.blend(x*(radius+5), y*(radius+5), blush, alpha);
    }
  },
};

export const seal = {
  meta: { name: "Seal opens", size: [128, 120], origin: [64, 61], fps: 60, duration: 0.50, loop: false },
  draw(p, t) {
    const age = t / 0.50;
    if (age >= 1) return;
    const ease = 1 - (1 - age) ** 3;
    const r = 17 + 40 * ease;
    const fade = (1 - age) ** 1.35;
    p.glow(0, -7, 35, violet, fade * 0.58);
    for (let a = 0; a < Math.PI * 2; a += 0.021) {
      const x = Math.cos(a), y = Math.sin(a);
      p.blend(x*r, y*r*0.48, lilac, fade);
      if (Math.cos(a * 9) > -0.15) p.blend(x*(r-6), y*(r-6)*0.48, gold, fade);
    }
    for (let i = 0; i < 15; i++) {
      const a = i * 2.39996;
      const x = Math.cos(a) * (11 + 36 * ease);
      const y = Math.sin(a) * (9 + 13 * ease) - 36 * age;
      p.line(x, y, x, y + 5 - 3 * age, i % 3 ? lilac : gold, fade);
      p.blend(x, y, white, fade);
    }
  },
};

export const cannon = {
  meta: { name: "Crater bloom", size: [136, 128], origin: [68, 63], fps: 60, duration: 0.44, loop: false },
  draw(p, t) {
    const age = t / 0.44;
    if (age >= 1) return;
    const ease = 1 - (1 - age) ** 4;
    const fade = (1 - age) ** 1.85;
    p.glow(0, 0, 43, violet, fade * 0.9);
    p.glow(0, -4, 25, blush, fade * 0.7);
    for (let i = 0; i < 24; i++) {
      const a = i * 2.39996;
      const dx = Math.cos(a) * (33 + i * 13 % 27);
      const dy = Math.sin(a) * (22 + i * 23 % 19);
      const end = 0.18 + ease * 0.78;
      const begin = Math.max(0.0, end - fade * 0.5);
      p.line(dx*begin, dy*begin, dx*end, dy*end, i % 3 ? lilac : gold, fade);
      p.blend(dx*end, dy*end, white, fade);
    }
    const r = 8 + 50 * ease;
    for (let a = 0; a < Math.PI * 2; a += 0.018) {
      const x = Math.cos(a), y = Math.sin(a);
      if (Math.cos(a*10) > -0.35 || age < 0.2) p.blend(x*r, y*r*0.57, lilac, fade);
      p.blend(x*(r-6), y*(r-6)*0.57, gold, fade * 0.78);
    }
    if (age < 0.28) {
      const s = 1 - age / 0.28;
      p.line(-21*s, 0, 22*s, -2*s, white);
      p.line(-2*s, -28*s, 3*s, 18*s, white);
      p.line(-10*s, -14*s, 12*s, 12*s, gold);
    }
  },
};
