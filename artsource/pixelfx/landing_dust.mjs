// PixelFX stores colour words as 0xAABBGGRR.
const slate = 0xff746465;     // #656474
const limestone = 0xff9a9da8; // #a89d9a
const grit = 0xffb1c2d0;      // #d0c2b1

export const meta = {
  name: "Limestone landing",
  size: [34, 14],
  origin: [17, 11],
  duration: 0.30,
  fps: 20,
  loop: false,
  bg: "none",
};

// The outer dust lifts first. Shorter, slower puffs separate at the heels.
const puffs = [
  { side: -1, travel: 11, rise: 3, delay: 0, radius: 1.8 },
  { side: 1, travel: 12, rise: 4, delay: 0, radius: 1.7 },
  { side: -1, travel: 7, rise: 5, delay: 0.045, radius: 1.3 },
  { side: 1, travel: 6, rise: 3, delay: 0.035, radius: 1.5 },
];

export function draw(painter, seconds) {
  for (const puff of puffs) {
    const phase = (seconds - puff.delay) / (meta.duration - puff.delay);
    if (phase < 0 || phase >= 1) continue;

    const spread = 1 - (1 - phase) ** 2;
    const x = puff.side * (2 + puff.travel * spread);
    const y = -1 - puff.rise * spread;
    const radius = puff.radius + phase * 0.9;
    const opacity = (1 - phase) ** 1.4;
    painter.disc(x, y, radius, slate, opacity * 0.82);
    painter.disc(x - 0.6, y - 0.65, radius * 0.67, limestone, opacity * 0.7);
  }

  // Two flecks lose height before the finer dust settles.
  const hop = seconds / 0.20;
  if (hop < 1) {
    painter.blend(-3 - 9 * hop, -1 - 18 * hop * (1 - hop), grit, 0.84 * (1 - hop));
    painter.blend(3 + 12 * hop, -1 - 23 * hop * (1 - hop), grit, 0.72 * (1 - hop));
  }
}
