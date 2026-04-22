"""
dialogo_sobrante.py — Diálogo modal para sugerencia de sobrante
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt
from gui.config import COLORES, LABELS, FUENTES


class DialogoSobrante(QDialog):
    """
    Muestra información de un sobrante disponible y pregunta al usuario
    si desea usarlo, descartarlo o saltar.

    Atributo público:
        respuesta: "u" | "d" | "s"  (usar / descartar / saltar)
    """

    def __init__(self, pieza, match, parent=None) -> None:
        super().__init__(parent)
        self.respuesta: str = "s"  # default: saltar
        self._pieza = pieza
        self._match = match
        self._build_ui()
        self.setModal(True)

    def _build_ui(self) -> None:
        self.setWindowTitle(LABELS["dialogo_titulo"])
        self.setMinimumWidth(460)
        self.setMaximumWidth(520)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Encabezado ────────────────────────────────────────────────────
        lbl_titulo = QLabel("Sobrante disponible en stock")
        lbl_titulo.setStyleSheet(
            f"color: {COLORES['acento_azul']}; font-size: 13pt; font-weight: bold;"
        )
        layout.addWidget(lbl_titulo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORES['borde']}; max-height: 1px;")
        layout.addWidget(sep)

        # ── Info de la pieza ──────────────────────────────────────────────
        p = self._pieza
        m = self._match
        s = m.sobrante

        def _fila(etiqueta: str, valor: str, color: str = "") -> QLabel:
            lbl = QLabel(f"<b>{etiqueta}</b>  {valor}")
            if color:
                lbl.setStyleSheet(f"color: {color};")
            return lbl

        layout.addWidget(_fila("Pieza:", f"{p.nombre}  "
                               f"({p.ancho:.0f} × {p.alto:.0f} mm)"))
        layout.addWidget(_fila("Sobrante ID:", f"#{s.id}"))
        layout.addWidget(_fila("Material:",
                               f"{s.material_nombre}  {s.material_espesor:.0f} mm"))
        layout.addWidget(_fila("Bounding box:",
                               f"{s.ancho_bbox:.0f} × {s.alto_bbox:.0f} mm"))
        layout.addWidget(_fila("Área disponible:",
                               f"{s.area_mm2 / 100:.0f} cm²"))
        layout.addWidget(_fila("Origen:",
                               f"{s.origen_orden or '—'}  "
                               f"(placa {s.origen_placa or '?'})"))

        posicion_txt = f"({m.pos_x:.0f}, {m.pos_y:.0f})"
        if m.rotada:
            posicion_txt += "  — rotada 90°"
        layout.addWidget(_fila("Posición sugerida:", posicion_txt,
                               color=COLORES["acento_verde"]))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {COLORES['borde']}; max-height: 1px;")
        layout.addWidget(sep2)

        hint = QLabel("Buscalo en el taller y verificá el estado antes de confirmar.")
        hint.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-style: italic;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ── Botones ───────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_usar = QPushButton(LABELS["dialogo_usar"])
        btn_usar.setStyleSheet(
            f"background-color: {COLORES['acento_verde']}; color: #FFFFFF;"
            f" font-weight: bold; border-radius: 2px; padding: 8px 20px;"
        )
        btn_usar.clicked.connect(self._usar)

        btn_descartar = QPushButton(LABELS["dialogo_descartar"])
        btn_descartar.setStyleSheet(
            f"background-color: {COLORES['boton_peligro']}; color: #FFFFFF;"
            f" font-weight: bold; border-radius: 2px; padding: 8px 20px;"
        )
        btn_descartar.clicked.connect(self._descartar)

        btn_saltar = QPushButton(LABELS["dialogo_saltar"])
        btn_saltar.setStyleSheet(
            f"background-color: {COLORES['boton_secundario']}; color: {COLORES['texto_primario']};"
            f" font-weight: bold; border-radius: 2px; padding: 8px 20px;"
        )
        btn_saltar.clicked.connect(self._saltar)

        btn_layout.addWidget(btn_usar)
        btn_layout.addWidget(btn_descartar)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_saltar)

        layout.addLayout(btn_layout)

        # Stylesheet de la ventana
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORES['fondo_panel']};
                color: {COLORES['texto_primario']};
                font-family: "{FUENTES['familia']}", "{FUENTES['familia_fallback']}";
                font-size: {FUENTES['size_normal']}pt;
            }}
            QLabel {{
                background: transparent;
                color: {COLORES['texto_primario']};
            }}
        """)

    def _usar(self) -> None:
        self.respuesta = "u"
        self.accept()

    def _descartar(self) -> None:
        self.respuesta = "d"
        self.accept()

    def _saltar(self) -> None:
        self.respuesta = "s"
        self.accept()
