"""
panel_nesting.py — Panel de nesting con visor gráfico de placas
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox,
    QCheckBox, QFrame, QScrollArea, QSizePolicy,
    QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot

from gui.config import COLORES, LABELS
from gui.state import AppState
from gui.nesting_canvas import NestingCanvas


# ===========================================================================
# Worker thread — ejecuta nesting sin bloquear la UI
# ===========================================================================

class _NestingWorker(QThread):
    terminado = pyqtSignal(object)   # ResultadoNesting
    error     = pyqtSignal(str)

    def __init__(
        self,
        piezas: list,
        placa_ancho: float,
        placa_alto: float,
        margen_corte: float,
        max_placas: int,
    ) -> None:
        super().__init__()
        self.piezas       = piezas
        self.placa_ancho  = placa_ancho
        self.placa_alto   = placa_alto
        self.margen_corte = margen_corte
        self.max_placas   = max_placas

    def run(self) -> None:
        try:
            from nesting_engine import nesting_automatico
            resultado = nesting_automatico(
                piezas=self.piezas,
                placa_ancho=self.placa_ancho,
                placa_alto=self.placa_alto,
                margen_corte=self.margen_corte,
                permitir_rotacion=True,
                max_placas=self.max_placas,
            )
            self.terminado.emit(resultado)
        except Exception as exc:
            import traceback
            self.error.emit(traceback.format_exc())


# ===========================================================================
# Panel principal
# ===========================================================================

class PanelNesting(QWidget):
    """Panel 2 — Configuración, cálculo y visualización del nesting."""

    nesting_calculado = pyqtSignal()

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state  = state
        self._worker: _NestingWorker | None = None
        self._build_ui()

    # ── Construcción de UI ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Splitter vertical: arriba=controles, abajo=canvas
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORES['borde']}; height: 2px; }}")
        outer.addWidget(splitter)

        # ── Panel superior: controles ─────────────────────────────────────
        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(28, 24, 28, 12)
        top_layout.setSpacing(16)
        splitter.addWidget(top)

        top_layout.addWidget(self._header())

        # Aviso "sin mueble"
        self.lbl_sin_mueble = QLabel(LABELS["nesting_sin_mueble"])
        self.lbl_sin_mueble.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_mueble.setStyleSheet(f"color: {COLORES['advertencia']}; padding: 16px;")
        top_layout.addWidget(self.lbl_sin_mueble)

        # Contenido
        self.frame_contenido = QFrame()
        self.frame_contenido.setVisible(False)
        contenido_layout = QVBoxLayout(self.frame_contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        contenido_layout.setSpacing(14)
        top_layout.addWidget(self.frame_contenido)

        # Parámetros
        grp_params = QGroupBox(LABELS["nesting_params"])
        params_layout = QHBoxLayout(grp_params)
        params_layout.setSpacing(24)

        self.spin_mecha       = self._dspin(2, 20, 4, " mm", "Mecha (margen entre piezas)")
        self.spin_placa_ancho = self._dspin(500, 3000, 1830, " mm", "Ancho de placa")
        self.spin_placa_alto  = self._dspin(500, 3000, 2750, " mm", "Alto de placa")
        self.spin_max_placas  = self._ispin(1, 30, 10, "Máx. placas")

        for label, widget in [
            ("Mecha:", self.spin_mecha),
            ("Placa ancho:", self.spin_placa_ancho),
            ("Placa alto:", self.spin_placa_alto),
            ("Máx. placas:", self.spin_max_placas),
        ]:
            col = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 9pt;")
            col.addWidget(lbl)
            col.addWidget(widget)
            params_layout.addLayout(col)

        params_layout.addStretch()
        contenido_layout.addWidget(grp_params)

        # Fila: botón sobrantes (outline) + botón calcular (primario)
        row = QHBoxLayout()
        row.setSpacing(12)

        self.btn_sobrantes = QPushButton(LABELS["nesting_sobrantes_btn"])
        self.btn_sobrantes.setObjectName("btnSobrantes")
        self.btn_sobrantes.setFixedHeight(40)
        self.btn_sobrantes.setMinimumWidth(200)
        self.btn_sobrantes.setEnabled(False)
        self.btn_sobrantes.setToolTip(LABELS["nesting_sobrantes_tip"])
        self.btn_sobrantes.clicked.connect(self._abrir_sobrantes)
        row.addWidget(self.btn_sobrantes)

        row.addStretch()

        self.btn_calcular = QPushButton(LABELS["nesting_calcular"])
        self.btn_calcular.setObjectName("btnCalcuar")
        self.btn_calcular.setFixedHeight(40)
        self.btn_calcular.setMinimumWidth(200)
        self.btn_calcular.clicked.connect(self._calcular)
        row.addWidget(self.btn_calcular)
        contenido_layout.addLayout(row)

        # Estado de sobrantes usados
        self.lbl_sobrantes_estado = QLabel()
        self.lbl_sobrantes_estado.setStyleSheet(
            f"color: {COLORES['acento_verde']}; font-size: 9pt;"
        )
        self.lbl_sobrantes_estado.setVisible(False)
        contenido_layout.addWidget(self.lbl_sobrantes_estado)

        # Resultado (estadísticas)
        self.grp_resultado = QGroupBox(LABELS["nesting_resultado"])
        resultado_layout = QHBoxLayout(self.grp_resultado)
        resultado_layout.setSpacing(32)

        self.lbl_placas      = self._stat_lbl("—", "Placas")
        self.lbl_eficiencia  = self._stat_lbl("—", "Eficiencia promedio")
        self.lbl_colocadas   = self._stat_lbl("—", "Piezas colocadas")
        self.lbl_no_colocadas = self._stat_lbl("—", "No colocadas", COLORES["error"])

        for w in (self.lbl_placas, self.lbl_eficiencia,
                  self.lbl_colocadas, self.lbl_no_colocadas):
            resultado_layout.addWidget(w)
        resultado_layout.addStretch()

        self.grp_resultado.setVisible(False)
        contenido_layout.addWidget(self.grp_resultado)

        top_layout.addStretch()

        # ── Panel inferior: canvas ────────────────────────────────────────
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(28, 8, 28, 16)
        bottom_layout.setSpacing(8)
        splitter.addWidget(bottom)

        # Navegación de placas
        nav = QHBoxLayout()
        self.btn_anterior = QPushButton("◀  Anterior")
        self.btn_anterior.setFixedWidth(130)
        self.btn_anterior.setEnabled(False)
        self.btn_anterior.clicked.connect(self._placa_anterior)

        self.lbl_placa_info = QLabel(LABELS["nesting_sin_calcular"])
        self.lbl_placa_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_placa_info.setStyleSheet(f"color: {COLORES['texto_secundario']};")

        self.btn_siguiente = QPushButton("Siguiente  ▶")
        self.btn_siguiente.setFixedWidth(130)
        self.btn_siguiente.setEnabled(False)
        self.btn_siguiente.clicked.connect(self._placa_siguiente)

        nav.addWidget(self.btn_anterior)
        nav.addStretch()
        nav.addWidget(self.lbl_placa_info)
        nav.addStretch()
        nav.addWidget(self.btn_siguiente)
        bottom_layout.addLayout(nav)

        # Canvas matplotlib
        self.canvas = NestingCanvas()
        bottom_layout.addWidget(self.canvas, stretch=1)

        splitter.setSizes([260, 440])

    def _header(self) -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        lbl_t = QLabel(LABELS["nesting_titulo"])
        lbl_t.setStyleSheet(
            f"color: {COLORES['acento_naranja']}; font-size: 14pt; font-weight: bold;"
        )
        lbl_s = QLabel("Configurá la placa y calculá la distribución óptima de piezas.")
        lbl_s.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 9pt;")
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {COLORES['borde']}; max-height: 1px; margin-top:4px;")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_s)
        vbox.addWidget(sep)
        return frame

    def _dspin(self, min_v, max_v, default, suffix="", tooltip="") -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(default)
        s.setSuffix(suffix)
        s.setDecimals(0)
        s.setFixedWidth(120)
        if tooltip:
            s.setToolTip(tooltip)
        return s

    def _ispin(self, min_v, max_v, default, tooltip="") -> QSpinBox:
        s = QSpinBox()
        s.setRange(min_v, max_v)
        s.setValue(default)
        s.setFixedWidth(80)
        if tooltip:
            s.setToolTip(tooltip)
        return s

    def _stat_lbl(self, valor: str, etiqueta: str, color: str = "") -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet(
            f"color: {color or COLORES['acento_naranja']}; font-size: 18pt; font-weight: bold;"
        )
        lbl_e = QLabel(etiqueta)
        lbl_e.setStyleSheet(f"color: {COLORES['texto_secundario']}; font-size: 8pt;")

        vbox.addWidget(lbl_v)
        vbox.addWidget(lbl_e)

        # guardar referencia al label de valor
        frame._lbl_valor = lbl_v  # type: ignore[attr-defined]
        frame._color_base = color or COLORES["acento_naranja"]  # type: ignore[attr-defined]
        return frame

    # ── API pública ───────────────────────────────────────────────────────

    def actualizar_estado(self) -> None:
        """Llamado por MainWindow al navegar a este panel."""
        if self.state.tiene_mueble:
            self.lbl_sin_mueble.setVisible(False)
            self.frame_contenido.setVisible(True)
            self._verificar_sobrantes_disponibles()
        else:
            self.lbl_sin_mueble.setVisible(True)
            self.frame_contenido.setVisible(False)

    def _verificar_sobrantes_disponibles(self) -> None:
        """Consulta la DB y habilita/deshabilita el botón de sobrantes con badge."""
        try:
            from sobrantes_db import listar_disponibles
            disponibles = listar_disponibles()
            n = len(disponibles)
        except Exception:
            n = 0

        if n > 0:
            self.btn_sobrantes.setEnabled(True)
            self.btn_sobrantes.setText(
                f"{LABELS['nesting_sobrantes_btn']}  ({n} disponible{'s' if n != 1 else ''})"
            )
            self.btn_sobrantes.setToolTip(
                f"{n} sobrante{'s' if n != 1 else ''} disponible{'s' if n != 1 else ''} "
                f"que pueden reutilizarse antes del cálculo"
            )
        else:
            self.btn_sobrantes.setEnabled(False)
            self.btn_sobrantes.setText(LABELS["nesting_sobrantes_btn"])
            self.btn_sobrantes.setToolTip(LABELS["nesting_sobrantes_tip"])

    def _abrir_sobrantes(self) -> None:
        """Ejecuta el flujo de sugerencia de sobrantes en la sesión actual."""
        if not self.state.tiene_mueble:
            return
        orden_label = f"preview_manual"
        try:
            from gui.sobrantes_flow import sugerir_sobrantes_gui
            piezas, asignaciones = sugerir_sobrantes_gui(
                list(self.state.piezas),
                self.spin_mecha.value(),
                orden_label,
                parent=self,
            )
            self.state.asignaciones_sobrantes = asignaciones
            n = len(asignaciones)
            if n > 0:
                self.lbl_sobrantes_estado.setText(
                    f"{n} pieza{'s asignadas' if n != 1 else ' asignada'} a sobrantes "
                    f"— se excluirán del nesting automatico"
                )
                self.lbl_sobrantes_estado.setVisible(True)
            else:
                self.lbl_sobrantes_estado.setVisible(False)
        except Exception as e:
            self.state.asignaciones_sobrantes = []
            self.lbl_sobrantes_estado.setVisible(False)

    # ── Slots ─────────────────────────────────────────────────────────────

    def _calcular(self) -> None:
        if not self.state.tiene_mueble:
            return

        # Usar piezas filtradas si se asignaron sobrantes manualmente
        asig = getattr(self.state, "asignaciones_sobrantes", [])
        if asig:
            nombres_asig = {a["pieza_nombre"] for a in asig}
            piezas = [p for p in self.state.piezas if p.nombre not in nombres_asig]
        else:
            piezas = list(self.state.piezas)

        # Guardar parámetros en state
        self.state.placa_ancho  = self.spin_placa_ancho.value()
        self.state.placa_alto   = self.spin_placa_alto.value()
        self.state.margen_corte = self.spin_mecha.value()
        self.state.max_placas   = int(self.spin_max_placas.value())

        # Paso 2: nesting en worker thread
        self.btn_calcular.setEnabled(False)
        self.btn_calcular.setText(LABELS["nesting_calculando"])
        self.canvas.draw_empty("Calculando nesting…")

        self._worker = _NestingWorker(
            piezas=piezas,
            placa_ancho=self.state.placa_ancho,
            placa_alto=self.state.placa_alto,
            margen_corte=self.state.margen_corte,
            max_placas=self.state.max_placas,
        )
        self._worker.terminado.connect(self._on_nesting_terminado)
        self._worker.error.connect(self._on_nesting_error)
        self._worker.start()

    @pyqtSlot(object)
    def _on_nesting_terminado(self, resultado) -> None:
        self.state.resultado_nesting  = resultado
        self.state.placa_actual_idx   = 0

        self.btn_calcular.setEnabled(True)
        self.btn_calcular.setText(LABELS["nesting_calcular"])

        # Estadísticas
        self.lbl_placas._lbl_valor.setText(str(resultado.num_placas))
        self.lbl_eficiencia._lbl_valor.setText(f"{resultado.eficiencia_promedio:.1f}%")
        self.lbl_colocadas._lbl_valor.setText(str(resultado.total_piezas_colocadas))

        no_col = len(resultado.piezas_no_colocadas)
        self.lbl_no_colocadas._lbl_valor.setText(str(no_col))
        color_nc = COLORES["error"] if no_col > 0 else COLORES["exito"]
        self.lbl_no_colocadas._lbl_valor.setStyleSheet(
            f"color: {color_nc}; font-size: 18pt; font-weight: bold;"
        )

        self.grp_resultado.setVisible(True)
        self._actualizar_canvas()
        self.nesting_calculado.emit()

    @pyqtSlot(str)
    def _on_nesting_error(self, msg: str) -> None:
        self.btn_calcular.setEnabled(True)
        self.btn_calcular.setText(LABELS["nesting_calcular"])
        self.canvas.draw_empty(f"Error en nesting:\n{msg[:200]}")

    def _placa_anterior(self) -> None:
        if self.state.placa_actual_idx > 0:
            self.state.placa_actual_idx -= 1
            self._actualizar_canvas()

    def _placa_siguiente(self) -> None:
        if (self.state.tiene_nesting and
                self.state.placa_actual_idx < self.state.resultado_nesting.num_placas - 1):
            self.state.placa_actual_idx += 1
            self._actualizar_canvas()

    def _actualizar_canvas(self) -> None:
        if not self.state.tiene_nesting:
            return
        resultado = self.state.resultado_nesting
        idx   = self.state.placa_actual_idx
        placa = resultado.placas[idx]

        self.canvas.draw_placa(placa)

        self.lbl_placa_info.setText(
            f"Placa  {idx + 1}  de  {resultado.num_placas}"
        )
        self.btn_anterior.setEnabled(idx > 0)
        self.btn_siguiente.setEnabled(idx < resultado.num_placas - 1)
