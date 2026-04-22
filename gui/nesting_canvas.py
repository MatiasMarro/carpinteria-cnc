"""
nesting_canvas.py — Widget matplotlib para visualizar placas nesteadas
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

from gui.config import COLORES


# Mapeo prefijo-nombre → color de relleno de pieza en canvas
_COLORES_PIEZA: dict[str, str] = {
    "tapa":       COLORES["pieza_tapa"],
    "lateral":    COLORES["pieza_lateral"],
    "espaldar":   COLORES["pieza_espaldar"],
    "estante":    COLORES["pieza_estante"],
    "cajon":      COLORES["pieza_cajon"],
    "travesano":  COLORES["pieza_travesano"],
    "fondo":      COLORES["pieza_fondo"],
    "frente":     COLORES["pieza_frente"],
}


def _color_pieza(nombre: str) -> str:
    prefijo = nombre.split("_")[0]
    return _COLORES_PIEZA.get(prefijo, COLORES["pieza_default"])


def _hex_to_01(h: str) -> tuple[float, float, float]:
    """Convierte hex '#RRGGBB' a tupla (r,g,b) 0-1 para matplotlib."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))  # type: ignore


class NestingCanvas(QWidget):
    """
    Widget que embebe un canvas de matplotlib y dibuja una PlacaNesteada
    con rectángulos coloreados por tipo de pieza y círculos para agujeros.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.fig = Figure(figsize=(6, 8), tight_layout=True)
        self.fig.set_facecolor(COLORES["canvas_fondo"])
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setMinimumHeight(350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self._draw_empty()

    # ── API pública ───────────────────────────────────────────────────────

    def draw_placa(self, placa) -> None:
        """Dibuja la placa nesteada completa con piezas y agujeros."""
        self.ax.cla()
        self._style_axes()

        w, h = placa.ancho, placa.alto

        # Fondo de la placa
        self.ax.add_patch(mpatches.Rectangle(
            (0, 0), w, h,
            linewidth=2,
            edgecolor=_hex_to_01(COLORES["canvas_placa_borde"]),
            facecolor=_hex_to_01(COLORES["canvas_placa_fondo"]),
            zorder=1,
        ))

        piezas_vistas: dict[str, str] = {}  # nombre → color (para leyenda)

        for pieza, x, y, rotada in placa.piezas:
            pw = pieza.alto if rotada else pieza.ancho
            ph = pieza.ancho if rotada else pieza.alto
            color_hex = _color_pieza(pieza.nombre)
            color_rgb = _hex_to_01(color_hex)
            piezas_vistas[pieza.nombre.split("_")[0]] = color_hex

            # Rectángulo de la pieza
            self.ax.add_patch(mpatches.FancyBboxPatch(
                (x, y), pw, ph,
                boxstyle="round,pad=1",
                linewidth=0.8,
                edgecolor=(0, 0, 0, 0.6),
                facecolor=(*color_rgb, 0.88),
                zorder=2,
            ))

            # Etiqueta centrada
            label = pieza.nombre
            if len(label) > 12:
                label = label[:11] + "…"
            if rotada:
                label += " ↺"
            self.ax.text(
                x + pw / 2, y + ph / 2,
                label,
                ha="center", va="center",
                fontsize=6.5,
                color=_hex_to_01(COLORES["texto_pieza"] if "texto_pieza" in COLORES else "#1E1E2E"),
                fontweight="bold",
                zorder=3,
                clip_on=True,
            )

            # Agujeros
            for op in pieza.operaciones:
                ox, oy = op.posicion
                if rotada:
                    ox_f = x + oy
                    oy_f = y + pieza.ancho - ox
                else:
                    ox_f = x + ox
                    oy_f = y + oy

                d = op.parametros.get("diametro", 8)
                if d >= 14:
                    hole_color = _hex_to_01(COLORES["agujero_minifix"])
                    r = 15 / 2
                elif d >= 6:
                    hole_color = _hex_to_01(COLORES["agujero_tarugo"])
                    r = 8 / 2
                else:
                    hole_color = _hex_to_01(COLORES["agujero_mecha4"])
                    r = 4 / 2

                self.ax.add_patch(mpatches.Circle(
                    (ox_f, oy_f), r,
                    linewidth=0.6,
                    edgecolor=(0, 0, 0, 0.7),
                    facecolor=(*hole_color, 0.9),
                    zorder=4,
                ))

        # Leyenda compacta de tipos de pieza
        legend_handles = [
            mpatches.Patch(facecolor=_hex_to_01(c), label=nombre, edgecolor="black", linewidth=0.5)
            for nombre, c in piezas_vistas.items()
        ]
        if legend_handles:
            leg = self.ax.legend(
                handles=legend_handles,
                loc="upper right",
                fontsize=7,
                framealpha=0.4,
                facecolor=COLORES["fondo_input"],
                labelcolor=COLORES["texto_primario"],
                edgecolor=COLORES["borde"],
            )
            for text in leg.get_texts():
                text.set_color(COLORES["texto_primario"])

        self.ax.set_xlim(-30, w + 30)
        self.ax.set_ylim(-30, h + 30)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlabel("X (mm)", color=COLORES["texto_secundario"], fontsize=8)
        self.ax.set_ylabel("Y (mm)", color=COLORES["texto_secundario"], fontsize=8)
        self.ax.set_title(
            f"Placa  {w:.0f} × {h:.0f} mm — {placa.num_piezas} piezas — "
            f"{placa.eficiencia:.1f}% eficiencia",
            color=COLORES["texto_primario"],
            fontsize=9,
            pad=6,
        )
        self.canvas.draw()

    def draw_empty(self, mensaje: str = "Sin datos de nesting") -> None:
        self._draw_empty(mensaje)

    # ── Internos ──────────────────────────────────────────────────────────

    def _style_axes(self) -> None:
        bg = _hex_to_01(COLORES["canvas_fondo"])
        self.ax.set_facecolor(bg)
        self.ax.tick_params(colors=COLORES["texto_secundario"], labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color(COLORES["borde"])

    def _draw_empty(self, mensaje: str = "Sin datos de nesting") -> None:
        self.ax.cla()
        self._style_axes()
        self.ax.text(
            0.5, 0.5, mensaje,
            transform=self.ax.transAxes,
            ha="center", va="center",
            fontsize=11,
            color=COLORES["texto_desactivado"],
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
