"""
furniture_estanteria.py
=======================
Implementación de Estantería paramétrica.

Ejemplo de uso:
    from furniture_core import MATERIALES, TipoUnion
    from furniture_estanteria import Estanteria
    
    mdf = MATERIALES["MDF_18"]
    estanteria = Estanteria(
        ancho=800,
        alto=1800,
        profundidad=350,
        num_estantes=5,
        material=mdf,
        tipo_union=TipoUnion.MINIFIX
    )
    
    piezas = estanteria.generar_piezas()
    print(f"Total piezas: {len(piezas)}")
    print(f"Costo material: ${estanteria.costo_material():,.0f}")
"""

from dataclasses import dataclass
from furniture_core import (
    Pieza, Material, TipoUnion, DireccionVeta, Mueble, MATERIALES
)
from typing import Optional


@dataclass
class Estanteria:
    """
    Estantería paramétrica con estructura lateral cerrada.
    
    Estructura:
    - 2 laterales (ancho x profundidad)
    - 1 tapa y 1 base (alto x profundidad)
    - N estantes (ancho - 2*espesor) x profundidad
    - Uniones según tipo (minifix, tarugo, etc.)
    """
    
    ancho: float                                   # mm (eje X)
    alto: float                                    # mm (eje Y)
    profundidad: float                             # mm (eje Z)
    num_estantes: int
    material: Material
    tipo_union: TipoUnion = TipoUnion.MINIFIX
    margen_agujereria: float = 50                 # mm desde bordes
    espaciado_agujeros: Optional[float] = None    # auto si None
    
    def __post_init__(self):
        if self.num_estantes < 1:
            raise ValueError("Debe haber al menos 1 estante")
        if self.num_estantes > 20:
            raise ValueError("Demasiados estantes (máx 20)")
        
        # Calcular espaciado automático si no se especifica
        if self.espaciado_agujeros is None:
            espacio_disponible = self.alto - 2 * self.material.espesor
            self.espaciado_agujeros = espacio_disponible / (self.num_estantes + 1)
    
    def generar_piezas(self) -> list[Pieza]:
        """Genera automáticamente todas las piezas de la estantería"""
        piezas = []
        e = self.material.espesor
        
        # ====== LATERALES ======
        # Son rectángulos de profundidad x alto, con agujerería para estantes
        lateral = Pieza(
            nombre="lateral",
            ancho=self.profundidad,
            alto=self.alto,
            material=self.material,
            cantidad=2,
            direccion_veta=DireccionVeta.VERTICAL
        )
        
        # Agregar agujeros para minifix (si aplica)
        if self.tipo_union == TipoUnion.MINIFIX:
            # Dos columnas de agujeros, una a cada lado
            x_izq = self.margen_agujereria
            x_der = self.profundidad - self.margen_agujereria
            
            for i in range(1, self.num_estantes + 1):
                y = e + i * self.espaciado_agujeros
                lateral.agregar_agujero_minifix(x_izq, y)
                lateral.agregar_agujero_minifix(x_der, y)
        
        piezas.append(lateral)
        
        # ====== TAPA Y BASE ======
        # Rectángulos ancho x profundidad
        tapa = Pieza(
            nombre="tapa",
            ancho=self.ancho,
            alto=self.profundidad,
            material=self.material,
            cantidad=2,  # tapa + base
            direccion_veta=DireccionVeta.HORIZONTAL
        )
        
        # Agujeros de fijación en tapa/base (si usa minifix)
        if self.tipo_union == TipoUnion.MINIFIX:
            # Dos agujeros centrales por lado para fijar a laterales
            x1 = e + 20
            x2 = self.ancho - e - 20
            y1 = self.profundidad / 4
            y2 = 3 * self.profundidad / 4
            
            tapa.agregar_agujero_minifix(x1, y1)
            tapa.agregar_agujero_minifix(x1, y2)
            tapa.agregar_agujero_minifix(x2, y1)
            tapa.agregar_agujero_minifix(x2, y2)
        
        piezas.append(tapa)
        
        # ====== ESTANTES ======
        # Rectángulos (ancho - 2*espesor) x profundidad
        estante = Pieza(
            nombre="estante",
            ancho=self.ancho - 2 * e,
            alto=self.profundidad,
            material=self.material,
            cantidad=self.num_estantes,
            direccion_veta=DireccionVeta.HORIZONTAL
        )
        
        # Agujeros para tarugos o pins en estantes
        if self.tipo_union in [TipoUnion.TARUGO, TipoUnion.MINIFIX]:
            x1 = e + 20
            x2 = self.ancho - 3*e - 20
            y_centro = self.profundidad / 2
            
            # Agujeros para tarugos de fijación a lateral
            estante.agregar_agujero_tarugo(x1, y_centro, diametro=8)
            estante.agregar_agujero_tarugo(x2, y_centro, diametro=8)
        
        piezas.append(estante)
        
        # ====== PIEZAS ADICIONALES (si aplica) ======
        # Espaldares o refuerzos (opcional, solo si alto > 1500mm)
        if self.alto > 1500 and self.profundidad > 300:
            espaldar = Pieza(
                nombre="espaldar",
                ancho=self.ancho,
                alto=self.alto,
                material=MATERIALES.get("HDF", self.material),
                cantidad=1,
                permitir_rotacion=False,
                direccion_veta=DireccionVeta.VERTICAL
            )
            # Agujeros para sujetadores cada 200mm
            for y in range(100, int(self.alto), 200):
                espaldar.agregar_agujero_tarugo(self.ancho/2, y, diametro=4)
            piezas.append(espaldar)
        
        return piezas
    
    def validar(self) -> list[str]:
        """Valida el diseño de la estantería"""
        warnings = []
        
        # Validar proporciones
        if self.alto < 600:
            warnings.append("Estantería muy baja (< 600mm)")
        if self.alto > 2400:
            warnings.append("Estantería muy alta (> 2400mm), verificar estabilidad")
        
        if self.profundidad < 250:
            warnings.append("Profundidad muy pequeña (< 250mm)")
        if self.profundidad > 500:
            warnings.append("Profundidad muy grande, verificar deformación")
        
        # Validar carga teórica por estante
        # Aproximación: 20kg por cada 50cm de ancho
        carga_estimada = (self.ancho / 500) * 20
        if carga_estimada > 100:
            warnings.append(
                f"Estante puede soportar ~{carga_estimada:.0f}kg, "
                "verificar refuerzos"
            )
        
        # Validar que los estantes quepan en placas estándar
        e = self.material.espesor
        ancho_estante = self.ancho - 2 * e
        if ancho_estante > 2400:
            warnings.append(
                f"Estante muy ancho ({ancho_estante}mm > 2400mm placa)"
            )
        
        return warnings
    
    def costo_material(self) -> float:
        """Calcula el costo total de material"""
        piezas = self.generar_piezas()
        return sum(p.costo_material for p in piezas)
    
    def tiempo_cnc_estimado(self) -> float:
        """
        Estima tiempo de CNC en minutos.
        
        Heurística:
        - ~1 minuto por cada 100mm de perímetro de corte (contorno)
        - ~0.5 minutos por agujero
        """
        piezas = self.generar_piezas()
        
        tiempo = 0
        for pieza in piezas:
            # Tiempo de contorno (perímetro)
            tiempo += pieza.perimetro / 100
            
            # Tiempo de operaciones
            tiempo += len(pieza.operaciones) * 0.5
        
        # Agregar 10% overhead
        return tiempo * 1.1
    
    def cantidad_minifix(self) -> int:
        """Retorna cantidad total de minifix necesarios"""
        if self.tipo_union != TipoUnion.MINIFIX:
            return 0
        
        # 2 agujeros por estante en laterales (arriba y abajo)
        count = self.num_estantes * 2 * 2  # 2 posiciones x 2 laterales
        
        # + 4 agujeros por tapa/base
        count += 2 * 4
        
        return count
    
    def cantidad_tarugos(self) -> int:
        """Retorna cantidad total de tarugos necesarios"""
        if self.tipo_union not in [TipoUnion.TARUGO, TipoUnion.MINIFIX]:
            return 0
        
        # 2 tarugos por estante (1 por lado)
        return self.num_estantes * 2
    
    def resumen(self) -> dict:
        """Retorna resumen completo de la estantería"""
        piezas = self.generar_piezas()
        
        return {
            "nombre": "Estantería",
            "dimensiones": {
                "ancho_mm": self.ancho,
                "alto_mm": self.alto,
                "profundidad_mm": self.profundidad,
            },
            "especificaciones": {
                "num_estantes": self.num_estantes,
                "tipo_union": self.tipo_union.value,
                "material": str(self.material),
            },
            "piezas": {
                "count": len(piezas),
                "tipos": list(set(p.nombre for p in piezas)),
                "detalle": [
                    {
                        "nombre": p.nombre,
                        "dimensiones": f"{p.ancho}x{p.alto}mm",
                        "cantidad": p.cantidad,
                        "area_total_m2": round(p.area_total / 1_000_000, 4),
                    }
                    for p in piezas
                ]
            },
            "costos": {
                "material_estimado": round(self.costo_material()),
                "minifix_necesarios": self.cantidad_minifix(),
                "tarugos_necesarios": self.cantidad_tarugos(),
            },
            "produccion": {
                "tiempo_cnc_min": round(self.tiempo_cnc_estimado(), 1),
                "tiempo_cnc_horas": round(self.tiempo_cnc_estimado() / 60, 2),
            },
            "validaciones": self.validar(),
        }
    
    def __str__(self):
        return (f"Estantería {self.ancho}x{self.alto}x{self.profundidad}mm, "
                f"{self.num_estantes} estantes, {self.tipo_union.value}")
    
    def __repr__(self):
        return self.__str__()


# ============================================================================
# FACTORY PATTERNS - Estanterías pre-configuradas
# ============================================================================

def estanteria_pequena() -> Estanteria:
    """Estantería pequeña: 60cm ancho x 100cm alto"""
    return Estanteria(
        ancho=600,
        alto=1000,
        profundidad=350,
        num_estantes=4,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX
    )


def estanteria_media() -> Estanteria:
    """Estantería media: 80cm x 180cm (más común)"""
    return Estanteria(
        ancho=800,
        alto=1800,
        profundidad=350,
        num_estantes=5,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX
    )


def estanteria_grande() -> Estanteria:
    """Estantería grande: 100cm x 200cm"""
    return Estanteria(
        ancho=1000,
        alto=2000,
        profundidad=350,
        num_estantes=6,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX
    )
