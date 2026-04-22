"""
sobrantes_matcher.py - Match de piezas rectangulares contra sobrantes poligonales
==================================================================================
Dada una pieza, busca en qué sobrante disponible puede ubicarse (considerando
rotaciones y margen de mecha). Usa grid-sweep con early exit + bounding-box
pre-filter para mantener la búsqueda barata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from shapely.geometry import Polygon, box

from sobrantes_db import Sobrante, listar_disponibles


PASO_BUSQUEDA_MM = 20  # grilla de búsqueda de posición; 20mm = balance velocidad/precisión


@dataclass
class MatchSobrante:
    sobrante: Sobrante
    pos_x: float
    pos_y: float
    rotada: bool
    desperdicio_mm2: float  # area sobrante - area pieza (menor = mejor ajuste)


def _buscar_posicion(
    poly: Polygon,
    pieza_w: float,
    pieza_h: float,
    margen: float,
    paso: float = PASO_BUSQUEDA_MM,
) -> Optional[tuple[float, float]]:
    """Intenta ubicar la pieza (con margen) dentro del polígono.

    Retorna (x, y) de la esquina inf-izq del rect pieza+margen, o None.
    """
    w = pieza_w + margen
    h = pieza_h + margen
    minx, miny, maxx, maxy = poly.bounds

    if (maxx - minx) < w or (maxy - miny) < h:
        return None

    x = minx
    while x + w <= maxx + 1e-6:
        y = miny
        while y + h <= maxy + 1e-6:
            candidato = box(x, y, x + w, y + h)
            if poly.contains(candidato):
                return (x, y)
            y += paso
        x += paso

    return None


def buscar_sobrante_para_pieza(
    pieza,
    margen_corte: float = 4.0,
) -> list[MatchSobrante]:
    """
    Busca todos los sobrantes disponibles donde esta pieza entra.

    Args:
        pieza: objeto Pieza (con .ancho, .alto, .material, .permitir_rotacion)
        margen_corte: mm de la mecha

    Returns:
        Lista de MatchSobrante ordenada por mejor ajuste (menor desperdicio).
    """
    disponibles = listar_disponibles(
        material_nombre=pieza.material.nombre,
        material_espesor=pieza.material.espesor,
    )

    matches: list[MatchSobrante] = []

    for s in disponibles:
        poly = s.to_polygon()

        pos = _buscar_posicion(poly, pieza.ancho, pieza.alto, margen_corte)
        if pos is not None:
            matches.append(MatchSobrante(
                sobrante=s,
                pos_x=pos[0],
                pos_y=pos[1],
                rotada=False,
                desperdicio_mm2=s.area_mm2 - pieza.area,
            ))
            continue

        if pieza.permitir_rotacion:
            pos = _buscar_posicion(poly, pieza.alto, pieza.ancho, margen_corte)
            if pos is not None:
                matches.append(MatchSobrante(
                    sobrante=s,
                    pos_x=pos[0],
                    pos_y=pos[1],
                    rotada=True,
                    desperdicio_mm2=s.area_mm2 - pieza.area,
                ))

    matches.sort(key=lambda m: m.desperdicio_mm2)
    return matches


def buscar_sobrantes_para_piezas(
    piezas: list,
    margen_corte: float = 4.0,
) -> dict:
    """
    Para cada pieza de la lista, encuentra el mejor sobrante disponible.
    Al asignar un sobrante a una pieza, ese sobrante no se reutiliza para
    las siguientes (así evitamos dobles sugerencias en la misma orden).

    Returns:
        dict {pieza_idx: MatchSobrante} con solo las piezas que matchearon.
    """
    asignaciones: dict[int, MatchSobrante] = {}
    usados: set[int] = set()

    for i, pieza in enumerate(piezas):
        matches = buscar_sobrante_para_pieza(pieza, margen_corte)
        for m in matches:
            if m.sobrante.id not in usados:
                asignaciones[i] = m
                usados.add(m.sobrante.id)
                break

    return asignaciones
