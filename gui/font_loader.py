"""
font_loader.py — Carga IBM Plex Sans / IBM Plex Mono desde la carpeta fonts/
Si los archivos no están disponibles, usa los fallbacks definidos en config.py.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFontDatabase

_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

_IBM_PLEX_SANS_FILES = [
    "IBMPlexSans-Regular.ttf",
    "IBMPlexSans-Medium.ttf",
    "IBMPlexSans-SemiBold.ttf",
    "IBMPlexSans-Bold.ttf",
    "IBMPlexSans-Italic.ttf",
]

_IBM_PLEX_MONO_FILES = [
    "IBMPlexMono-Regular.ttf",
    "IBMPlexMono-Medium.ttf",
    "IBMPlexMono-Bold.ttf",
]


def load_fonts() -> tuple[str, str]:
    """
    Intenta cargar las fuentes IBM Plex Sans y IBM Plex Mono.
    Retorna (familia_normal, familia_mono) — pueden ser las IBM o los fallbacks.
    """
    sans_ok  = _load_family(_IBM_PLEX_SANS_FILES)
    mono_ok  = _load_family(_IBM_PLEX_MONO_FILES)

    familia_normal = "IBM Plex Sans"  if sans_ok else "Segoe UI"
    familia_mono   = "IBM Plex Mono"  if mono_ok else "Consolas"
    return familia_normal, familia_mono


def _load_family(files: list[str]) -> bool:
    """Carga los archivos de una familia. Retorna True si al menos uno cargó."""
    loaded = False
    for fname in files:
        path = _FONTS_DIR / fname
        if path.exists():
            result = QFontDatabase.addApplicationFont(str(path))
            if result != -1:
                loaded = True
    return loaded
