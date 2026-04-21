"""
dxf_exporter.py
===============
Exporta piezas a archivos DXF compatibles con Vectric Aspire.

Las convenciones de layers permiten que Aspire reconozca automáticamente
qué herramienta debe usar para cada operación.

Uso:
    from dxf_exporter import exportar_pieza_dxf, exportar_proyecto
    from furniture_estanteria import estanteria_media
    
    estanteria = estanteria_media()
    piezas = estanteria.generar_piezas()
    
    # Exportar piezas individuales
    exportar_proyecto(piezas, "output/estanteria_001/")
"""

import os
from pathlib import Path
from typing import Optional

try:
    import ezdxf
except ImportError:
    raise ImportError(
        "Se requiere ezdxf. Instala con: pip install ezdxf"
    )

from furniture_core import Pieza, Operacion, TipoOperacion


# ============================================================================
# CONVENCIÓN DE LAYERS PARA ASPIRE
# ============================================================================

LAYERS_ASPIRE = {
    "CONTORNO_EXTERIOR": {
        "color": 1,  # Rojo en Aspire
        "herramienta": "mecha_6mm_exterior",
        "descripcion": "Contorno exterior (última herramienta)"
    },
    "AGUJEROS_15MM": {
        "color": 2,  # Amarillo en Aspire
        "herramienta": "mecha_15mm",
        "descripcion": "Agujeros minifix (15mm)"
    },
    "AGUJEROS_8MM": {
        "color": 3,  # Verde en Aspire
        "herramienta": "mecha_8mm",
        "descripcion": "Agujeros tarugo (8mm)"
    },
    "AGUJEROS_4MM": {
        "color": 4,  # Cian en Aspire
        "herramienta": "mecha_4mm",
        "descripcion": "Agujeros pequeños (4mm)"
    },
    "RANURAS": {
        "color": 5,  # Magenta en Aspire
        "herramienta": "mecha_4mm",
        "descripcion": "Ranuras y grabados"
    },
    "GRABADO": {
        "color": 6,  # Blanco en Aspire
        "herramienta": "v_bit_grabado",
        "descripcion": "Grabados decorativos"
    },
}


def _crear_documento_dxf(titulo: str = "Pieza CNC") -> tuple:
    """Crea un documento DXF nuevo con layers estándar Aspire"""
    doc = ezdxf.new("R2018", setup=True)
    msp = doc.modelspace()
    
    # Crear layers
    for layer_name, props in LAYERS_ASPIRE.items():
        try:
            doc.layers.new(name=layer_name, dxfattribs={"color": props["color"]})
        except ezdxf.DXFValueError:
            pass  # Layer ya existe
    
    return doc, msp


def exportar_pieza_dxf(pieza: Pieza, path: str,
                       agregar_metadata: bool = True) -> None:
    """
    Exporta una pieza individual a DXF.
    
    Args:
        pieza: Objeto Pieza
        path: Ruta del archivo (ej: "output/lateral.dxf")
        agregar_metadata: Si True, agrega dimensiones como atributos
    """
    doc, msp = _crear_documento_dxf(titulo=pieza.nombre)
    
    # ====== CONTORNO EXTERIOR ======
    # Rectángulo que define los límites de corte
    puntos_contorno = [
        (0, 0),
        (pieza.ancho, 0),
        (pieza.ancho, pieza.alto),
        (0, pieza.alto),
        (0, 0)
    ]
    
    msp.add_lwpolyline(
        puntos_contorno,
        dxfattribs={"layer": "CONTORNO_EXTERIOR", "color": 1}
    )
    
    # ====== OPERACIONES (agujeros, ranuras, etc.) ======
    for op in pieza.operaciones:
        x, y = op.posicion
        
        if op.tipo == TipoOperacion.AGUJERO_CIEGO:
            # Agujero ciego (típicamente minifix 15mm)
            diametro = op.parametros.get("diametro", 15)
            layer = _seleccionar_layer_por_diametro(diametro)
            
            msp.add_circle(
                center=(x, y),
                radius=diametro / 2,
                dxfattribs={"layer": layer, "color": LAYERS_ASPIRE[layer]["color"]}
            )
        
        elif op.tipo == TipoOperacion.AGUJERO_PASANTE:
            # Agujero pasante (típicamente tarugo 8mm)
            diametro = op.parametros.get("diametro", 8)
            layer = _seleccionar_layer_por_diametro(diametro)
            
            msp.add_circle(
                center=(x, y),
                radius=diametro / 2,
                dxfattribs={"layer": layer, "color": LAYERS_ASPIRE[layer]["color"]}
            )
        
        elif op.tipo == TipoOperacion.RANURA:
            # Ranura rectangular
            ancho = op.parametros.get("ancho", 4)
            largo = op.parametros.get("largo", 50)
            angulo = op.parametros.get("angulo", 0)
            
            # Por simplificar, usar rectángulo
            # En producción, implementar rotaciones si es necesario
            rect_points = [
                (x - ancho/2, y - largo/2),
                (x + ancho/2, y - largo/2),
                (x + ancho/2, y + largo/2),
                (x - ancho/2, y + largo/2),
                (x - ancho/2, y - largo/2),
            ]
            msp.add_lwpolyline(
                rect_points,
                dxfattribs={"layer": "RANURAS", "color": 5}
            )
        
        elif op.tipo == TipoOperacion.GRABADO:
            # Grabado (simplemente marcado con círculo pequeño)
            msp.add_circle(
                center=(x, y),
                radius=1,
                dxfattribs={"layer": "GRABADO", "color": 6}
            )
    
    # ====== METADATOS ======
    if agregar_metadata:
        # Agregar dimensiones como texto en un layer diferente
        try:
            doc.layers.new(name="METADATA", dxfattribs={"color": 7})
        except:
            pass
        
        # Texto con dimensiones
        texto = f"{pieza.nombre} {pieza.ancho}x{pieza.alto}mm"
        msp.add_text(
            text=texto,
            dxfattribs={
                "layer": "METADATA",
                "height": 8,
                "color": 7
            }
        ).set_placement((0, -20))
    
    # ====== GUARDAR ======
    # Crear directorio si no existe
    os.makedirs(Path(path).parent, exist_ok=True)
    doc.saveas(path)
    
    print(f"✓ Exportado: {path}")


