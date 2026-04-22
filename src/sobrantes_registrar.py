"""
sobrantes_registrar.py - Coordina cálculo + persistencia + sugerencia de sobrantes
===================================================================================
- registrar_sobrantes_de_resultado: tras nesting, guarda polígonos como 'disponible'.
- sugerir_uso_sobrantes: flujo interactivo antes del nesting para usar stock previo.
"""

from __future__ import annotations

from dataclasses import replace

from sobrantes_db import Sobrante, init_db, insert, marcar_usado, marcar_descartado
from sobrantes_geometry import calcular_sobrantes
from sobrantes_matcher import buscar_sobrante_para_pieza


def registrar_sobrantes_de_resultado(
    resultado,
    orden_label: str,
    notas: str = "",
) -> list[int]:
    """
    Inserta los sobrantes de todas las placas del resultado.

    Args:
        resultado: ResultadoNesting (con .placas y .margen_corte)
        orden_label: identificador de la orden ("P_20260422_143530_escritorio_estandar")
        notas: texto libre opcional

    Returns:
        IDs de los sobrantes insertados.
    """
    init_db()
    ids: list[int] = []

    for placa in resultado.placas:
        if not placa.piezas:
            continue

        material = placa.piezas[0][0].material

        polys = calcular_sobrantes(
            placa_ancho=placa.ancho,
            placa_alto=placa.alto,
            piezas_colocadas=placa.piezas,
            margen_corte=resultado.margen_corte,
        )

        for poly in polys:
            sobrante = Sobrante.from_polygon(
                poly=poly,
                material_nombre=material.nombre,
                material_espesor=material.espesor,
                origen_orden=orden_label,
                origen_placa=placa.numero,
                notas=notas or None,
            )
            ids.append(insert(sobrante))

    return ids


def sugerir_uso_sobrantes(
    piezas: list,
    margen_corte: float,
    orden_label: str,
    input_fn=input,
) -> tuple[list, list[dict]]:
    """
    Busca en DB sobrantes que sirvan para las piezas. Por cada match pregunta
    interactivamente al usuario si usar / descartar / saltar.

    Args:
        piezas: lista de Pieza (se consume .cantidad)
        margen_corte: mm de mecha
        orden_label: para marcar sobrantes como usados en esta orden
        input_fn: inyectable para tests

    Returns:
        (piezas_restantes, asignaciones)
        - piezas_restantes: lista ajustada (cantidades reducidas) para nesting
        - asignaciones: [{pieza_nombre, sobrante_id, pos_x, pos_y, rotada}, ...]
    """
    init_db()
    piezas_restantes: list = []
    asignaciones: list[dict] = []

    for pieza in piezas:
        qty = pieza.cantidad

        while qty > 0:
            matches = buscar_sobrante_para_pieza(pieza, margen_corte=margen_corte)
            if not matches:
                break

            m = matches[0]
            s = m.sobrante

            print()
            print(f"  [SOBRANTE DISPONIBLE] Pieza '{pieza.nombre}' ({pieza.ancho:.0f}x{pieza.alto:.0f}mm)")
            print(f"    Cabe en sobrante #{s.id}: bbox {s.ancho_bbox:.0f}x{s.alto_bbox:.0f}mm, area {s.area_mm2:.0f}mm2")
            print(f"    Origen: {s.origen_orden} (placa {s.origen_placa})")
            print(f"    Material: {s.material_nombre} {s.material_espesor:.0f}mm")
            print(f"    Posicion sugerida: ({m.pos_x:.0f}, {m.pos_y:.0f}){' ROTADA 90' if m.rotada else ''}")
            print(f"    --> Buscalo en el taller y chequealo.")

            respuesta = input_fn("    [u]sar / [d]escartar / [s]kip: ").strip().lower()

            if respuesta in ("u", "usar"):
                marcar_usado(s.id, orden_label)
                qty -= 1
                asignaciones.append({
                    "pieza_nombre": pieza.nombre,
                    "pieza_ancho": pieza.ancho,
                    "pieza_alto": pieza.alto,
                    "sobrante_id": s.id,
                    "pos_x": m.pos_x,
                    "pos_y": m.pos_y,
                    "rotada": m.rotada,
                })
                print(f"    OK. Usada 1 unidad del sobrante. Quedan {qty} unidad(es) de '{pieza.nombre}'.")
            elif respuesta in ("d", "descartar"):
                marcar_descartado(s.id)
                print(f"    Sobrante #{s.id} descartado permanentemente.")
            else:
                print(f"    Skip. El resto de '{pieza.nombre}' va a placa nueva.")
                break

        if qty > 0:
            piezas_restantes.append(replace(pieza, cantidad=qty))

    return piezas_restantes, asignaciones
