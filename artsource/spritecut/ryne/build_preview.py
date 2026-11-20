"""Copy Ryne's selected SpriteCut bakes and update the Godot preview catalog."""
import json
import os
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
ACTORS = ROOT / "assets/actors"
ASSETS = ACTORS / "ryne_spritecut"
GAME = Path(__file__).resolve().parent / "productions/pilot-01"
SPRITECUT = Path(os.environ.get("SPRITECUT_ROOT", ROOT.parent / "SpriteCut"))
SOCIAL = SPRITECUT / "build/social-ryne/pilot-01"

# Display order is also the keyboard navigation order in the preview.
GROUPS = {
    "이동 · 기본": [
        ("idle", "대기"), ("walk", "걷기"), ("run", "달리기"), ("arm_swing", "팔 스윙"),
        ("jump", "점프"), ("double_jump", "이단 점프"),
        ("dash_forward", "전방 대시"), ("dash_backward", "후방 대시"),
    ],
    "검술": [("slash_left", "왼쪽 횡베기"), ("slash_right", "오른쪽 횡베기"), ("slash_down", "내려베기"),
           ("slash_up", "올려베기")],
    "소셜": [
        ("pant", "헐떡이기"), ("wave", "손인사"), ("kneel_hug", "무릎 앉기"),
        ("thank_you", "감사 인사"), ("stretch_overhead", "머리 위 스트레칭"),
        ("applause", "응원의 박수"), ("stretch_reach", "한 팔씩 뻗기"), ("listen", "귀 기울이기"),
        ("think", "생각하기"), ("talk", "대화하기"), ("doze", "꾸벅꾸벅 졸기"), ("yawn", "하품하기"),
    ],
}


def read(path):
    return json.loads(path.read_bytes())


def entry(group, label, clip, version, manifest):
    return dict(group=group, label=label, clip=clip, version=version,
                manifest="res://" + manifest.relative_to(ROOT).as_posix())


def prepare(staging, group, label, clip, revision, folder=None):
    target = ASSETS / "motions" / (folder or clip)
    staged = staging / target.name
    source = revision / "sheets"
    manifest = source / "clips.json"
    clips = read(manifest)["clips"]
    if clip not in clips:
        raise ValueError(f"{revision}: missing {clip}")
    staged.mkdir()
    copyfile(manifest, staged / manifest.name)
    for sheet in clips.values():
        for filename in sheet["maps"].values():
            copyfile(source / filename, staged / filename)
    root_motion = revision / "root_motion.json"
    if root_motion.exists():
        copyfile(root_motion, staged / root_motion.name)
    return entry(group, label, clip, read(revision / "revision.json")["id"], target / "clips.json")


def build_catalog(staging):
    game = read(GAME / "selection.json")
    selected = {**game["reviewed"], **game["motions"], "dash_forward": "v001", "dash_backward": "v002"}
    selected.setdefault("slash_up", "v002")
    social = read(SOCIAL / "selection.json")["motions"]
    catalog = []
    for group, motions in GROUPS.items():
        for clip, label in motions:
            if group == "소셜":
                revision = SOCIAL / "motions" / clip / social[clip]
            elif clip == "slash_down":
                revision = SOCIAL / "motions/slash_down/v002"
            else:
                revision = GAME / "motions" / clip / selected[clip]
            catalog.append(prepare(staging, group, label, clip, revision))

    catalog.append(prepare(staging, "비교본", "내려베기 · 초기", "slash_down",
                           GAME / "motions/slash_down/v001", "slash_down_v001"))
    for clip, label in [("walk", "걷기 · 기존 씬"), ("run", "달리기 · 기존 씬")]:
        catalog.append(entry("비교본", label, clip, "", ASSETS / "clips.json"))
    catalog.append(entry("비교본", "걷기 · 508", "walk", "", ACTORS / "ryne_508/walk/clips.json"))
    return catalog


def main():
    # Check the whole character before publishing any regenerated motion.
    with TemporaryDirectory(dir=ASSETS) as temp:
        staging = Path(temp)
        catalog = build_catalog(staging)
        for motion in staging.iterdir():
            target = ASSETS / "motions" / motion.name
            target.mkdir(parents=True, exist_ok=True)
            for path in motion.iterdir():
                path.replace(target / path.name)
        index = staging / "catalog.json"
        index.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index.replace(ASSETS / index.name)


if __name__ == "__main__":
    main()
