# PROJECT.md - CONTEXTO CARPINTERÍA 2.0

## El problema
Matías: carpintero CNC (Córdoba, AR). Escala 3→12 muebles/mes.
Bottleneck: 45min diseño + 30-40min nesting manual = 75min/mueble.
Máquina CNC: Mach3 + Aspire V8.502 (viejo, pero funciona).

## La solución
Sistema Python que genera muebles paramétricos con nesting automático integrado.
Output: **1 DXF por placa** con todas las piezas ya acomodadas.
Ganancia: 75min → 15min = **60min ahorrados por mueble**.

## Stack
- Python 3.13 (dataclasses clean)
- ezdxf (DXF R2000, AC1015)
- rectpack (nesting MaxRects BSSF)
- CLI (argparse) - no web

## Muebles actuales
- **Escritorio** (main): 4 preconfigurados + customizable (ancho, profundidad, altura, cajones)
- **Estantería** (variedad): 3 preconfigurados + customizable

## Configuración Matías
- Placa MDF: 1830x2750mm (configurable `--placa-ancho`, `--placa-alto`)
- Margen: por mecha (4/5/6/8mm) con `--mecha N`
- Material: MDF 18mm blanco
- Precio MDF: $18,000/m² (ajustable en `furniture_core.py`)

## Decisiones críticas (NO cambiar sin debate)

1. **Nesting integrado** → Un DXF por placa (vs múltiples sin nesting)
   - Ahorró 30-40min nesting manual
   - Usuario abre Aspire, ya está todo resuelto

2. **DXF R2000 (AC1015)** → Aspire V8.502
   - R2018 no abrió ("Ningun dato ha sido importado")
   - R2000 probado, funciona perfectamente

3. **Margen configurable** → `--mecha N`
   - Cada herramienta es diferente (4, 5, 6, 8mm)
   - Se suma a dimensiones en nesting

4. **Placa estándar 1830x2750** → Las de Matías
   - Configurable pero por defecto ésta

5. **Modelo paramétrico** → class Escritorio(Protocol)
   - Fácil clonar para "Mesita", "Cajonera", etc.
   - New mueble = 1 archivo nuevo

6. **Dos DXFs para 2+ placas** → placa_1_de_2.dxf + placa_2_de_2.dxf
   - Claridad para usuario

## Arquitectura (condensada)

```
cli.py (orquestador)
  ├─ parse args (--ancho, --mecha, --exportar)
  ├─ factory mueble (escritorio_estandar, etc)
  ├─ .generar_piezas() → [Pieza, Pieza, ...]
  ├─ nesting_automatico() → [PlacaNesteada, ...]
  └─ exportar_placa() → DXF R2000

src/
  ├─ furniture_core.py (Material, Pieza, Operacion, enums)
  ├─ furniture_escritorio.py (Escritorio class + factories)
  ├─ furniture_estanteria.py (Estanteria class + factories)
  ├─ nesting_engine.py (nesting_automatico, PlacaNesteada)
  └─ dxf_exporter.py (exportar_placa, validar_dxf)
```

## CLI Actual

```
python cli.py listar                                  # muebles disponibles
python cli.py usar escritorio_estandar --mecha 6 --exportar
python cli.py escritorio --ancho 1400 --profundidad 700 --mecha 6 --exportar
```

## DXF Output

Layers estándar (todos preconfigurados):
- CONTORNO (rojo) - exterior
- MINIFIX_15 (amarillo) - agujeros 15mm
- TARUGO_8 (verde) - agujeros 8mm
- MECHA_4 (cian) - agujeros 4mm
- RANURA (magenta) - ranuras
- PLACA (gris) - informativo

## Estado actual (v1.0)

✅ Sistema funcional, testeado en Aspire V8.502 real
✅ Escritorio estándar genera 1 placa, 86.2% eficiencia
✅ Escritorio ejecutivo genera 2 placas, 71.7% eficiencia promedio
✅ CLI funciona, nesting automático optimiza

## Validaciones importantes

- Aspire V8.502: ✅ Abre DXF sin errores
- Nesting: ✅ 86% eficiencia típica (rect MaxRects BSSF)
- DXF: ✅ R2000 (60 LINE + 86 CIRCLE probado)

## Riesgos mitigados

- DXF no abre → R2000 testeado
- Nesting malo → Algorithm estándar MaxRects
- Piezas no caben → Warning si no se colocan
- Scaling → Arquitectura modular lista

---

**Todos los detalles en `.claude/ARCHITECTURE.md`, `.claude/ROADMAP.md`**
**Decision log en `docs/PROYECTO_BRIEF.md`**
