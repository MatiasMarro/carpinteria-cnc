# ARCHITECTURE.md - ESTRUCTURA TÉCNICA

## Classes principales

### furniture_core.py
```
Pieza
  .ancho, .alto, .material, .cantidad
  .area, .perimetro, .costo_material
  .agregar_operacion(Operacion)
  .agregar_agujero_minifix(x, y)
  .agregar_agujero_tarugo(x, y, diametro)

Operacion
  .tipo (enum TipoOperacion)
  .posicion (x, y)
  .parametros {diametro, tipo}

Material
  .nombre, .espesor, .densidad, .precio_m2

TipoUnion (enum)
  MINIFIX, TORNILLO, TARUGO, ENCASTRE, NINGUNA
```

### furniture_escritorio.py
```
Escritorio(Protocol)
  .ancho, .profundidad, .altura_trabajo, .num_cajones, .material
  .generar_piezas() → [Pieza, ...]
  .validar() → [warnings]
  .costo_material() → float
  .tiempo_cnc_estimado() → float
  .resumen() → dict

Factories:
  escritorio_compacto(), _estandar(), _ejecutivo(), _gaming()
```

### nesting_engine.py
```
nesting_automatico(piezas, placa_ancho, placa_alto, margen_corte)
  → ResultadoNesting
  
PlacaNesteada
  .numero, .ancho, .alto
  .piezas [(pieza, x, y, rotada), ...]
  .eficiencia → %
  
ResultadoNesting
  .placas [PlacaNesteada, ...]
  .piezas_no_colocadas [Pieza, ...]
  .eficiencia_promedio → %
```

### dxf_exporter.py
```
exportar_placa(piezas_con_posicion, path, placa_ancho, placa_alto)
  → genera DXF R2000 con LINE + CIRCLE

validar_dxf(ruta) → {valido, version, layers, entidades}
```

## Flujo de ejecución

```
cli.py parse args
  ↓
factory (escritorio_estandar() etc)
  ↓
Mueble.generar_piezas() → [Pieza, Pieza, ...]
  ↓
nesting_automatico() → [PlacaNesteada, ...]
  ↓
for placa in resultado.placas:
    exportar_placa(placa.piezas) → placa_N.dxf
```

## Extensión: Agregar nuevo mueble

1. **Crear archivo**: `src/furniture_NUEVO.py`
2. **Clase**: `class NuevoMueble: def __init__(self): ...`
3. **Implementar**:
   ```python
   def generar_piezas(self) -> list[Pieza]:
       piezas = []
       # Crear piezas con self.ancho, self.alto, etc
       return piezas
   
   def validar(self) -> list[str]:
       # warnings si hay
       return []
   
   def costo_material(self) -> float:
       return sum(p.costo_material for p in self.generar_piezas())
   
   def tiempo_cnc_estimado(self) -> float:
       # heurística según piezas
       return 0
   ```
4. **Factories**: `def nuevo_estandar(): return NuevoMueble(...)`
5. **CLI**: Agregar a `MUEBLES_PRECONFIGURADOS` en `cli.py`
6. **Test**: `python cli.py usar nuevo_estandar --exportar`

## Algoritmo nesting

- **Librería**: `rectpack`
- **Algorithm**: `MaxRectsBssf` (Best Short Side Fit)
- **Ordenamiento**: `SORT_AREA` (grandes primero)
- **Rotación**: Automática (MDF sin veta)
- **Margen**: `--mecha N` se suma a dimensiones

Resultado típico:
- 1 placa (escritorio pequeño): 86% eficiencia
- 2 placas (escritorio grande): 71-84% eficiencia promedio

## DXF Generation

Layer mapping:
```
diametro >= 14   → MINIFIX_15 (amarillo)
diametro >= 6    → TARUGO_8 (verde)
diametro < 6     → MECHA_4 (cian)
```

Solo entidades:
- `LINE` (contornos)
- `CIRCLE` (agujeros)

Headers mínimos (R2000 standard):
- `$INSUNITS = 4` (milímetros)
- `$MEASUREMENT = 1` (métrico)

## Constraints

- Placa min: 1500x2000mm (máximo que entra en máquina)
- Placa max: 2500x3000mm (placas comerciales)
- Mecha típica: 4, 5, 6, 8mm
- Margen min: 2mm (entre piezas)
- Posición min desde borde: 20mm (para agujerería segura)

## Performance

- Generar 14 piezas (escritorio): < 1s
- Nesting 14 piezas: < 0.5s
- Exportar DXF: < 0.5s
- **Total**: < 2s para todo el pipeline

## Git estructura

```
main (siempre production-ready)
├─ commits por feature: "Feature: X", "Fix: Y", "Refactor: Z"
├─ nunca branch experimental en proyecto actual
└─ release tags: v1.0, v1.1, v2.0
```

## Testing

No hay unit tests aún (lo agregan en Fase 2).
Testing actual: "¿Abre en Aspire sin errores?"
CLI testing: `python cli.py usar escritorio_estandar --exportar`

---

**Detalles en `.claude/ROADMAP.md` para qué sigue**
