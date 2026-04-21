"""
furniture_core.py
================
Núcleo del sistema paramétrico de muebles para carpintería CNC.
Define las clases base, validadores y enumeraciones.

Uso:
    from furniture_core import Pieza, Material, TipoUnion
    
    mdf = Material(nombre="MDF", espesor=18, densidad=800, precio_m2=18000)
    pieza = Pieza(
        nombre="lateral",
        ancho=350,
        alto=1800,
        material=mdf,
        cantidad=2
    )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS
# ============================================================================

class TipoUnion(Enum):
    """Tipos de uniones entre piezas"""
    MINIFIX = "minifix"        # Sistemas de bisagra oculta (15mm)
    TORNILLO = "tornillo"      # Tornillos autorroscantes
    TARUGO = "tarugo"          # Tarugos de madera + cola
    ENCASTRE = "encastre"      # Encastres cortados por CNC
    NINGUNA = "ninguna"        # Pieza sin unión (base, tapa)


class TipoOperacion(Enum):
    """Tipos de operaciones que realiza la CNC"""
    CONTORNO_EXTERIOR = "contorno_exterior"
    AGUJERO_PASANTE = "agujero_pasante"
    AGUJERO_CIEGO = "agujero_ciego"
    RANURA = "ranura"
    GRABADO = "grabado"
    ENCASTRE = "encastre"


class DireccionVeta(Enum):
    """Dirección de la veta (importante para acabado visual)"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    SIN_VETA = "sin_veta"


# ============================================================================
# CLASES DE DATOS BÁSICAS
# ============================================================================

@dataclass
class Material:
    """Define propiedades de un material"""
    nombre: str
    espesor: float                      # mm
    densidad: float                     # kg/m³
    precio_m2: float                    # precio por m² en moneda local
    
    def __post_init__(self):
        if self.espesor <= 0:
            raise ValueError(f"Espesor debe ser > 0, recibido: {self.espesor}")
        if self.precio_m2 < 0:
            raise ValueError(f"Precio no puede ser negativo: {self.precio_m2}")
    
    @property
    def precio_kg(self) -> float:
        """Convierte precio/m² a precio/kg (aproximado)"""
        # Asume 1m² de material = espesor(mm) * densidad / 1_000_000
        m2_kg = (self.espesor / 1000.0) * self.densidad
        return self.precio_m2 / m2_kg if m2_kg > 0 else 0
    
    def __str__(self):
        return f"{self.nombre} ({self.espesor}mm)"


@dataclass
class Operacion:
    """Una operación que la CNC ejecuta sobre una pieza"""
    tipo: TipoOperacion
    posicion: tuple[float, float]       # (x, y) en mm
    parametros: dict = field(default_factory=dict)
    herramienta: str = ""               # ej: "mecha_15mm"
    profundidad: float = 0              # mm (para agujeros ciegos)
    
    def __post_init__(self):
        x, y = self.posicion
        if not (0 <= x <= 2500 and 0 <= y <= 1500):
            # Aviso (no error) ya que pueden haber diseños especiales
            pass


@dataclass
class Pieza:
    """Representa una pieza individual de un mueble"""
    nombre: str                                    # ej: "lateral", "estante"
    ancho: float                                   # mm (X)
    alto: float                                    # mm (Y)
    material: Material
    cantidad: int = 1
    operaciones: list[Operacion] = field(default_factory=list)
    direccion_veta: DireccionVeta = DireccionVeta.HORIZONTAL
    permitir_rotacion: bool = True                 # para nesting
    
    def __post_init__(self):
        if self.ancho <= 0 or self.alto <= 0:
            raise ValueError(f"Dimensiones inválidas: {self.ancho}x{self.alto}")
        if self.cantidad < 1:
            raise ValueError(f"Cantidad debe ser >= 1, recibido: {self.cantidad}")
    
    @property
    def area(self) -> float:
        """Área de la pieza en mm²"""
        return self.ancho * self.alto
    
    @property
    def area_total(self) -> float:
        """Área total considerando cantidad"""
        return self.area * self.cantidad
    
    @property
    def perimetro(self) -> float:
        """Perímetro en mm"""
        return 2 * (self.ancho + self.alto)
    
    @property
    def costo_material(self) -> float:
        """Costo aproximado del material de esta pieza"""
        area_m2 = self.area_total / 1_000_000
        return area_m2 * self.material.precio_m2
    
    def agregar_operacion(self, operacion: Operacion) -> None:
        """Añade una operación a la pieza"""
        self.operaciones.append(operacion)
    
    def agregar_agujero_minifix(self, x: float, y: float, 
                                profundidad: float = 12.5) -> None:
        """Añade un agujero estándar para minifix (15mm, 12.5mm profundo)"""
        op = Operacion(
            tipo=TipoOperacion.AGUJERO_CIEGO,
            posicion=(x, y),
            parametros={"diametro": 15, "tipo": "minifix"},
            herramienta="mecha_15mm",
            profundidad=profundidad
        )
        self.agregar_operacion(op)
    
    def agregar_agujero_tarugo(self, x: float, y: float, 
                               diametro: float = 8) -> None:
        """Añade un agujero para tarugo estándar"""
        op = Operacion(
            tipo=TipoOperacion.AGUJERO_PASANTE,
            posicion=(x, y),
            parametros={"diametro": diametro, "tipo": "tarugo"},
            herramienta=f"mecha_{int(diametro)}mm",
            profundidad=self.material.espesor + 2  # Pasante
        )
        self.agregar_operacion(op)
    
    def validar(self) -> list[str]:
        """Retorna lista de advertencias/errores"""
        warnings = []
        
        # Verificar que los agujeros estén dentro de la pieza
        margen = 20  # 20mm del borde
        for op in self.operaciones:
            x, y = op.posicion
            if x < margen or x > (self.ancho - margen):
                warnings.append(
                    f"Operación {op.tipo.value} en X={x} muy cerca del borde"
                )
            if y < margen or y > (self.alto - margen):
                warnings.append(
                    f"Operación {op.tipo.value} en Y={y} muy cerca del borde"
                )
        
        return warnings
    
    def __str__(self):
        return f"Pieza({self.nombre}, {self.ancho}x{self.alto}mm, qty={self.cantidad})"
    
    def __repr__(self):
        return self.__str__()


