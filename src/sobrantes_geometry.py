"""
sobrantes_geometry.py - Cálculo geométrico de sobrantes
========================================================
Dado el layout de una placa nesteada, calcula los polígonos de sobrantes
reales usando Shapely (operación difference entre placa y piezas ocupadas).

Convención de coordenadas del nesting_engine:
- Cada pieza ocupa un rectángulo (ancho + margen_corte, alto + margen_corte)
  con esquina inferior-izquierda en (x, y). La pieza real mide (ancho, alto).
- La mecha corta entre piezas dentro del margen_corte, por lo que el sobrante
  útil coincide con placa - union(rects_reservados). No hace falta buffer extra.
"""

from __future__ import annotations

from shapely import set_precision
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


AREA_MINIMA_MM2 = 10_000  # 100 cm² (10x10 cm) — menor que eso se descarta


def calcular_sobrantes(
    placa_ancho: float,
    placa_alto: float,
    piezas_colocadas: list,
    margen_corte: float = 4.0,
    area_minima_mm2: float = AREA_MINIMA_MM2,
) -> list[Polygon]:
    """
    Calcula polígonos de sobrantes de una placa nesteada.

    Args:
        placa_ancho: mm
        placa_alto: mm
        piezas_colocadas: [(pieza, x, y, rotada), ...] como retorna PlacaNesteada.piezas
        margen_corte: mm de la mecha (se usa para reconstruir el rect reservado)
        area_minima_mm2: filtra sobrantes más chicos (ruido, descartables)

    Returns:
        Lista de Polygon de Shapely, uno por cada región de sobrante utilizable.
    """
    placa = box(0, 0, placa_ancho, placa_alto)

    rects = []
    for pieza, x, y, rotada in piezas_colocadas:
        if rotada:
            w = pieza.alto + margen_corte
            h = pieza.ancho + margen_corte
        else:
            w = pieza.ancho + margen_corte
            h = pieza.alto + margen_corte
        rects.append(box(x, y, x + w, y + h))

    if not rects:
        return [placa] if placa.area >= area_minima_mm2 else []

    usado = unary_union(rects)
    sobrante = placa.difference(usado)

    if sobrante.is_empty:
        return []

    sobrante = set_precision(sobrante, 1.0)
    if not sobrante.is_valid:
        sobrante = sobrante.buffer(0)

    if sobrante.is_empty:
        return []

    geoms = [sobrante] if sobrante.geom_type == "Polygon" else list(sobrante.geoms)

    return [
        g for g in geoms
        if g.geom_type == "Polygon" and g.is_valid and g.area >= area_minima_mm2
    ]


def descontar_pieza_de_sobrante(
    sobrante: Polygon,
    pieza_ancho: float,
    pieza_alto: float,
    pos_x: float,
    pos_y: float,
    margen_corte: float = 4.0,
) -> Polygon:
    """
    Tras usar una pieza de un sobrante, retorna el polígono residual.
    La pieza se ubica en (pos_x, pos_y) relativa al origen del sobrante.
    """
    rect_pieza = box(
        pos_x, pos_y,
        pos_x + pieza_ancho + margen_corte,
        pos_y + pieza_alto + margen_corte,
    )
    residual = sobrante.difference(rect_pieza)
    residual = set_precision(residual, 1.0)
    if not residual.is_valid:
        residual = residual.buffer(0)
    return residual
