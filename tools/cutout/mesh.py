"""Compatibility entry point for the shared SpriteCut mesh module."""
from spritecut_cli import locate

locate()
from spritecut.mesh import SkinMesh, blend, rigid, screen, segment
