"""
main_window.py — Ventana principal con stepper wizard 3-pasos
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from gui.config import COLORES, LABELS, DIMENSIONES, FUENTES, COPYRIGHT
from gui.state import AppState
from gui.panel_mueble import PanelMueble
from gui.panel_nesting import PanelNesting
from gui.panel_exportar import PanelExportar


# ── Stepper header ─────────────────────────────────────────────────────────

class _StepperHeader(QWidget):
    """Barra superior con 3 círculos numerados y líneas conectoras."""

    PASOS = [
        (LABELS["paso_1_titulo"], LABELS["paso_1_sub"]),
        (LABELS["paso_2_titulo"], LABELS["paso_2_sub"]),
        (LABELS["paso_3_titulo"], LABELS["paso_3_sub"]),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._paso_actual   = 0
        self._paso_maximo   = 0   # hasta qué paso se llegó (desbloquea)
        self.setFixedHeight(DIMENSIONES["stepper_alto"])
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(0)

        self._items: list[_StepItem] = []
        for i, (titulo, sub) in enumerate(self.PASOS):
            item = _StepItem(i + 1, titulo, sub)
            self._items.append(item)
            layout.addWidget(item, stretch=2)
            if i < len(self.PASOS) - 1:
                line = _StepLine()
                self._items_lines = getattr(self, "_items_lines", [])
                self._items_lines.append(line)
                layout.addWidget(line, stretch=1)

        self._refresh()

    def set_paso(self, idx: int) -> None:
        self._paso_actual = idx
        self._paso_maximo = max(self._paso_maximo, idx)
        self._refresh()

    def marcar_completado(self, idx: int) -> None:
        self._paso_maximo = max(self._paso_maximo, idx + 1)
        self._refresh()

    def _refresh(self) -> None:
        for i, item in enumerate(self._items):
            if i < self._paso_actual:
                item.set_estado("completado")
            elif i == self._paso_actual:
                item.set_estado("activo")
            else:
                item.set_estado("bloqueado")

        lines = getattr(self, "_items_lines", [])
        for i, line in enumerate(lines):
            line.set_hecha(i < self._paso_actual)


class _StepLine(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(2)
        self._hecha = False
        self._apply()

    def set_hecha(self, v: bool) -> None:
        self._hecha = v
        self._apply()

    def _apply(self) -> None:
        color = COLORES["paso_linea_hecha"] if self._hecha else COLORES["paso_linea"]
        self.setStyleSheet(f"background: {color}; max-height: 2px; margin-top: 1px;")


class _StepItem(QWidget):
    CIRCLE_R = 18

    def __init__(self, numero: int, titulo: str, sub: str) -> None:
        super().__init__()
        self._numero = numero
        self._titulo = titulo
        self._sub    = sub
        self._estado = "bloqueado"
        self.setFixedHeight(DIMENSIONES["stepper_alto"])
        self._build()

    def _build(self) -> None:
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 8, 0, 8)
        vbox.setSpacing(2)
        vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Fila: círculo + título
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._circulo = _StepCircle(self._numero)
        row.addWidget(self._circulo)

        col = QVBoxLayout()
        col.setSpacing(1)
        self._lbl_t = QLabel(self._titulo)
        self._lbl_t.setStyleSheet(
            f"color: {COLORES['texto_desactivado']}; font-weight: bold; font-size: 10pt;"
        )
        self._lbl_s = QLabel(self._sub)
        self._lbl_s.setStyleSheet(
            f"color: {COLORES['texto_desactivado']}; font-size: 8pt;"
        )
        col.addWidget(self._lbl_t)
        col.addWidget(self._lbl_s)
        row.addLayout(col)

        vbox.addLayout(row)

    def set_estado(self, estado: str) -> None:
        self._estado = estado
        self._circulo.set_estado(estado)

        if estado == "activo":
            self._lbl_t.setStyleSheet(
                f"color: {COLORES['paso_activo']}; font-weight: bold; font-size: 10pt;"
            )
            self._lbl_s.setStyleSheet(
                f"color: {COLORES['texto_secundario']}; font-size: 8pt;"
            )
        elif estado == "completado":
            self._lbl_t.setStyleSheet(
                f"color: {COLORES['paso_completado']}; font-weight: bold; font-size: 10pt;"
            )
            self._lbl_s.setStyleSheet(
                f"color: {COLORES['texto_secundario']}; font-size: 8pt;"
            )
        else:
            self._lbl_t.setStyleSheet(
                f"color: {COLORES['texto_desactivado']}; font-weight: bold; font-size: 10pt;"
            )
            self._lbl_s.setStyleSheet(
                f"color: {COLORES['texto_desactivado']}; font-size: 8pt;"
            )


class _StepCircle(QWidget):
    R = 18

    def __init__(self, numero: int) -> None:
        super().__init__()
        self._numero = numero
        self._estado = "bloqueado"
        self.setFixedSize(self.R * 2 + 2, self.R * 2 + 2)

    def set_estado(self, estado: str) -> None:
        self._estado = estado
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() // 2, self.height() // 2

        if self._estado == "activo":
            fill  = QColor(COLORES["paso_activo"])
            text  = QColor(COLORES["paso_activo_texto"])
            pen_c = QColor(COLORES["paso_activo"])
        elif self._estado == "completado":
            fill  = QColor(COLORES["paso_completado"])
            text  = QColor(COLORES["paso_completado_texto"])
            pen_c = QColor(COLORES["paso_completado"])
        else:
            fill  = QColor(COLORES["paso_bloqueado"])
            text  = QColor(COLORES["paso_bloqueado_texto"])
            pen_c = QColor(COLORES["paso_bloqueado"])

        pen = QPen(pen_c, 2)
        p.setPen(pen)
        p.setBrush(fill)
        p.drawEllipse(cx - self.R, cy - self.R, self.R * 2, self.R * 2)

        if self._estado == "completado":
            p.setPen(QPen(text, 2))
            p.setFont(QFont(FUENTES["familia"], 9, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "✓")
        else:
            p.setPen(QPen(text, 1))
            p.setFont(QFont(FUENTES["familia"], 9, QFont.Weight.Bold))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self._numero))


# ── Footer ─────────────────────────────────────────────────────────────────

class _Footer(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(DIMENSIONES["footer_alto"])
        self.setObjectName("footer")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 0, 32, 0)

        self.btn_volver = QPushButton(LABELS["btn_volver"])
        self.btn_volver.setObjectName("btnVolver")
        self.btn_volver.setFixedHeight(38)
        self.btn_volver.setMinimumWidth(130)

        self.lbl_estado = QLabel()
        self.lbl_estado.setObjectName("footerEstado")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_continuar = QPushButton(LABELS["btn_continuar"])
        self.btn_continuar.setObjectName("btnContinuar")
        self.btn_continuar.setFixedHeight(38)
        self.btn_continuar.setMinimumWidth(160)
        self.btn_continuar.setEnabled(False)

        layout.addWidget(self.btn_volver)
        layout.addStretch()
        layout.addWidget(self.lbl_estado)
        layout.addStretch()
        layout.addWidget(self.btn_continuar)


# ── Ventana principal ──────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Ventana principal — stepper wizard de 3 pasos."""

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self._paso = 0
        self._setup_window()
        self._build_ui()
        self._apply_stylesheet()
        self._ir_paso(0)

    def _setup_window(self) -> None:
        self.setWindowTitle(LABELS["app_nombre"])
        self.setMinimumSize(
            DIMENSIONES["ventana_min_ancho"],
            DIMENSIONES["ventana_min_alto"],
        )
        self.resize(DIMENSIONES["ventana_ancho"], DIMENSIONES["ventana_alto"])

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # ── Header con nombre de app + stepper ────────────────────────────
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        header_vbox = QVBoxLayout(self.header_frame)
        header_vbox.setContentsMargins(0, 0, 0, 0)
        header_vbox.setSpacing(0)

        # Topbar: logo izquierda
        topbar = QFrame()
        topbar.setObjectName("topBar")
        topbar.setFixedHeight(44)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(24, 0, 24, 0)
        lbl_logo = QLabel(LABELS["app_nombre"].upper())
        lbl_logo.setObjectName("lblLogo")
        lbl_copy = QLabel(COPYRIGHT)
        lbl_copy.setObjectName("lblTopCopy")
        topbar_layout.addWidget(lbl_logo)
        topbar_layout.addStretch()
        topbar_layout.addWidget(lbl_copy)
        header_vbox.addWidget(topbar)

        # Separador
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setObjectName("sepHeader")
        header_vbox.addWidget(sep1)

        # Stepper
        self.stepper = _StepperHeader()
        header_vbox.addWidget(self.stepper)

        # Separador inferior
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setObjectName("sepHeader")
        header_vbox.addWidget(sep2)

        vbox.addWidget(self.header_frame)

        # ── Stack de paneles ──────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.panel_mueble  = PanelMueble(self.state, self)
        self.panel_nesting = PanelNesting(self.state, self)
        self.panel_exportar = PanelExportar(self.state, self)
        self.stack.addWidget(self.panel_mueble)    # 0
        self.stack.addWidget(self.panel_nesting)   # 1
        self.stack.addWidget(self.panel_exportar)  # 2
        vbox.addWidget(self.stack, stretch=1)

        # ── Footer ────────────────────────────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setObjectName("sepFooter")
        vbox.addWidget(sep3)

        self.footer = _Footer()
        vbox.addWidget(self.footer)

        # ── Señales ───────────────────────────────────────────────────────
        self.panel_mueble.mueble_generado.connect(self._on_mueble_generado)
        self.panel_nesting.nesting_calculado.connect(self._on_nesting_calculado)
        self.footer.btn_continuar.clicked.connect(self._continuar)
        self.footer.btn_volver.clicked.connect(self._volver)

    # ── Navegación ────────────────────────────────────────────────────────

    def _ir_paso(self, idx: int) -> None:
        self._paso = idx
        self.stack.setCurrentIndex(idx)
        self.stepper.set_paso(idx)

        # Footer izquierdo
        self.footer.btn_volver.setVisible(idx > 0)

        # Estado del botón continuar según paso
        if idx == 0:
            self._set_continuar(self.state.tiene_mueble, "Generá el mueble para continuar")
        elif idx == 1:
            self.panel_nesting.actualizar_estado()
            self._set_continuar(self.state.tiene_nesting, "Calculá el nesting para continuar")
        elif idx == 2:
            self.panel_exportar.actualizar_estado()
            self.footer.btn_continuar.setVisible(False)

        # Mensaje del footer según paso
        if idx < 2:
            self.footer.btn_continuar.setVisible(True)

    def _continuar(self) -> None:
        if self._paso < 2:
            self._ir_paso(self._paso + 1)

    def _volver(self) -> None:
        if self._paso > 0:
            self._ir_paso(self._paso - 1)

    def _set_continuar(self, habilitado: bool, tooltip: str = "") -> None:
        self.footer.btn_continuar.setEnabled(habilitado)
        self.footer.btn_continuar.setToolTip("" if habilitado else tooltip)

    # ── Slots de señales de paneles ───────────────────────────────────────

    @pyqtSlot()
    def _on_mueble_generado(self) -> None:
        self.stepper.marcar_completado(0)
        self._set_continuar(True)
        self.footer.lbl_estado.setText("✓  Mueble generado — podés continuar al nesting")
        self.footer.lbl_estado.setStyleSheet(f"color: {COLORES['exito']}; font-size: 9pt;")
        self.panel_nesting.actualizar_estado()

    @pyqtSlot()
    def _on_nesting_calculado(self) -> None:
        self.stepper.marcar_completado(1)
        self._set_continuar(True)
        self.footer.lbl_estado.setText("✓  Nesting calculado — podés exportar")
        self.footer.lbl_estado.setStyleSheet(f"color: {COLORES['exito']}; font-size: 9pt;")
        self.panel_exportar.actualizar_estado()

    # ── Stylesheet ────────────────────────────────────────────────────────

    def _apply_stylesheet(self) -> None:
        c = COLORES
        f = FUENTES
        ff  = f["familia"]
        ffm = f["familia_mono"]

        self.setStyleSheet(f"""
            /* ── Base ─────────────────────────────────────────────────── */
            QMainWindow, QWidget {{
                background-color: {c["fondo_app"]};
                color: {c["texto_primario"]};
                font-family: "{ff}", "{f["familia_fallback"]}";
                font-size: {f["size_normal"]}pt;
            }}

            /* ── Header / topbar ──────────────────────────────────────── */
            QFrame#headerFrame {{
                background-color: {c["fondo_panel"]};
            }}
            QFrame#topBar {{
                background-color: #080808;
            }}
            QLabel#lblLogo {{
                color: {c["acento_naranja"]};
                font-size: 11pt;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QLabel#lblTopCopy {{
                color: {c["texto_desactivado"]};
                font-size: 8pt;
            }}
            QFrame#sepHeader, QFrame#sepFooter {{
                background-color: {c["borde"]};
                max-height: 1px;
            }}

            /* ── Footer ───────────────────────────────────────────────── */
            QFrame#footer {{
                background-color: {c["fondo_panel"]};
            }}
            QLabel#footerEstado {{
                color: {c["texto_secundario"]};
                font-size: 9pt;
            }}

            /* ── Botón Continuar ──────────────────────────────────────── */
            QPushButton#btnContinuar {{
                background-color: {c["boton_primario"]};
                color: {c["boton_primario_texto"]};
                border: none;
                border-radius: 2px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: {f["size_normal"]}pt;
            }}
            QPushButton#btnContinuar:hover {{
                background-color: {c["boton_primario_hover"]};
            }}
            QPushButton#btnContinuar:disabled {{
                background-color: {c["borde"]};
                color: {c["texto_desactivado"]};
            }}

            /* ── Botón Volver ─────────────────────────────────────────── */
            QPushButton#btnVolver {{
                background-color: transparent;
                color: {c["texto_secundario"]};
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                padding: 8px 18px;
                font-size: {f["size_normal"]}pt;
            }}
            QPushButton#btnVolver:hover {{
                background-color: {c["boton_secundario_hover"]};
                color: {c["texto_primario"]};
            }}

            /* ── Botones genéricos ────────────────────────────────────── */
            QPushButton {{
                background-color: {c["boton_primario"]};
                color: {c["boton_primario_texto"]};
                border: none;
                border-radius: 2px;
                padding: 7px 20px;
                font-weight: bold;
                font-size: {f["size_normal"]}pt;
            }}
            QPushButton:hover {{
                background-color: {c["boton_primario_hover"]};
            }}
            QPushButton:disabled {{
                background-color: {c["fondo_input"]};
                color: {c["texto_desactivado"]};
            }}

            /* ── Botón outline (sobrantes) ────────────────────────────── */
            QPushButton#btnSobrantes {{
                background-color: transparent;
                color: {c["boton_outline_texto"]};
                border: 1px solid {c["boton_outline_borde"]};
                border-radius: 2px;
                padding: 7px 16px;
                font-weight: normal;
            }}
            QPushButton#btnSobrantes:hover {{
                background-color: {c["boton_outline_hover"]};
            }}
            QPushButton#btnSobrantes:disabled {{
                color: {c["texto_desactivado"]};
                border-color: {c["borde"]};
            }}

            /* ── Botón secundario ─────────────────────────────────────── */
            QPushButton#btnSecundario {{
                background-color: {c["boton_secundario"]};
                color: {c["boton_secundario_texto"]};
                border: none;
                font-weight: normal;
            }}
            QPushButton#btnSecundario:hover {{
                background-color: {c["boton_secundario_hover"]};
            }}

            /* ── Inputs ───────────────────────────────────────────────── */
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
                background-color: {c["fondo_input"]};
                color: {c["texto_primario"]};
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                padding: 5px 9px;
                selection-background-color: {c["acento_naranja"]};
                selection-color: #000000;
            }}
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {c["borde_activo"]};
            }}
            QComboBox QAbstractItemView {{
                background-color: {c["fondo_input"]};
                color: {c["texto_primario"]};
                selection-background-color: {c["acento_naranja"]};
                selection-color: #000000;
            }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {c["borde"]};
                border: none;
                width: 18px;
            }}
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {c["acento_naranja"]};
            }}

            /* ── GroupBox ─────────────────────────────────────────────── */
            QGroupBox {{
                color: {c["texto_secundario"]};
                font-weight: bold;
                font-size: {f["size_subtitulo"]}pt;
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                margin-top: 14px;
                padding-top: 10px;
                background-color: {c["fondo_tarjeta"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 14px;
                padding: 0 6px;
                color: {c["texto_secundario"]};
                background-color: {c["fondo_tarjeta"]};
            }}

            /* ── Labels ───────────────────────────────────────────────── */
            QLabel {{
                color: {c["texto_primario"]};
                background: transparent;
            }}

            /* ── TextEdit ─────────────────────────────────────────────── */
            QTextEdit {{
                background-color: {c["fondo_input"]};
                color: {c["texto_primario"]};
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                font-family: "{ffm}", "{f["familia_mono_fallback"]}";
                font-size: {f["size_pequeño"]}pt;
            }}

            /* ── Tabla ────────────────────────────────────────────────── */
            QTableWidget {{
                background-color: {c["fondo_app"]};
                color: {c["texto_primario"]};
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                gridline-color: {c["borde"]};
                alternate-background-color: {c["tabla_fila_impar"]};
            }}
            QTableWidget::item {{ padding: 4px 8px; }}
            QTableWidget::item:selected {{
                background-color: {c["tabla_seleccion"]};
                color: {c["acento_naranja"]};
            }}
            QHeaderView::section {{
                background-color: {c["tabla_header"]};
                color: {c["texto_secundario"]};
                padding: 6px 8px;
                border: none;
                border-right: 1px solid {c["borde"]};
                border-bottom: 1px solid {c["borde"]};
                font-weight: bold;
                font-size: 9pt;
            }}

            /* ── Scrollbars ───────────────────────────────────────────── */
            QScrollBar:vertical {{
                background: {c["fondo_panel"]}; width: 7px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {c["borde"]}; border-radius: 2px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {c["acento_naranja"]}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {c["fondo_panel"]}; height: 7px; border-radius: 2px;
            }}
            QScrollBar::handle:horizontal {{
                background: {c["borde"]}; border-radius: 2px; min-width: 24px;
            }}
            QScrollBar::handle:horizontal:hover {{ background: {c["acento_naranja"]}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

            /* ── ProgressBar ──────────────────────────────────────────── */
            QProgressBar {{
                background-color: {c["fondo_input"]};
                border: 1px solid {c["borde"]};
                border-radius: 2px;
                text-align: center;
                color: {c["texto_primario"]};
                font-size: 8pt;
            }}
            QProgressBar::chunk {{
                background-color: {c["acento_naranja"]};
                border-radius: 2px;
            }}

            /* ── Radio / Checkbox ─────────────────────────────────────── */
            QRadioButton, QCheckBox {{
                color: {c["texto_primario"]};
                spacing: 8px;
            }}
            QRadioButton::indicator, QCheckBox::indicator {{
                width: 15px; height: 15px;
                border: 2px solid {c["borde"]};
                border-radius: 2px;
                background: {c["fondo_input"]};
            }}
            QRadioButton::indicator {{ border-radius: 8px; }}
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
                background: {c["acento_naranja"]};
                border: 2px solid {c["acento_naranja"]};
            }}

            /* ── Splitter ─────────────────────────────────────────────── */
            QSplitter::handle {{
                background: {c["borde"]};
            }}

            /* ── Diálogos ─────────────────────────────────────────────── */
            QDialog {{
                background-color: {c["fondo_panel"]};
                border: 1px solid {c["borde"]};
            }}

            /* ── ScrollArea ───────────────────────────────────────────── */
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)

