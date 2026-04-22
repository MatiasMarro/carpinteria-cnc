"""
gui_app.py — Punto de entrada principal de la interfaz gráfica.
Ejecutar con:  python gui_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que src/ esté en el path antes de cualquier import del proyecto
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow


def main() -> None:
    # Habilitar DPI alto en Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Carpintería CNC 2.0")
    app.setOrganizationName("Carpintería CNC")

    # Cargar tipografías IBM Plex antes de construir la ventana
    from gui.font_loader import load_fonts
    familia, familia_mono = load_fonts()

    # Parchar config con las familias resueltas (fallback si no hay archivos)
    import gui.config as cfg
    cfg.FUENTES["familia"]    = familia
    cfg.FUENTES["familia_mono"] = familia_mono

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