# ============================================================================
# PROTOCOLO PARA MUEBLES (interfaz)
# ============================================================================

@runtime_checkable
class Mueble(Protocol):
    """Protocolo que todo mueble debe implementar"""
    
    def generar_piezas(self) -> list[Pieza]:
        """Genera la lista de piezas que forman el mueble"""
        ...
    
    def validar(self) -> list[str]:
        """Retorna lista de errores/advertencias de diseño"""
        ...
    
    def costo_material(self) -> float:
        """Costo total aproximado de material"""
        ...
    
    def tiempo_cnc_estimado(self) -> float:
        """Tiempo estimado de ejecución en la CNC, en minutos"""
        ...


# ============================================================================
# CLASE HELPER PARA GENERAR LAYOUTS DE PIEZAS
# ============================================================================

@dataclass
class ArregloPiezas:
    """Agrupa múltiples piezas con sus posiciones y orientaciones
    
    Usado por el nesting engine para organizar piezas en placas.
    """
    piezas: list[tuple[Pieza, int, int, bool]] = field(default_factory=list)
    # Estructura: (pieza, x, y, rotada)
    
    placa_ancho: float = 2440
    placa_alto: float = 1220
    
    def agregar_pieza(self, pieza: Pieza, x: float, y: float, 
                     rotada: bool = False) -> None:
        """Añade una pieza en una posición específica"""
        # Validación básica de límites
        w = pieza.alto if rotada else pieza.ancho
        h = pieza.ancho if rotada else pieza.alto
        
        if x + w > self.placa_ancho or y + h > self.placa_alto:
            raise ValueError(
                f"Pieza {pieza.nombre} no cabe en posición ({x}, {y}) "
                f"con dimensiones {w}x{h}"
            )
        
        self.piezas.append((pieza, int(x), int(y), rotada))
    
    @property
    def area_usada(self) -> float:
        """Área total de piezas (sin considerar desperdicio)"""
        return sum(p[0].area for p in self.piezas)
    
    @property
    def area_placa(self) -> float:
        """Área total de la placa"""
        return self.placa_ancho * self.placa_alto
    
    @property
    def eficiencia(self) -> float:
        """Porcentaje de eficiencia (0-100)"""
        if self.area_placa == 0:
            return 0
        return (self.area_usada / self.area_placa) * 100
    
    def __str__(self):
        return (f"Arreglo({len(self.piezas)} piezas, "
                f"eficiencia={self.eficiencia:.1f}%)")


# ============================================================================
# CONFIGURACIÓN DE HERRAMIENTAS ESTÁNDAR
# ============================================================================

HERRAMIENTAS_ESTANDAR = {
    "mecha_4mm": {
        "diametro": 4,
        "velocidad_rpm": 12000,
        "avance_mm_min": 800,
        "usos": ["grabado", "ranuras pequeñas"]
    },
    "mecha_6mm": {
        "diametro": 6,
        "velocidad_rpm": 10000,
        "avance_mm_min": 1000,
        "usos": ["contorno", "pequeños agujeros"]
    },
    "mecha_8mm": {
        "diametro": 8,
        "velocidad_rpm": 9000,
        "avance_mm_min": 1200,
        "usos": ["agujeros tarugo"]
    },
    "mecha_15mm": {
        "diametro": 15,
        "velocidad_rpm": 7000,
        "avance_mm_min": 1500,
        "usos": ["agujeros minifix"]
    },
}

# Materiales comunes
MATERIALES = {
    "MDF_18": Material(
        nombre="MDF 18mm",
        espesor=18,
        densidad=800,
        precio_m2=18000  # Ajustar según tu proveedor
    ),
    "MDF_25": Material(
        nombre="MDF 25mm",
        espesor=25,
        densidad=800,
        precio_m2=24000
    ),
    "HDF": Material(
        nombre="HDF",
        espesor=15,
        densidad=900,
        precio_m2=22000
    ),
    "MELAMINA_18": Material(
        nombre="Melamina 18mm",
        espesor=18,
        densidad=750,
        precio_m2=25000
    ),
}
