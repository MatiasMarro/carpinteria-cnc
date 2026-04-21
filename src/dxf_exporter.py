"""
dxf_exporter.py - V8.502 COMPATIBLE
====================================
Exporta DXFs que Aspire V8.502 puede leer sin problemas.

Cambios clave:
- Formato R2000 (AC1015) - máxima compatibilidad
- Solo LINE y CIRCLE (sin LWPOLYLINE con XDATA)
- Setup mínimo de headers
- Sin metadatos extendidos
"""

import os
from pathlib import Path
import ezdxf
from ezdxf import units


LAYERS_ASPIRE = {
    "CONTORNO": 1,
    "MINIFIX_15": 2,
    "TARUGO_8": 3,
    "MECHA_4": 4,
    "RANURA": 5,
    "GRABADO": 6,
}


def _crear_documento():
    """Crea documento DXF R2000 mínimo para Aspire V8"""
    doc = ezdxf.new("R2000")
    doc.units = units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LUNITS"] = 2
    
    msp = doc.modelspace()
    
    for layer_name, color in LAYERS_ASPIRE.items():
        if layer_name not in doc.layers:
            doc.layers.add(name=layer_name, color=color)
    
    return doc, msp


def _dibujar_rectangulo(msp, x0, y0, ancho, alto, layer="CONTORNO"):
    """Rectángulo con 4 LINEs separadas (compatible V8)"""
    puntos = [
        (x0, y0),
        (x0 + ancho, y0),
        (x0 + ancho, y0 + alto),
        (x0, y0 + alto),
    ]
    for i in range(4):
        msp.add_line(
            start=puntos[i],
            end=puntos[(i + 1) % 4],
            dxfattribs={"layer": layer}
        )


def _dibujar_circulo(msp, cx, cy, radio, layer):
    msp.add_circle(
        center=(cx, cy),
        radius=radio,
        dxfattribs={"layer": layer}
    )


def _dibujar_pieza_en_posicion(msp, pieza, offset_x, offset_y, rotada=False):
    """Dibuja pieza en (offset_x, offset_y), rotada opcionalmente 90°"""
    if rotada:
        ancho = pieza.alto
        alto = pieza.ancho
    else:
        ancho = pieza.ancho
        alto = pieza.alto
    
    _dibujar_rectangulo(msp, offset_x, offset_y, ancho, alto, layer="CONTORNO")
    
    for op in pieza.operaciones:
        x_orig, y_orig = op.posicion
        
        if rotada:
            x_final = offset_x + y_orig
            y_final = offset_y + pieza.ancho - x_orig
        else:
            x_final = offset_x + x_orig
            y_final = offset_y + y_orig
        
        diametro = op.parametros.get("diametro", 8)
        if diametro >= 14:
            layer = "MINIFIX_15"
            radio = 15 / 2
        elif diametro >= 6:
            layer = "TARUGO_8"
            radio = 8 / 2
        else:
            layer = "MECHA_4"
            radio = 4 / 2
        
        _dibujar_circulo(msp, x_final, y_final, radio, layer)


def exportar_pieza_simple(pieza, path: str):
    """Exporta UNA pieza (sin nesting)"""
    doc, msp = _crear_documento()
    _dibujar_pieza_en_posicion(msp, pieza, 0, 0, rotada=False)
    
    os.makedirs(Path(path).parent, exist_ok=True)
    doc.saveas(path)


def exportar_placa(piezas_con_posicion, path: str, 
                   placa_ancho: float, placa_alto: float,
                   dibujar_contorno_placa: bool = True):
    """
    Exporta placa completa con varias piezas ya nesteadas.
    
    Args:
        piezas_con_posicion: lista de (pieza, x, y, rotada)
        path: ruta del DXF
        placa_ancho, placa_alto: dimensiones de la placa
        dibujar_contorno_placa: dibujar rectángulo informativo de la placa
    """
    doc, msp = _crear_documento()
    
    if dibujar_contorno_placa:
        if "PLACA" not in doc.layers:
            doc.layers.add(name="PLACA", color=8)
        _dibujar_rectangulo(msp, 0, 0, placa_ancho, placa_alto, layer="PLACA")
    
    for pieza, x, y, rotada in piezas_con_posicion:
        _dibujar_pieza_en_posicion(msp, pieza, x, y, rotada=rotada)
    
    os.makedirs(Path(path).parent, exist_ok=True)
    doc.saveas(path)


def validar_dxf(ruta_dxf: str) -> dict:
    try:
        doc = ezdxf.readfile(ruta_dxf)
        msp = doc.modelspace()
        conteo = {}
        for entity in msp:
            tipo = entity.dxftype()
            conteo[tipo] = conteo.get(tipo, 0) + 1
        return {
            "valido": True,
            "version": doc.dxfversion,
            "layers": len(doc.layers),
            "entidades": conteo,
        }
    except Exception as e:
        return {"valido": False, "error": str(e)}
