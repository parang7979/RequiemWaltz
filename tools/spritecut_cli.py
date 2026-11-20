"""Run the SpriteCut checkout used by this game's art tools."""
import os
from pathlib import Path
import sys


def locate():
    override = os.environ.get("SPRITECUT_ROOT")
    checkout = Path(override) if override else Path(__file__).resolve().parents[2] / "SpriteCut"
    if (checkout / "spritecut" / "cli.py").is_file():
        sys.path.insert(0, str(checkout.resolve()))
    elif override:
        raise ImportError(f"SPRITECUT_ROOT has no SpriteCut package: {checkout}")
    else:
        from importlib.util import find_spec
        if find_spec("spritecut") is None:
            raise ImportError("Install SpriteCut, clone it beside the game, or set SPRITECUT_ROOT.")


if __name__ == "__main__":
    locate()
    from spritecut.cli import main
    main()
