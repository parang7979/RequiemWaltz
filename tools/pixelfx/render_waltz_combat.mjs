import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { arc, seal, cannon } from "../../artsource/pixelfx/waltz_combat.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const shared = resolve(root, process.env.PIXELFX_ROOT ?? "../pixelfx");
const { renderFrames, spriteSheet } = await import(pathToFileURL(resolve(shared, "tools/lib/fxlib.mjs")));
const output = resolve(root, "assets/vfx/waltz_combat");
mkdirSync(output, { recursive: true });

for (const [name, mod] of Object.entries({ arc, seal, cannon })) {
  const fx = { id: `requiem/waltz-${name}`, meta: mod.meta, mod };
  const atlas = spriteSheet(fx, renderFrames(fx, { actor: false }), name);
  const manifest = resolve(output, name + ".json");
  writeFileSync(manifest, JSON.stringify(atlas.json, null, 2) + "\n");
  writeFileSync(resolve(output, name + ".png"), atlas.png);
  execFileSync("python", [resolve(shared, "tools/import_godot.py"), manifest, "--project", root], { stdio: "inherit" });
}
