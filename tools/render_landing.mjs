import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import * as dust from "../artsource/pixelfx/landing_dust.mjs";

const project = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const pixelfx = resolve(project, process.env.PIXELFX_ROOT ?? "../pixelfx");
const plinkfx = resolve(project, process.env.PLINKFX_ROOT ?? "../plinkfx");
const { renderFrames, spriteSheet } = await import(pathToFileURL(resolve(pixelfx, "tools/lib/fxlib.mjs")).href);

function run(program, args) {
  const result = spawnSync(program, args, { cwd: project, stdio: "inherit" });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`${program} exited with ${result.status}`);
}

const dustDir = resolve(project, "assets/vfx/landing_dust");
mkdirSync(dustDir, { recursive: true });
const effect = { id: "requiem/landing_dust", meta: dust.meta, mod: dust };
const atlas = spriteSheet(effect, renderFrames(effect, { actor: false }), "landing_dust");
const metadata = resolve(dustDir, "landing_dust.json");
writeFileSync(resolve(dustDir, "landing_dust.png"), atlas.png);
writeFileSync(metadata, JSON.stringify(atlas.json, null, 2) + "\n");
run("python", [resolve(pixelfx, "tools/import_godot.py"), metadata, "--project", project]);

const audioDir = resolve(project, "assets/audio");
mkdirSync(audioDir, { recursive: true });
run(process.execPath, [
  resolve(plinkfx, "dist/cli.js"), "render", "artsource/plinkfx/stone_land.json",
  "--rate", "48000", "--variant", "0", "-o", resolve(audioDir, "stone_land.wav"),
]);
