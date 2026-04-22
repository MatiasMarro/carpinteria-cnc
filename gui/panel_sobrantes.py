"""
panel_sobrantes.py — Diálogo modal de gestión de sobrantes en DB
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QAbstractItemView, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from gui.config import COLORES, LABELS

_ESTADO_COLORES = {
    "disponible": COLORES["exito"],
    "usado":      COLORES["texto_desactivado"],
    "descartado": COLORES["error"],
}

_COLUMNAS = [
    LABELS["col_id"],
    LABELS["col_material"],
    LABELS["col_bbox"],
    LABELS["col_area"],
    LABELS["col_origen"],
    LABELS["col_placa"],
    LABELS["col_fecha"],
    LABELS["col_estado"],
    LABELS["col_acciones"],
]


class DialogoSobrantes(QDialog):
    """Diálogo modal — Tabla de sobrantes con filtros y acción de descarte."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(LABELS["sobrantes_titulo"])
        self.resize(900, 560)
        self._todos: list = []
        self._build_ui()
        self.cargar_sobrantes()

    # Alias para compatibilidad con código que usaba PanelSobrantes
    PanelSobrantes = None  # se redefine abajo

    # ── Construcción ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)

        # Título
        layout.addWidget(self._header())

        # Barra de filtros + botón actualizar
        barra = QHBoxLayout()
        barra.setSpacing(12)

        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Todos", "disponible", "usado", "descartado"])
        self.cmb_estado.setFixedWidth(140)
        self.cmb_estado.currentIndexChanged.connect(self._aplicar_filtro)

        lbl_mat = QLabel("Material:")
        lbl_mat.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.cmb_material = QComboBox()
        self.cmb_material.addItem("Todos")
        self.cmb_material.setFixedWidth(180)
        self.cmb_material.currentIndexChanged.connect(self._aplicar_filtro)

        btn_actualizar = QPushButton(LABELS["sobrantes_actualizar"])
        btn_actualizar.setFixedWidth(140)
        btn_actualizar.clicked.connect(self.cargar_sobrantes)

        barra.addWidget(lbl_estado)
        barra.addWidget(self.cmb_estado)
        barra.addWidget(lbl_mat)
        barra.addWidget(self.cmb_material)
        barra.addStretch()
        barra.addWidget(btn_actualizar)
        layout.addLayout(barra)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(len(_COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(_COLUMNAS)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla, stretch=1)

        # Placeholder
        self.lbl_vacio = QLabel(LABELS["sobrantes_sin_datos"])
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setStyleSheet(f"color: {COLORES['texto_desactivado']}; padding: 24px;")
        self.lbl_vacio.setVisible(False)
        layout.addWidget(self.lbl_vacio)

        # Resumen
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 9pt;")
        layout.addWidget(self.lbl_resumen)

        # Botón cerrar
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecundario")
        btn_cerrar.setFixedWidth(120)
        btn_cerrar.clicked.connect(self.accept)
        btn_box.addWidget(btn_cerrar)
        layout.addLayout(btn_box)

        self._todos: list = []

    def _header(self) -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        lbl_t = QLabel(LABELS["sobrantes_titulo"])
        lbl_t.setStyleSheet(
            f"color: {COLORES['acento_naranja']}; font-size: 14pt; font-weight: bold;"
        )
        lbl_s = QLabel(
            "Stock de retazos disponibles generados en órdenes anteriores."
        )
        lbl_s.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 9pt;")
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORES['borde']}; max-height: 1px; margin-top:4px;")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_s)
        vbox.addWidget(sep)
        return frame

    # ── API pública ───────────────────────────────────────────────────────

    def cargar_sobrantes(self) -> None:
        """Recarga todos los sobrantes desde la DB y refresca la tabla."""
        try:
            from sobrantes_db import init_db, listar_todos
            init_db()
            self._todos = listar_todos()
        except Exception as exc:
            self._todos = []
            self.lbl_resumen.setText(f"Error al leer DB: {exc}")

        # Actualizar combo de materiales
        materiales = sorted({s.material_nombre for s in self._todos})
        self.cmb_material.blockSignals(True)
        self.cmb_material.clear()
        self.cmb_material.addItem("Todos")
        self.cmb_material.addItems(materiales)
        self.cmb_material.blockSignals(False)

        self._aplicar_filtro()

    # ── Internos ──────────────────────────────────────────────────────────

    def _aplicar_filtro(self) -> None:
        estado_filtro   = self.cmb_estado.currentText()
        material_filtro = self.cmb_material.currentText()

        filtrados = [
            s for s in self._todos
            if (estado_filtro   == "Todos" or s.estado          == estado_filtro)
            and (material_filtro == "Todos" or s.material_nombre == material_filtro)
        ]

        self._poblar_tabla(filtrados)

    def _poblar_tabla(self, sobrantes: list) -> None:
        self.tabla.setRowCount(0)

        if not sobrantes:
            self.tabla.setVisible(False)
            self.lbl_vacio.setVisible(True)
            self.lbl_resumen.setText("")
            return

        self.tabla.setVisible(True)
        self.lbl_vacio.setVisible(False)
        self.tabla.setRowCount(len(sobrantes))

        for row, s in enumerate(sobrantes):
            fecha_corta = s.fecha_creacion[:10] if s.fecha_creacion else "—"

            valores = [
                str(s.id),
                f"{s.material_nombre} {s.material_espesor:.0f}mm",
                f"{s.ancho_bbox:.0f} × {s.alto_bbox:.0f}",
                f"{s.area_mm2 / 100:.0f}",
                s.origen_orden or "—",
                str(s.origen_placa) if s.origen_placa else "—",
                fecha_corta,
                s.estado,
            ]

            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 7:  # estado
                    item.setForeground(
                        QColor(
                            _ESTADO_COLORES.get(s.estado, COLORES["texto_primario"])
                        )
                    )
                self.tabla.setItem(row, col, item)

            # Botón descartar (solo si disponible)
            if s.estado == "disponible":
                btn = QPushButton(LABELS["sobrantes_descartar"])
                btn.setFixedHeight(28)
                btn.setStyleSheet(
                    f"background-color: {COLORES['boton_peligro']};"
                    f"color: #FFFFFF; border-radius:2px; font-weight:bold;"
                    f"padding: 0px 10px;"
                )
                btn.clicked.connect(lambda _checked, sid=s.id: self._descartar(sid))
                self.tabla.setCellWidget(row, 8, btn)
            else:
                self.tabla.setItem(row, 8, QTableWidgetItem("—"))

        disponibles = sum(1 for s in sobrantes if s.estado == "disponible")
        area_total  = sum(s.area_mm2 / 100 for s in sobrantes if s.estado == "disponible")
        self.lbl_resumen.setText(
            f"Mostrando {len(sobrantes)} sobrantes  •  "
            f"{disponibles} disponibles  •  "
            f"Área total disponible: {area_total:,.0f} cm²"
        )

    def _descartar(self, sobrante_id: int) -> None:
        try:
            from sobrantes_db import marcar_descartado
            marcar_descartado(sobrante_id)
            self.cargar_sobrantes()
        except Exception as exc:
            self.lbl_resumen.setText(f"Error: {exc}")
