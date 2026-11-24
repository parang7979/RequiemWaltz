import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { drawSpectralLink, drawSpectralSpirit } from "../../artsource/pixelfx/requiem_chain_spirit.mjs";

const root = new URL("../../", import.meta.url);
const output = new URL("artsource/spritecut/waltz/materials/v009/prepared/", root);
const shared = new URL("../pixelfx/", root);
const library = process.env.PIXELFX_ROOT
  ? pathToFileURL(resolve(process.env.PIXELFX_ROOT, "tools/lib/fxlib.mjs"))
  : new URL("tools/lib/fxlib.mjs", shared);
const { renderFrames, spriteSheet } = await import(library);

function save(name, size, origin, duration, draw) {
  const meta = { name, size, origin, duration, fps: 60, loop: true, bg: "none" };
  const effect = { id: "requiem/" + name, meta, mod: { meta, draw } };
  const rendered = renderFrames(effect, { actor: false });
  writeFileSync(new URL(name + ".png", output), spriteSheet(effect, rendered, name).png);
}

mkdirSync(output, { recursive: true });
save("front", [112, 104], [56, 52], 1 / 60, (p) => {
  const taper = Array.from({ length: 13 }, (_, i) => ({ x: 22 + i, y: 0, length: i }));
  drawSpectralSpirit(p, taper, 0);
});
save("chain_links", [20, 20], [10, 10], 2 / 60, (p, t) => {
  drawSpectralLink(p, 0, 0, 0, t < 1 / 120, 1, .65);
});
