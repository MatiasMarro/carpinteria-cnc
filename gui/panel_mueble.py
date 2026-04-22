"""
panel_mueble.py — Panel de selección y configuración del mueble
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QPushButton, QLabel, QComboBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QFrame,
    QStackedWidget, QFormLayout, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal

from gui.config import COLORES, LABELS
from gui.state import AppState


class PanelMueble(QWidget):
    """Panel 1 — Configuración del mueble y generación de piezas."""

    mueble_generado = pyqtSignal()

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._factories: dict = {}
        self._build_ui()
        self._load_factories()

    # ── Construcción de UI ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        contenido = QWidget()
        scroll.setWidget(contenido)

        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # ── Título ────────────────────────────────────────────────────────
        layout.addWidget(self._header(
            LABELS["mueble_titulo"],
            "Seleccioná un mueble preconfigurado o ingresá dimensiones personalizadas.",
        ))

        # ── Tipo: preconfigurado / personalizado ──────────────────────────
        grp_tipo = QGroupBox("Tipo de mueble")
        tipo_layout = QHBoxLayout(grp_tipo)
        tipo_layout.setSpacing(24)

        self.rb_preconfig = QRadioButton(LABELS["mueble_preconfig"])
        self.rb_custom    = QRadioButton(LABELS["mueble_custom"])
        self.rb_preconfig.setChecked(True)
        self.rb_preconfig.toggled.connect(self._on_tipo_changed)

        tipo_layout.addWidget(self.rb_preconfig)
        tipo_layout.addWidget(self.rb_custom)
        tipo_layout.addStretch()
        layout.addWidget(grp_tipo)

        # ── Stack: preconfigurado | personalizado ─────────────────────────
        self.form_stack = QStackedWidget()

        self.form_stack.addWidget(self._build_form_preconfig())
        self.form_stack.addWidget(self._build_form_custom())

        layout.addWidget(self.form_stack)

        # ── Botón Generar ─────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_generar = QPushButton(LABELS["mueble_generar"])
        self.btn_generar.setObjectName("btnGenerar")
        self.btn_generar.setFixedHeight(42)
        self.btn_generar.setMinimumWidth(200)
        self.btn_generar.clicked.connect(self._generar)
        btn_row.addWidget(self.btn_generar)
        layout.addLayout(btn_row)

        # ── Resumen ───────────────────────────────────────────────────────
        layout.addWidget(self._build_resumen())
        layout.addStretch()

    def _header(self, titulo: str, subtitulo: str) -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet(
            f"color: {COLORES['acento_naranja']}; font-size: 14pt; font-weight: bold;"
        )
        lbl_s = QLabel(subtitulo)
        lbl_s.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 9pt;")
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORES['borde']}; max-height: 1px; margin-top:6px;")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_s)
        vbox.addWidget(sep)
        return frame

    def _build_form_preconfig(self) -> QFrame:
        frame = QFrame()
        lay = QFormLayout(frame)
        lay.setSpacing(14)
        lay.setContentsMargins(8, 8, 8, 8)

        self.cmb_preconfig = QComboBox()
        self.cmb_preconfig.setFixedWidth(260)
        lay.addRow("Mueble:", self.cmb_preconfig)
        return frame

    def _build_form_custom(self) -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(12)

        # Sub-tipo (Escritorio / Estantería)
        row = QHBoxLayout()
        lbl = QLabel("Tipo:")
        lbl.setFixedWidth(110)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Escritorio", "Estantería"])
        self.cmb_tipo.setFixedWidth(200)
        self.cmb_tipo.currentIndexChanged.connect(
            lambda idx: self.mueble_form_stack.setCurrentIndex(idx)
        )
        row.addWidget(lbl)
        row.addWidget(self.cmb_tipo)
        row.addStretch()
        vbox.addLayout(row)

        self.mueble_form_stack = QStackedWidget()
        self.mueble_form_stack.addWidget(self._build_form_escritorio())
        self.mueble_form_stack.addWidget(self._build_form_estanteria())
        vbox.addWidget(self.mueble_form_stack)
        return frame

    def _build_form_escritorio(self) -> QFrame:
        frame = QFrame()
        lay = QFormLayout(frame)
        lay.setSpacing(10)

        self.esc_ancho         = self._dspin(300, 2500, 1200)
        self.esc_prof          = self._dspin(300, 1000,  600)
        self.esc_altura        = self._dspin(600,  900,  750)
        self.esc_cajones       = self._ispin(2, 3, 2)
        self.esc_altura_cajon  = self._dspin(80, 300, 150)
        self.esc_espaldar      = QCheckBox("Incluir espaldar")
        self.esc_espaldar.setChecked(True)
        self.esc_material      = self._material_cmb()

        lay.addRow("Ancho:",            self.esc_ancho)
        lay.addRow("Profundidad:",      self.esc_prof)
        lay.addRow("Altura de trabajo:",self.esc_altura)
        lay.addRow("N.º cajones:",      self.esc_cajones)
        lay.addRow("Altura cajón:",     self.esc_altura_cajon)
        lay.addRow("",                  self.esc_espaldar)
        lay.addRow("Material:",         self.esc_material)
        return frame

    def _build_form_estanteria(self) -> QFrame:
        frame = QFrame()
        lay = QFormLayout(frame)
        lay.setSpacing(10)

        self.est_ancho    = self._dspin(300, 2500,  800)
        self.est_alto     = self._dspin(400, 2500, 1800)
        self.est_prof     = self._dspin(200,  700,  350)
        self.est_estantes = self._ispin(1, 20, 5)
        self.est_material = self._material_cmb()

        lay.addRow("Ancho:",         self.est_ancho)
        lay.addRow("Alto:",          self.est_alto)
        lay.addRow("Profundidad:",   self.est_prof)
        lay.addRow("N.º estantes:",  self.est_estantes)
        lay.addRow("Material:",      self.est_material)
        return frame

    def _build_resumen(self) -> QGroupBox:
        self.grp_resumen = QGroupBox(LABELS["mueble_resumen_titulo"])
        vbox = QVBoxLayout(self.grp_resumen)
        vbox.setSpacing(8)

        self.lbl_placeholder = QLabel(LABELS["mueble_sin_generar"])
        self.lbl_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_placeholder.setStyleSheet(f"color: {COLORES['texto_desactivado']};")
        vbox.addWidget(self.lbl_placeholder)

        self.frame_datos = QFrame()
        self.frame_datos.setVisible(False)
        datos_vbox = QVBoxLayout(self.frame_datos)
        datos_vbox.setSpacing(6)

        self.lbl_dims     = QLabel()
        self.lbl_piezas   = QLabel()
        self.lbl_costo    = QLabel()
        self.lbl_tiempo   = QLabel()
        self.lbl_material = QLabel()
        self.lbl_warnings = QLabel()
        self.lbl_warnings.setStyleSheet(f"color: {COLORES['advertencia']};")
        self.lbl_warnings.setWordWrap(True)
        self.lbl_warnings.setVisible(False)

        for lbl in (self.lbl_dims, self.lbl_piezas, self.lbl_costo,
                    self.lbl_tiempo, self.lbl_material, self.lbl_warnings):
            datos_vbox.addWidget(lbl)

        vbox.addWidget(self.frame_datos)
        return self.grp_resumen

    # ── Helpers de widgets ────────────────────────────────────────────────

    def _dspin(self, min_v: float, max_v: float, default: float) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(default)
        s.setSuffix(" mm")
        s.setDecimals(0)
        s.setFixedWidth(140)
        return s

    def _ispin(self, min_v: int, max_v: int, default: int) -> QSpinBox:
        s = QSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(default)
        s.setFixedWidth(80)
        return s

    def _material_cmb(self) -> QComboBox:
        cmb = QComboBox()
        cmb.addItems(["MDF_18", "MDF_25", "HDF", "MELAMINA_18"])
        cmb.setFixedWidth(200)
        return cmb

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_tipo_changed(self) -> None:
        self.form_stack.setCurrentIndex(0 if self.rb_preconfig.isChecked() else 1)

    def _load_factories(self) -> None:
        try:
            from furniture_escritorio import (
                escritorio_compacto, escritorio_estandar,
                escritorio_ejecutivo, escritorio_gaming,
            )
            from furniture_estanteria import (
                estanteria_pequena, estanteria_media, estanteria_grande,
            )
            self._factories = {
                "escritorio_compacto":  escritorio_compacto,
                "escritorio_estandar":  escritorio_estandar,
                "escritorio_ejecutivo": escritorio_ejecutivo,
                "escritorio_gaming":    escritorio_gaming,
                "estanteria_pequeña":   estanteria_pequena,
                "estanteria_media":     estanteria_media,
                "estanteria_grande":    estanteria_grande,
            }
            self.cmb_preconfig.addItems(list(self._factories.keys()))
        except Exception as e:
            self.cmb_preconfig.addItem(f"Error al cargar: {e}")

    def _generar(self) -> None:
        try:
            from furniture_core import MATERIALES, TipoUnion

            if self.rb_preconfig.isChecked():
                nombre = self.cmb_preconfig.currentText()
                if nombre not in self._factories:
                    raise ValueError(f"Mueble '{nombre}' no disponible.")
                mueble = self._factories[nombre]()
                self.state.nombre_mueble = nombre
            else:
                mat_key = ""
                if self.cmb_tipo.currentIndex() == 0:
                    from furniture_escritorio import Escritorio
                    mat_key = self.esc_material.currentText()
                    mueble = Escritorio(
                        ancho=self.esc_ancho.value(),
                        profundidad=self.esc_prof.value(),
                        altura_trabajo=self.esc_altura.value(),
                        num_cajones=int(self.esc_cajones.value()),
                        altura_cajon=self.esc_altura_cajon.value(),
                        material=MATERIALES[mat_key],
                        tipo_union=TipoUnion.MINIFIX,
                        incluir_espaldar=self.esc_espaldar.isChecked(),
                    )
                    self.state.nombre_mueble = (
                        f"escritorio_{int(self.esc_ancho.value())}"
                        f"x{int(self.esc_prof.value())}"
                    )
                else:
                    from furniture_estanteria import Estanteria
                    mat_key = self.est_material.currentText()
                    mueble = Estanteria(
                        ancho=self.est_ancho.value(),
                        alto=self.est_alto.value(),
                        profundidad=self.est_prof.value(),
                        num_estantes=int(self.est_estantes.value()),
                        material=MATERIALES[mat_key],
                        tipo_union=TipoUnion.MINIFIX,
                    )
                    self.state.nombre_mueble = (
                        f"estanteria_{int(self.est_ancho.value())}"
                        f"x{int(self.est_alto.value())}"
                    )

            piezas  = mueble.generar_piezas()
            resumen = mueble.resumen()

            self.state.mueble  = mueble
            self.state.piezas  = piezas
            self.state.reset_nesting()

            self._mostrar_resumen(mueble, piezas, resumen)
            self.mueble_generado.emit()

        except Exception as exc:
            self.frame_datos.setVisible(False)
            self.lbl_placeholder.setText(f"⛔  Error: {exc}")
            self.lbl_placeholder.setStyleSheet(f"color: {COLORES['error']};")
            self.lbl_placeholder.setVisible(True)

    def _mostrar_resumen(self, mueble, piezas: list, resumen: dict) -> None:
        self.lbl_placeholder.setVisible(False)
        self.frame_datos.setVisible(True)

        dims = resumen.get("dimensiones", {})
        dim_str = "  ×  ".join(f"{v} mm" for v in dims.values())
        self.lbl_dims.setText(f"Dimensiones:     {dim_str}")
        self.lbl_piezas.setText(f"Total de piezas: {len(piezas)}")
        self.lbl_costo.setText(
            f"Costo estimado:  "
            f"${resumen['costos']['material_estimado']:,.0f}"
        )
        self.lbl_tiempo.setText(
            f"Tiempo CNC:      "
            f"{resumen['produccion']['tiempo_cnc_horas']:.2f} h"
        )
        self.lbl_material.setText(f"Material:        {mueble.material}")

        warnings = resumen.get("validaciones", [])
        if warnings:
            self.lbl_warnings.setText(
                "Advertencias:\n" + "\n".join(f"  * {w}" for w in warnings)
            )
            self.lbl_warnings.setVisible(True)
        else:
            self.lbl_warnings.setVisible(False)
