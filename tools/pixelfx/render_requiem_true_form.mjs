import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { concern, idle } from "../../artsource/pixelfx/requiem_true_form.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const shared = resolve(root, process.env.PIXELFX_ROOT ?? "../pixelfx");
const { renderFrames, spriteSheet } = await import(pathToFileURL(resolve(shared, "tools/lib/fxlib.mjs")));
const output = resolve(root, "assets/vfx/requiem_forms");

for (const [name, mod] of Object.entries({ true_form_idle: idle, true_form_concern: concern })) {
  const effect = { id: "requiem/" + name, meta: mod.meta, mod };
  const atlas = spriteSheet(effect, renderFrames(effect, { actor: false }), name);
  const manifest = resolve(output, name + ".json");
  writeFileSync(manifest, JSON.stringify(atlas.json, null, 2) + "\n");
  writeFileSync(resolve(output, name + ".png"), atlas.png);
  execFileSync("python", [resolve(shared, "tools/import_godot.py"), manifest, "--project", root], { stdio: "inherit" });
}