def exportar_proyecto(piezas: list[Pieza], directorio_salida: str) -> None:
    """
    Exporta todas las piezas de un proyecto a archivos DXF separados.
    
    Genera:
    - Un DXF por tipo de pieza
    - Archivo manifest.txt con información de todas las piezas
    
    Args:
        piezas: Lista de objetos Pieza
        directorio_salida: Ruta donde guardar los archivos
    """
    os.makedirs(directorio_salida, exist_ok=True)
    
    # Exportar cada pieza
    piezas_exportadas = []
    for pieza in piezas:
        # Nombre seguro para archivo
        nombre_archivo = pieza.nombre.lower().replace(" ", "_")
        ruta_dxf = os.path.join(directorio_salida, f"{nombre_archivo}.dxf")
        
        exportar_pieza_dxf(pieza, ruta_dxf)
        piezas_exportadas.append({
            "nombre": pieza.nombre,
            "archivo": f"{nombre_archivo}.dxf",
            "cantidad": pieza.cantidad,
            "dimensiones": f"{pieza.ancho}x{pieza.alto}mm",
            "area_m2": round(pieza.area_total / 1_000_000, 4),
            "operaciones": len(pieza.operaciones),
        })
    
    # Generar manifest
    manifest_path = os.path.join(directorio_salida, "manifest.txt")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("MANIFEST DE PIEZAS\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("Instrucciones para Aspire:\n")
        f.write("1. Abre Aspire\n")
        f.write("2. Para cada pieza:\n")
        f.write("   - File > Open Vector File\n")
        f.write("   - Selecciona el .dxf correspondiente\n")
        f.write("   - Los layers ya están organizados (colores indican herramientas)\n")
        f.write("3. Configura las herramientas según los colores\n")
        f.write("4. Genera toolpaths\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("PIEZAS\n")
        f.write("=" * 70 + "\n\n")
        
        for pieza_info in piezas_exportadas:
            f.write(f"Archivo: {pieza_info['archivo']}\n")
            f.write(f"  Nombre: {pieza_info['nombre']}\n")
            f.write(f"  Cantidad: {pieza_info['cantidad']}\n")
            f.write(f"  Dimensiones: {pieza_info['dimensiones']}\n")
            f.write(f"  Área total: {pieza_info['area_m2']} m²\n")
            f.write(f"  Operaciones CNC: {pieza_info['operaciones']}\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("LAYERS Y HERRAMIENTAS\n")
        f.write("=" * 70 + "\n\n")
        
        for layer_name, props in LAYERS_ASPIRE.items():
            f.write(f"{layer_name}:\n")
            f.write(f"  Color: {props['color']}\n")
            f.write(f"  Herramienta: {props['herramienta']}\n")
            f.write(f"  {props['descripcion']}\n\n")
    
    print(f"\n✓ Proyecto exportado a: {directorio_salida}")
    print(f"✓ Manifest guardado: {manifest_path}")


def _seleccionar_layer_por_diametro(diametro: float) -> str:
    """Selecciona el layer apropiado según el diámetro del agujero"""
    if diametro >= 14:  # Minifix 15mm
        return "AGUJEROS_15MM"
    elif diametro >= 6:  # Tarugo 8mm
        return "AGUJEROS_8MM"
    elif diametro >= 3:  # Pequeños 4mm
        return "AGUJEROS_4MM"
    else:
        return "GRABADO"


def validar_dxf(ruta_dxf: str) -> dict:
    """
    Valida un archivo DXF existente.
    
    Retorna:
        dict con información del archivo y posibles problemas
    """
    try:
        doc = ezdxf.readfile(ruta_dxf)
    except Exception as e:
        return {
            "valido": False,
            "error": str(e)
        }
    
    info = {
        "valido": True,
        "ruta": ruta_dxf,
        "layers": len(doc.layers),
        "entities": len(list(doc.modelspace())),
        "problemas": [],
    }
    
    # Verificar layers estándar
    layers_presentes = {l.dxf.name for l in doc.layers}
    layers_esperados = set(LAYERS_ASPIRE.keys())
    
    if not layers_presentes.intersection(layers_esperados):
        info["problemas"].append(
            "No se encontraron layers estándar Aspire"
        )
    
    # Verificar entidades
    msp = doc.modelspace()
    tipos_entidad = {}
    for entity in msp:
        tipo = entity.dxftype()
        tipos_entidad[tipo] = tipos_entidad.get(tipo, 0) + 1
    
    info["tipos_entidad"] = tipos_entidad
    
    return info


if __name__ == "__main__":
    # Test
    from furniture_estanteria import estanteria_media
    
    print("Probando exportador DXF...")
    
    estanteria = estanteria_media()
    piezas = estanteria.generar_piezas()
    
    exportar_proyecto(piezas, "test_output/estanteria_001")
    
    print("\nValidación de DXF...")
    for pieza in piezas[:1]:  # Validar la primera
        ruta = f"test_output/estanteria_001/{pieza.nombre.lower().replace(' ', '_')}.dxf"
        validacion = validar_dxf(ruta)
        print(validacion)
