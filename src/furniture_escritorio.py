"""
furniture_escritorio.py
=======================
Implementación de Escritorio paramétrico con dos cajones.

Estructura:
- 1 Tapa (superficie de trabajo)
- 2 Laterales
- 1 Espaldar (opcional)
- 2 Cajones (cada uno con frente, laterales, fondo, base)
- Estructura de soporte

Ejemplo de uso:
    from furniture_core import MATERIALES, TipoUnion
    from furniture_escritorio import Escritorio
    
    mdf = MATERIALES["MDF_18"]
    escritorio = Escritorio(
        ancho=1200,
        profundidad=600,
        altura_trabajo=750,
        num_cajones=2,
        material=mdf,
        tipo_union=TipoUnion.MINIFIX
    )
    
    piezas = escritorio.generar_piezas()
    print(f"Total piezas: {len(piezas)}")
    print(f"Costo: ${escritorio.costo_material():,.0f}")
"""

from dataclasses import dataclass
from furniture_core import (
    Pieza, Material, TipoUnion, DireccionVeta, Mueble, MATERIALES
)
from typing import Optional


@dataclass
class Escritorio:
    """
    Escritorio paramétrico con cajones.
    
    Dimensiones:
    - Ancho: superficie de trabajo (eje X)
    - Profundidad: profundidad de escritorio (eje Z)
    - Altura trabajo: altura estándar de escritorio (750mm típico)
    - Num cajones: 2 o 3 (acá implementamos 2)
    
    Estructura:
    - Tapa de trabajo
    - Laterales cerrados (con agujerería para cajones)
    - Estructura interna para sostener cajones
    - Dos cajones con guías
    """
    
    ancho: float                                   # mm (eje X)
    profundidad: float                             # mm (eje Z)
    altura_trabajo: float = 750                    # mm altura estándar
    num_cajones: int = 2                           # 2 o 3
    material: Material = None                      # Se establece por defecto
    tipo_union: TipoUnion = TipoUnion.MINIFIX
    margen_agujereria: float = 50                 # mm desde bordes
    incluir_espaldar: bool = True                 # Agregar respaldo cerrado
    altura_cajon: float = 150                     # altura de cada cajón en mm
    
    def __post_init__(self):
        if self.material is None:
            self.material = MATERIALES["MDF_18"]
        
        if self.num_cajones < 2 or self.num_cajones > 3:
            raise ValueError("Número de cajones debe ser 2 o 3")
        
        if self.altura_cajon * self.num_cajones > self.altura_trabajo - 100:
            raise ValueError(
                f"Cajones muy altos ({self.altura_cajon}mm x {self.num_cajones}) "
                f"para altura de trabajo {self.altura_trabajo}mm"
            )
    
    def generar_piezas(self) -> list[Pieza]:
        """Genera todas las piezas del escritorio"""
        piezas = []
        e = self.material.espesor
        
        # ====== ESTRUCTURA PRINCIPAL ======
        
        # 1. TAPA (superficie de trabajo)
        tapa = Pieza(
            nombre="tapa",
            ancho=self.ancho,
            alto=self.profundidad,
            material=self.material,
            cantidad=1,
            direccion_veta=DireccionVeta.HORIZONTAL,
            permitir_rotacion=False
        )
        # Agujeros para fijar a laterales (tornillos desde abajo)
        for x in [100, self.ancho - 100]:
            for y in [100, self.profundidad - 100]:
                tapa.agregar_agujero_tarugo(x, y, diametro=4)
        piezas.append(tapa)
        
        # 2. LATERALES (estructura de soporte)
        # Altura = altura_trabajo - espesor tapa
        altura_lateral = self.altura_trabajo - e
        
        lateral = Pieza(
            nombre="lateral",
            ancho=self.profundidad,
            alto=altura_lateral,
            material=self.material,
            cantidad=2,
            direccion_veta=DireccionVeta.VERTICAL
        )
        
        # Agujerería para guías de cajones
        # Dos filas de agujeros (izq y der) para instalar correderas
        x_izq = self.margen_agujereria
        x_der = self.profundidad - self.margen_agujereria
        
        # Calcular posiciones Y de los cajones
        espacio_inicial = 50  # mm desde la tapa
        for cajon_num in range(self.num_cajones):
            y_pos = espacio_inicial + cajon_num * (self.altura_cajon + 20)
            
            # 4 agujeros por cada guía de cajón (2 guías por cajón)
            for x in [x_izq, x_der]:
                # Agujeros de montaje para correderas
                for dy in [0, 100, 200, 300]:
                    if y_pos + dy < altura_lateral:
                        lateral.agregar_agujero_tarugo(x, y_pos + dy, diametro=6)
        
        piezas.append(lateral)
        
        # 3. ESPALDAR (optional, pero común en escritorios)
        if self.incluir_espaldar:
            espaldar = Pieza(
                nombre="espaldar",
                ancho=self.ancho,
                alto=altura_lateral,
                material=MATERIALES.get("HDF", self.material),
                cantidad=1,
                permitir_rotacion=False,
                direccion_veta=DireccionVeta.HORIZONTAL
            )
            # Agujeros decorativos o para ventilación
            for x in range(100, int(self.ancho), 150):
                for y in range(100, int(altura_lateral), 200):
                    espaldar.agregar_agujero_tarugo(x, y, diametro=4)
            piezas.append(espaldar)
        
        # ====== CAJONES ======
        # Cada cajón consta de: frente, fondo, 2 laterales, 1 base
        
        for cajon_num in range(self.num_cajones):
            # Ancho interior del cajón (con tolerancia)
            ancho_cajon = self.ancho - 2 * e - 20  # 20mm tolerancia
            profundidad_cajon = self.profundidad - e - 50  # cuenta separación
            
            # FRENTE DEL CAJÓN
            frente = Pieza(
                nombre=f"cajon_{cajon_num + 1}_frente",
                ancho=self.ancho - 2*e,
                alto=self.altura_cajon,
                material=self.material,
                cantidad=1,
                direccion_veta=DireccionVeta.HORIZONTAL
            )
            # Agujeros para tirador
            frente.agregar_agujero_tarugo(
                self.ancho / 2,
                self.altura_cajon / 2,
                diametro=6
            )
            piezas.append(frente)
            
            # LATERALES DEL CAJÓN (2)
            lateral_cajon = Pieza(
                nombre=f"cajon_{cajon_num + 1}_lateral",
                ancho=profundidad_cajon,
                alto=self.altura_cajon,
                material=self.material,
                cantidad=2,
                direccion_veta=DireccionVeta.VERTICAL
            )
            # Agujeros para encastres o tarugos
            for x in [20, profundidad_cajon - 20]:
                lateral_cajon.agregar_agujero_tarugo(x, 10, diametro=8)
                lateral_cajon.agregar_agujero_tarugo(x, self.altura_cajon - 10, diametro=8)
            piezas.append(lateral_cajon)
            
            # FONDO DEL CAJÓN (puede ser MDF más delgado)
            fondo_cajon = Pieza(
                nombre=f"cajon_{cajon_num + 1}_fondo",
                ancho=ancho_cajon - 20,
                alto=profundidad_cajon - 20,
                material=MATERIALES.get("MDF_18", self.material),
                cantidad=1,
                permitir_rotacion=False,
                direccion_veta=DireccionVeta.HORIZONTAL
            )
            piezas.append(fondo_cajon)
        
        # ====== ESTRUCTURA DE SOPORTE ======
        # Travesaños horizontales para refuerzo
        
        # Travesaño frontal
        travesano_frontal = Pieza(
            nombre="travesano_frontal",
            ancho=self.ancho - 2*e,
            alto=e,
            material=self.material,
            cantidad=1,
            permitir_rotacion=False
        )
        piezas.append(travesano_frontal)
        
        # Travesaño posterior
        travesano_posterior = Pieza(
            nombre="travesano_posterior",
            ancho=self.ancho - 2*e,
            alto=e,
            material=self.material,
            cantidad=1,
            permitir_rotacion=False
        )
        piezas.append(travesano_posterior)
        
        return piezas
    
    def validar(self) -> list[str]:
        """Valida el diseño del escritorio"""
        warnings = []
        
        # Altura estándar
        if self.altura_trabajo < 700 or self.altura_trabajo > 800:
            warnings.append(
                f"Altura de trabajo {self.altura_trabajo}mm. "
                f"Estándar es 700-800mm"
            )
        
        # Profundidad
        if self.profundidad < 500:
            warnings.append("Profundidad muy pequeña (< 500mm)")
        if self.profundidad > 800:
            warnings.append("Profundidad muy grande (> 800mm)")
        
        # Ancho
        if self.ancho < 800:
            warnings.append("Ancho muy pequeño (< 800mm)")
        if self.ancho > 2000:
            warnings.append("Ancho muy grande (> 2000mm), considerar división")
        
        # Altura de cajones
        total_altura_cajones = self.altura_cajon * self.num_cajones
        if total_altura_cajones > self.altura_trabajo - 150:
            warnings.append(
                f"Cajones ocupan {total_altura_cajones}mm, "
                f"dejar >= 150mm para estructura"
            )
        
        return warnings
    
    def costo_material(self) -> float:
        """Calcula el costo total de material"""
        piezas = self.generar_piezas()
        return sum(p.costo_material for p in piezas)
    
    def tiempo_cnc_estimado(self) -> float:
        """
        Estima tiempo de CNC en minutos.
        Los escritorios tienen más operaciones que estanterías.
        """
        piezas = self.generar_piezas()
        
        tiempo = 0
        for pieza in piezas:
            # Tiempo de contorno
            tiempo += pieza.perimetro / 100
            
            # Tiempo de operaciones (más densas en escritorio)
            tiempo += len(pieza.operaciones) * 0.5
        
        # Escritorio es más complejo, 15% overhead
        return tiempo * 1.15
    
    def cantidad_accesorios(self) -> dict:
        """Retorna cantidad de accesorios necesarios"""
        e = self.material.espesor
        
        # Correderas de cajón (marcas estándar: 300-400mm)
        largo_correderas = self.profundidad - e - 50
        tipo_corredera = "400mm" if largo_correderas >= 400 else "300mm"
        
        return {
            "correderas_cahones": {
                "cantidad": self.num_cajones * 2,  # 2 por cajón (izq, der)
                "tipo": tipo_corredera,
                "marca_sugerida": "Accuride o equivalente"
            },
            "tiradores": {
                "cantidad": self.num_cajones,
                "tipo": "manija metálica 96mm",
            },
            "tornillos_estrutura": {
                "cantidad": 40,
                "tipo": "4x30mm autorroscante"
            },
            "minifix": {
                "cantidad": 12,
                "tipo": "15mm"
            }
        }
    
    def resumen(self) -> dict:
        """Retorna resumen completo del escritorio"""
        piezas = self.generar_piezas()
        
        return {
            "nombre": "Escritorio",
            "dimensiones": {
                "ancho_mm": self.ancho,
                "profundidad_mm": self.profundidad,
                "altura_mm": self.altura_trabajo,
            },
            "especificaciones": {
                "num_cajones": self.num_cajones,
                "altura_cajon_mm": self.altura_cajon,
                "tipo_union": self.tipo_union.value,
                "material": str(self.material),
                "con_espaldar": self.incluir_espaldar,
            },
            "piezas": {
                "count": len(piezas),
                "tipos": list(set(p.nombre.split('_')[0] for p in piezas)),
                "total_area_m2": round(sum(p.area_total for p in piezas) / 1_000_000, 3),
            },
            "costos": {
                "material_estimado": round(self.costo_material()),
                "accesorios": self.cantidad_accesorios(),
            },
            "produccion": {
                "tiempo_cnc_min": round(self.tiempo_cnc_estimado(), 1),
                "tiempo_cnc_horas": round(self.tiempo_cnc_estimado() / 60, 2),
            },
            "validaciones": self.validar(),
        }
    
    def __str__(self):
        return (f"Escritorio {self.ancho}x{self.profundidad}x{self.altura_trabajo}mm, "
                f"{self.num_cajones} cajones")
    
    def __repr__(self):
        return self.__str__()


