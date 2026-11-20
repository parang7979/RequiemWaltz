"""Compatibility entry point for the shared SpriteCut texture module."""
from spritecut_cli import locate

locate()
from spritecut.texture import register_texture
