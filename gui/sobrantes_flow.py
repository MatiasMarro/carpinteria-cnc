"""
sobrantes_flow.py — Versión GUI del flujo interactivo de sobrantes
===================================================================
Reemplaza la función `sugerir_uso_sobrantes` del CLI mostrando
un QDialog en lugar de usar input().
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


def sugerir_sobrantes_gui(
    piezas: list,
    margen_corte: float,
    orden_label: str,
    parent: "QWidget | None" = None,
) -> tuple[list, list[dict]]:
    """
    Para cada pieza busca sobrantes disponibles en DB y muestra un diálogo
    al usuario. Devuelve las piezas que siguen al nesting y las asignaciones.

    Args:
        piezas:        list[Pieza] a procesar
        margen_corte:  mm de mecha
        orden_label:   ID de la orden (para registrar el sobrante como usado)
        parent:        widget padre del diálogo (para centrarlo correctamente)

    Returns:
        (piezas_restantes, asignaciones)
    """
    from sobrantes_db import init_db, marcar_usado, marcar_descartado
    from sobrantes_matcher import buscar_sobrante_para_pieza
    from gui.dialogo_sobrante import DialogoSobrante

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
            dialog = DialogoSobrante(pieza, m, parent=parent)
            dialog.exec()
            respuesta = dialog.respuesta

            if respuesta == "u":
                marcar_usado(m.sobrante.id, orden_label)
                qty -= 1
                asignaciones.append({
                    "pieza_nombre": pieza.nombre,
                    "pieza_ancho":  pieza.ancho,
                    "pieza_alto":   pieza.alto,
                    "sobrante_id":  m.sobrante.id,
                    "pos_x":        m.pos_x,
                    "pos_y":        m.pos_y,
                    "rotada":       m.rotada,
                })
            elif respuesta == "d":
                marcar_descartado(m.sobrante.id)
            else:
                # saltar: no usar sobrantes para esta pieza
                break

        if qty > 0:
            piezas_restantes.append(replace(pieza, cantidad=qty))

    return piezas_restantes, asignaciones