# ============================================================================
# FACTORY PATTERNS - Escritorios pre-configurados
# ============================================================================

def escritorio_compacto() -> Escritorio:
    """Escritorio compacto: 100cm x 50cm (apartamento/oficina pequeña)"""
    return Escritorio(
        ancho=1000,
        profundidad=500,
        altura_trabajo=750,
        num_cajones=2,
        altura_cajon=100,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX,
        incluir_espaldar=False
    )


def escritorio_estandar() -> Escritorio:
    """Escritorio estándar: 120cm x 60cm (oficina típica)"""
    return Escritorio(
        ancho=1200,
        profundidad=600,
        altura_trabajo=750,
        num_cajones=2,
        altura_cajon=150,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX,
        incluir_espaldar=True
    )


def escritorio_ejecutivo() -> Escritorio:
    """Escritorio ejecutivo: 150cm x 75cm (despacho/dirección)"""
    return Escritorio(
        ancho=1500,
        profundidad=750,
        altura_trabajo=750,
        num_cajones=3,
        altura_cajon=120,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX,
        incluir_espaldar=True
    )


def escritorio_gaming() -> Escritorio:
    """Escritorio gaming: 140cm x 70cm (con espacio para monitores)"""
    return Escritorio(
        ancho=1400,
        profundidad=700,
        altura_trabajo=780,  # Un poco más alto para ergonomía gaming
        num_cajones=2,
        altura_cajon=120,
        material=MATERIALES["MDF_18"],
        tipo_union=TipoUnion.MINIFIX,
        incluir_espaldar=False
    )
