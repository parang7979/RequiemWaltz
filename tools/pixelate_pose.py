"""Compatibility entry point for the shared SpriteCut pixelate_pose module."""
from spritecut_cli import locate

locate()
from spritecut.pixelate_pose import extract_pose, main


if __name__ == "__main__":
    main()
