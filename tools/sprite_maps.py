"""Compatibility entry point for the shared SpriteCut sprite_maps module."""
from spritecut_cli import locate

locate()
from spritecut.sprite_maps import emissive_map, lighting_preview, main, normal_map, rgb_color


if __name__ == "__main__":
    main()
