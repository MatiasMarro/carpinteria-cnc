"""
gui/__init__.py
Asegura que src/ esté en el path antes de cualquier import del backend.
"""
import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
