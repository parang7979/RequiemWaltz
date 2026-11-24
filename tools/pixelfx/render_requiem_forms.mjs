import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { bowRelease, cannonRelease, counterCut, disperse, handCut, shift, tail } from "../../artsource/pixelfx/requiem_forms.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const shared = resolve(root, process.env.PIXELFX_ROOT ?? "../pixelfx");
const { renderFrames, spriteSheet } = await import(pathToFileURL(resolve(shared, "tools/lib/fxlib.mjs")));
const output = resolve(root, "assets/vfx/requiem_forms");
mkdirSync(output, { recursive: true });

const requested = process.argv.slice(2);
const effects = { tail, shift, hand_cut: handCut, counter_cut: counterCut, bow_release: bowRelease, cannon_release: cannonRelease, disperse };
for (const [name, mod] of Object.entries(effects)) {
  if (requested.length && !requested.includes(name)) continue;
  const fx = { id: "requiem/forms-" + name, meta: mod.meta, mod };
  const atlas = spriteSheet(fx, renderFrames(fx, { actor: false }), name);
  const manifest = resolve(output, name + ".json");
  writeFileSync(manifest, JSON.stringify(atlas.json, null, 2) + "\n");
  writeFileSync(resolve(output, name + ".png"), atlas.png);
  execFileSync("python", [resolve(shared, "tools/import_godot.py"), manifest, "--project", root], { stdio: "inherit" });
}
