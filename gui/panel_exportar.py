"""
panel_exportar.py — Panel de exportación DXF con barra de progreso
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QLineEdit, QCheckBox,
    QProgressBar, QTextEdit, QFrame, QFileDialog,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from gui.config import COLORES, LABELS
from gui.state import AppState


# ===========================================================================
# Worker thread — exporta DXF sin bloquear la UI
# ===========================================================================

class _ExportWorker(QThread):
    progreso  = pyqtSignal(int, str)   # (porcentaje, mensaje)
    terminado = pyqtSignal(str)        # ruta del proyecto
    error     = pyqtSignal(str)

    def __init__(self, state: AppState, output_dir: str, registrar: bool) -> None:
        super().__init__()
        self.state      = state
        self.output_dir = output_dir
        self.registrar  = registrar

    def run(self) -> None:
        try:
            from dxf_exporter import exportar_placa
            from sobrantes_registrar import registrar_sobrantes_de_resultado

            resultado  = self.state.resultado_nesting
            nombre     = self.state.nombre_mueble
            ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
            proyecto_id = f"P_{ts}_{nombre}"

            out = Path(self.output_dir) / proyecto_id
            out.mkdir(parents=True, exist_ok=True)

            total_steps = resultado.num_placas + 2
            step = 0

            for placa in resultado.placas:
                step += 1
                pct = int(step / total_steps * 88)
                fname = f"placa_{placa.numero}_de_{resultado.num_placas}.dxf"
                self.progreso.emit(pct, f"Exportando {fname}…")

                exportar_placa(
                    piezas_con_posicion=placa.piezas,
                    path=str(out / fname),
                    placa_ancho=placa.ancho,
                    placa_alto=placa.alto,
                    dibujar_contorno_placa=True,
                )

            # Manifest
            self.progreso.emit(90, "Generando manifest.txt…")
            manifest_txt = self._generar_manifest(resultado, proyecto_id)
            (out / "manifest.txt").write_text(manifest_txt, encoding="utf-8")

            # Sobrantes
            if self.registrar:
                self.progreso.emit(96, "Registrando sobrantes en DB…")
                registrar_sobrantes_de_resultado(resultado, proyecto_id)

            self.progreso.emit(100, LABELS["exportar_exito"])
            self.terminado.emit(str(out))

        except Exception:
            import traceback
            self.error.emit(traceback.format_exc())

    def _generar_manifest(self, resultado, proyecto_id: str) -> str:
        mueble = self.state.mueble
        lineas = [
            f"PROYECTO: {self.state.nombre_mueble}",
            f"ID:       {proyecto_id}",
            f"FECHA:    {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"MUEBLE:   {mueble}",
            "",
            f"PLACA:    {self.state.placa_ancho:.0f} × {self.state.placa_alto:.0f} mm",
            f"MECHA:    {self.state.margen_corte:.0f} mm  (margen entre piezas)",
            f"PLACAS NECESARIAS: {resultado.num_placas}",
            f"EFICIENCIA:        {resultado.eficiencia_promedio:.1f}%",
            "",
            "INSTRUCCIONES PARA ASPIRE:",
            "  1. File > Open Vector File > seleccionar placa_X.dxf",
            "  2. Configurar material y dimensiones de placa",
            "  3. Layers importados:",
            "     - CONTORNO  (rojo)    → mecha de contorno exterior",
            "     - MINIFIX_15 (amarillo)→ agujeros minifix 15mm",
            "     - TARUGO_8  (verde)   → agujeros tarugo 8mm",
            "     - MECHA_4   (cian)    → agujeros pequeños 4mm",
            "  4. Generar toolpaths por layer",
            "  5. Exportar G-code y cargar en Mach3",
        ]

        asig = self.state.asignaciones_sobrantes
        if asig:
            lineas.append("")
            lineas.append("PIEZAS ASIGNADAS A SOBRANTES (cortar manualmente):")
            for a in asig:
                rot = "  [rotada 90°]" if a["rotada"] else ""
                lineas.append(
                    f"  - {a['pieza_nombre']}  "
                    f"({a['pieza_ancho']:.0f}×{a['pieza_alto']:.0f}mm)  "
                    f"→ sobrante #{a['sobrante_id']}  "
                    f"en ({a['pos_x']:.0f}, {a['pos_y']:.0f}){rot}"
                )

        if resultado.piezas_no_colocadas:
            lineas.append("")
            lineas.append("⚠  PIEZAS NO COLOCADAS (placa insuficiente):")
            for p in resultado.piezas_no_colocadas:
                lineas.append(f"  - {p.nombre}  ({p.ancho:.0f}×{p.alto:.0f}mm)")

        return "\n".join(lineas)


# ===========================================================================
# Panel principal
# ===========================================================================

class PanelExportar(QWidget):
    """Panel 4 — Opciones de exportación y visualización del manifest."""

    def __init__(self, state: AppState, parent=None) -> None:
        super().__init__(parent)
        self.state = state
        self._worker: _ExportWorker | None = None
        self._build_ui()

    # ── Construcción ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 20)
        layout.setSpacing(18)

        layout.addWidget(self._header())

        # Aviso "sin nesting"
        self.lbl_sin_nesting = QLabel(LABELS["exportar_sin_nesting"])
        self.lbl_sin_nesting.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_nesting.setStyleSheet(
            f"color: {COLORES['advertencia']}; padding: 20px;"
        )
        layout.addWidget(self.lbl_sin_nesting)

        # Contenido principal
        self.frame_contenido = QFrame()
        self.frame_contenido.setVisible(False)
        contenido = QVBoxLayout(self.frame_contenido)
        contenido.setContentsMargins(0, 0, 0, 0)
        contenido.setSpacing(16)
        layout.addWidget(self.frame_contenido)

        # ── Opciones ──────────────────────────────────────────────────────
        grp_opciones = QGroupBox("Opciones de exportación")
        opc_layout = QVBoxLayout(grp_opciones)
        opc_layout.setSpacing(12)

        # Carpeta de salida
        carpeta_row = QHBoxLayout()
        lbl_carpeta = QLabel(LABELS["exportar_carpeta"])
        lbl_carpeta.setFixedWidth(140)
        lbl_carpeta.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.txt_carpeta = QLineEdit()
        default_out = str(Path(__file__).resolve().parent.parent / "output")
        self.txt_carpeta.setText(default_out)
        btn_explorar = QPushButton(LABELS["exportar_explorar"])
        btn_explorar.setFixedWidth(110)
        btn_explorar.clicked.connect(self._explorar_carpeta)
        carpeta_row.addWidget(lbl_carpeta)
        carpeta_row.addWidget(self.txt_carpeta, stretch=1)
        carpeta_row.addWidget(btn_explorar)
        opc_layout.addLayout(carpeta_row)

        self.chk_registrar = QCheckBox(LABELS["exportar_registrar"])
        self.chk_registrar.setChecked(True)
        opc_layout.addWidget(self.chk_registrar)

        contenido.addWidget(grp_opciones)

        # ── Resumen rápido del nesting ────────────────────────────────────
        self.lbl_resumen_nesting = QLabel()
        self.lbl_resumen_nesting.setStyleSheet(
            f"color: {COLORES['texto_secundario']}; padding: 4px 0px;"
        )
        contenido.addWidget(self.lbl_resumen_nesting)

        # ── Botón exportar + progreso ─────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_exportar = QPushButton(LABELS["exportar_boton"])
        self.btn_exportar.setFixedHeight(44)
        self.btn_exportar.setMinimumWidth(200)
        self.btn_exportar.clicked.connect(self._exportar)
        btn_row.addWidget(self.btn_exportar)
        contenido.addLayout(btn_row)

        self.lbl_estado = QLabel()
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setVisible(False)
        contenido.addWidget(self.lbl_estado)

        self.barra = QProgressBar()
        self.barra.setVisible(False)
        self.barra.setFixedHeight(20)
        contenido.addWidget(self.barra)

        # Botón abrir carpeta (post-exportación)
        self.btn_abrir = QPushButton(LABELS['exportar_abrir_carpeta'])
        self.btn_abrir.setVisible(False)
        self.btn_abrir.setFixedWidth(190)
        btn_abrir_row = QHBoxLayout()
        btn_abrir_row.addStretch()
        btn_abrir_row.addWidget(self.btn_abrir)
        contenido.addLayout(btn_abrir_row)

        # ── Vista previa del manifest ─────────────────────────────────────
        grp_manifest = QGroupBox(LABELS["exportar_manifest"])
        man_layout = QVBoxLayout(grp_manifest)
        self.txt_manifest = QTextEdit()
        self.txt_manifest.setReadOnly(True)
        self.txt_manifest.setPlaceholderText(
            "El manifest aparecerá aquí después de exportar."
        )
        self.txt_manifest.setMinimumHeight(160)
        man_layout.addWidget(self.txt_manifest)
        contenido.addWidget(grp_manifest, stretch=1)

        layout.addStretch()

    def _header(self) -> QFrame:
        frame = QFrame()
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)
        lbl_t = QLabel(LABELS["exportar_titulo"])
        lbl_t.setStyleSheet(
            f"color: {COLORES['acento_naranja']}; font-size: 14pt; font-weight: bold;"
        )
        lbl_s = QLabel(
            "Generá los archivos DXF por placa y el manifest para el operador CNC."
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

    def actualizar_estado(self) -> None:
        if self.state.tiene_nesting:
            self.lbl_sin_nesting.setVisible(False)
            self.frame_contenido.setVisible(True)
            r = self.state.resultado_nesting
            self.lbl_resumen_nesting.setText(
                f"Nesting listo:   {r.num_placas} placa(s)   /   "
                f"{r.total_piezas_colocadas} piezas   /   "
                f"{r.eficiencia_promedio:.1f}% eficiencia promedio"
            )
        else:
            self.lbl_sin_nesting.setVisible(True)
            self.frame_contenido.setVisible(False)

    # ── Slots ─────────────────────────────────────────────────────────────

    def _explorar_carpeta(self) -> None:
        carpeta = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de salida", self.txt_carpeta.text()
        )
        if carpeta:
            self.txt_carpeta.setText(carpeta)

    def _exportar(self) -> None:
        if not self.state.tiene_nesting:
            return

        output_base = self.txt_carpeta.text().strip() or "output"

        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setText(LABELS["exportar_exportando"])
        self.barra.setValue(0)
        self.barra.setVisible(True)
        self.lbl_estado.setText("Iniciando exportación…")
        self.lbl_estado.setStyleSheet(f"color: {COLORES['texto_secundario']};")
        self.lbl_estado.setVisible(True)
        self.btn_abrir.setVisible(False)
        self.txt_manifest.clear()

        self._worker = _ExportWorker(
            state=self.state,
            output_dir=output_base,
            registrar=self.chk_registrar.isChecked(),
        )
        self._worker.progreso.connect(self._on_progreso)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    @pyqtSlot(int, str)
    def _on_progreso(self, pct: int, mensaje: str) -> None:
        self.barra.setValue(pct)
        self.lbl_estado.setText(mensaje)

    @pyqtSlot(str)
    def _on_terminado(self, ruta: str) -> None:
        self._ruta_exportada = ruta
        self.btn_exportar.setEnabled(True)
        self.btn_exportar.setText(LABELS["exportar_boton"])
        self.barra.setValue(100)
        self.lbl_estado.setText(f"  {LABELS['exportar_exito']}  →  {ruta}")
        self.lbl_estado.setStyleSheet(f"color: {COLORES['exito']};")

        # Mostrar manifest en el área de texto
        manifest_path = Path(ruta) / "manifest.txt"
        if manifest_path.exists():
            self.txt_manifest.setText(manifest_path.read_text(encoding="utf-8"))

        self.btn_abrir.setVisible(True)
        self.btn_abrir.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        )

    @pyqtSlot(str)
    def _on_error(self, msg: str) -> None:
        self.btn_exportar.setEnabled(True)
        self.btn_exportar.setText(LABELS["exportar_boton"])
        self.barra.setVisible(False)
        self.lbl_estado.setText(f"  Error durante la exportación")
        self.lbl_estado.setStyleSheet(f"color: {COLORES['error']};")
        self.txt_manifest.setText(f"ERROR:\n{msg}")
