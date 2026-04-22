"""
nesting_canvas.py — Widget matplotlib para visualizar placas nesteadas
Estilo CAD: rectángulos nítidos, grid milimetrado, tipografía mono para dimensiones.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

from gui.config import COLORES, FUENTES


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

_GRID_STEP_TENUE  = 100   # mm
_GRID_STEP_FUERTE = 500   # mm


def _color_pieza(nombre: str) -> str:
    return _COLORES_PIEZA.get(nombre.split("_")[0], COLORES["pieza_default"])


def _hex_to_01(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))  # type: ignore


class NestingCanvas(QWidget):
    """Canvas matplotlib con estilo CAD (rectángulos + grid milimetrado)."""

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
        self.ax.cla()
        self._style_axes()

        w, h = placa.ancho, placa.alto
        mono = [FUENTES["familia_mono"], FUENTES["familia_mono_fallback"]]

        self._draw_grid(w, h)

        # Contorno de la placa (sin relleno, sólo borde amber)
        self.ax.add_patch(mpatches.Rectangle(
            (0, 0), w, h,
            linewidth=1.5,
            edgecolor=_hex_to_01(COLORES["canvas_placa_borde"]),
            facecolor=_hex_to_01(COLORES["canvas_placa_fondo"]),
            zorder=1,
        ))

        piezas_vistas: dict[str, str] = {}

        for pieza, x, y, rotada in placa.piezas:
            pw = pieza.alto if rotada else pieza.ancho
            ph = pieza.ancho if rotada else pieza.alto
            color_hex = _color_pieza(pieza.nombre)
            color_rgb = _hex_to_01(color_hex)
            piezas_vistas[pieza.nombre.split("_")[0]] = color_hex

            self.ax.add_patch(mpatches.Rectangle(
                (x, y), pw, ph,
                linewidth=0.9,
                edgecolor=(0, 0, 0, 0.75),
                facecolor=(*color_rgb, 0.88),
                zorder=2,
            ))

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
                color=_hex_to_01(COLORES.get("texto_pieza", "#0E0E0E")),
                fontweight="bold",
                zorder=3,
                clip_on=True,
            )

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

        if piezas_vistas:
            handles = [
                mpatches.Patch(facecolor=_hex_to_01(c), label=nombre,
                               edgecolor="black", linewidth=0.5)
                for nombre, c in piezas_vistas.items()
            ]
            leg = self.ax.legend(
                handles=handles,
                loc="upper right",
                fontsize=7,
                framealpha=0.5,
                facecolor=COLORES["canvas_placa_fondo"],
                edgecolor=COLORES["borde"],
            )
            for text in leg.get_texts():
                text.set_color(COLORES["texto_primario"])

        self.ax.set_xlim(-30, w + 30)
        self.ax.set_ylim(-30, h + 30)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlabel("X [mm]", color=COLORES["texto_secundario"],
                           fontsize=8, fontfamily=mono)
        self.ax.set_ylabel("Y [mm]", color=COLORES["texto_secundario"],
                           fontsize=8, fontfamily=mono)
        self.ax.set_title(
            f"PLACA  {w:.0f} × {h:.0f} mm   │   {placa.num_piezas} piezas   │   "
            f"{placa.eficiencia:.1f}% eficiencia",
            color=COLORES["texto_primario"],
            fontsize=9, pad=6, fontfamily=mono,
        )
        for tl in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            tl.set_fontfamily(mono)
        self.canvas.draw()

    def draw_empty(self, mensaje: str = "Sin datos de nesting") -> None:
        self._draw_empty(mensaje)

    # ── Internos ──────────────────────────────────────────────────────────

    def _draw_grid(self, w: float, h: float) -> None:
        """Grid técnico estilo CAD: líneas tenues cada 100mm, fuertes cada 500mm."""
        tenue  = _hex_to_01(COLORES["canvas_grid_tenue"])
        fuerte = _hex_to_01(COLORES["canvas_grid_fuerte"])

        x = 0
        while x <= w + 1:
            col = fuerte if int(x) % _GRID_STEP_FUERTE == 0 else tenue
            lw  = 0.5  if int(x) % _GRID_STEP_FUERTE == 0 else 0.3
            self.ax.plot([x, x], [0, h], color=col, linewidth=lw, zorder=0)
            x += _GRID_STEP_TENUE

        y = 0
        while y <= h + 1:
            col = fuerte if int(y) % _GRID_STEP_FUERTE == 0 else tenue
            lw  = 0.5  if int(y) % _GRID_STEP_FUERTE == 0 else 0.3
            self.ax.plot([0, w], [y, y], color=col, linewidth=lw, zorder=0)
            y += _GRID_STEP_TENUE

    def _style_axes(self) -> None:
        bg = _hex_to_01(COLORES["canvas_fondo"])
        self.ax.set_facecolor(bg)
        self.ax.tick_params(colors=COLORES["texto_secundario"], labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color(COLORES["borde"])
            spine.set_linewidth(0.6)

    def _draw_empty(self, mensaje: str = "Sin datos de nesting") -> None:
        self.ax.cla()
        self._style_axes()
        self.ax.text(
            0.5, 0.5, mensaje,
            transform=self.ax.transAxes,
            ha="center", va="center",
            fontsize=11,
            fontfamily=[FUENTES["familia_mono"], FUENTES["familia_mono_fallback"]],
            color=COLORES["texto_desactivado"],
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
