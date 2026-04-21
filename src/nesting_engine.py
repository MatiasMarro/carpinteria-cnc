"""
nesting_engine.py - Motor de optimización de placas
====================================================
Acomoda piezas en placas de MDF minimizando desperdicio.

Features:
- Placas estándar (configurable, default 1830x2750mm)
- Margen configurable entre piezas (por mecha de corte)
- Rotación automática de piezas (MDF sin veta)
- Multi-placa: si no entra todo, usa más placas
- Salida: lista de placas con piezas posicionadas
"""

from dataclasses import dataclass, field
from rectpack import newPacker, PackingMode, PackingBin, SORT_AREA
from rectpack import MaxRectsBssf, MaxRectsBaf, MaxRectsBl


@dataclass
class PlacaNesteada:
    """Una placa con piezas acomodadas"""
    numero: int                         # 1, 2, 3...
    ancho: float                        # mm
    alto: float                         # mm
    piezas: list = field(default_factory=list)  # [(pieza, x, y, rotada), ...]
    
    @property
    def area_total(self) -> float:
        return self.ancho * self.alto
    
    @property
    def area_usada(self) -> float:
        total = 0
        for pieza, x, y, rotada in self.piezas:
            total += pieza.ancho * pieza.alto
        return total
    
    @property
    def eficiencia(self) -> float:
        if self.area_total == 0:
            return 0
        return (self.area_usada / self.area_total) * 100
    
    @property
    def num_piezas(self) -> int:
        return len(self.piezas)


@dataclass
class ResultadoNesting:
    """Resultado completo del nesting"""
    placas: list  # [PlacaNesteada, ...]
    piezas_no_colocadas: list = field(default_factory=list)
    margen_corte: float = 4.0
    
    @property
    def num_placas(self) -> int:
        return len(self.placas)
    
    @property
    def eficiencia_promedio(self) -> float:
        if not self.placas:
            return 0
        return sum(p.eficiencia for p in self.placas) / len(self.placas)
    
    @property
    def total_piezas_colocadas(self) -> int:
        return sum(p.num_piezas for p in self.placas)


def nesting_automatico(
    piezas: list,
    placa_ancho: float = 1830,
    placa_alto: float = 2750,
    margen_corte: float = 4,
    permitir_rotacion: bool = True,
    max_placas: int = 10
) -> ResultadoNesting:
    """
    Realiza nesting automático de piezas en placas.
    
    Args:
        piezas: lista de objetos Pieza (con .ancho, .alto, .cantidad)
        placa_ancho: ancho de placa en mm (default 1830)
        placa_alto: alto de placa en mm (default 2750)
        margen_corte: margen entre piezas en mm (según mecha)
        permitir_rotacion: si las piezas pueden rotar 90°
        max_placas: máximo de placas a usar
    
    Returns:
        ResultadoNesting con placas y piezas posicionadas
    """
    
    # Crear packer con algoritmo MaxRects (mejor eficiencia)
    packer = newPacker(
        mode=PackingMode.Offline,
        bin_algo=PackingBin.BFF,   # Best Fit First
        pack_algo=MaxRectsBssf,    # Best Short Side Fit
        sort_algo=SORT_AREA,       # Ordenar por área (grandes primero)
        rotation=permitir_rotacion
    )
    
    # Expandir piezas según cantidad y agregar al packer
    piezas_originales = {}  # id -> pieza original
    rect_id = 0
    
    for pieza in piezas:
        # Respetar permitir_rotacion de cada pieza individualmente
        rotacion_pieza = permitir_rotacion and pieza.permitir_rotacion
        
        for i in range(pieza.cantidad):
            # Agregar margen de corte a las dimensiones
            w = pieza.ancho + margen_corte
            h = pieza.alto + margen_corte
            
            packer.add_rect(w, h, rid=rect_id)
            piezas_originales[rect_id] = (pieza, rotacion_pieza)
            rect_id += 1
    
    # Agregar placas disponibles
    for i in range(max_placas):
        packer.add_bin(placa_ancho, placa_alto, bid=i)
    
    # Ejecutar nesting
    packer.pack()
    
    # Procesar resultados
    placas_resultado = []
    piezas_colocadas_ids = set()
    
    for bin_idx, abin in enumerate(packer):
        if len(abin) == 0:
            continue
        
        placa = PlacaNesteada(
            numero=bin_idx + 1,
            ancho=placa_ancho,
            alto=placa_alto
        )
        
        for rect in abin:
            pieza_original, _ = piezas_originales[rect.rid]
            
            # Determinar si la pieza fue rotada
            # rectpack indica orientación con rect.width vs pieza original
            ancho_rect_sin_margen = rect.width - margen_corte
            rotada = abs(ancho_rect_sin_margen - pieza_original.alto) < 1
            
            placa.piezas.append((
                pieza_original,
                rect.x,
                rect.y,
                rotada
            ))
            piezas_colocadas_ids.add(rect.rid)
        
        placas_resultado.append(placa)
    
    # Piezas que no se pudieron colocar
    no_colocadas = []
    for rid, (pieza, _) in piezas_originales.items():
        if rid not in piezas_colocadas_ids:
            no_colocadas.append(pieza)
    
    return ResultadoNesting(
        placas=placas_resultado,
        piezas_no_colocadas=no_colocadas,
        margen_corte=margen_corte
    )


def resumen_nesting(resultado: ResultadoNesting) -> str:
    """Genera resumen legible del resultado de nesting"""
    lineas = []
    lineas.append(f"Placas usadas: {resultado.num_placas}")
    lineas.append(f"Piezas colocadas: {resultado.total_piezas_colocadas}")
    lineas.append(f"Margen de corte: {resultado.margen_corte}mm")
    lineas.append(f"Eficiencia promedio: {resultado.eficiencia_promedio:.1f}%")
    
    if resultado.piezas_no_colocadas:
        lineas.append(f"\nADVERTENCIA: {len(resultado.piezas_no_colocadas)} piezas no se pudieron colocar:")
        for p in resultado.piezas_no_colocadas:
            lineas.append(f"  - {p.nombre} ({p.ancho}x{p.alto}mm)")
    
    lineas.append("\nDETALLE POR PLACA:")
    for placa in resultado.placas:
        lineas.append(f"  Placa {placa.numero}: {placa.num_piezas} piezas, "
                     f"eficiencia {placa.eficiencia:.1f}%")
    
    return "\n".join(lineas)
