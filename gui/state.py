"""
state.py — Estado compartido entre todos los paneles de la aplicación
"""
from __future__ import annotations


class AppState:
    """
    Objeto singleton-like de estado. Se instancia una sola vez en MainWindow
    y se pasa a cada panel como referencia.
    """

    def __init__(self) -> None:
        # ── Mueble ────────────────────────────────────────────────────────
        self.mueble = None           # Objeto Escritorio | Estanteria
        self.nombre_mueble: str = "" # Ej: "escritorio_estandar"
        self.piezas: list = []       # list[Pieza] generadas

        # ── Nesting ───────────────────────────────────────────────────────
        self.resultado_nesting = None   # ResultadoNesting
        self.placa_ancho: float = 1830.0
        self.placa_alto: float  = 2750.0
        self.margen_corte: float = 4.0
        self.max_placas: int = 10
        self.placa_actual_idx: int = 0  # placa visible en el canvas

        # ── Sobrantes ─────────────────────────────────────────────────────
        self.asignaciones_sobrantes: list[dict] = []

    # ── Propiedades de conveniencia ───────────────────────────────────────

    @property
    def tiene_mueble(self) -> bool:
        return self.mueble is not None and len(self.piezas) > 0

    @property
    def tiene_nesting(self) -> bool:
        return self.resultado_nesting is not None

    def reset_nesting(self) -> None:
        self.resultado_nesting = None
        self.placa_actual_idx = 0
        self.asignaciones_sobrantes = []
