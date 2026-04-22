# CARPINTERÍA 2.0 - PROJECT BRIEF

## Fecha de creación
21 de abril 2026

## Stakeholders
- **Propietario**: Matías (Córdoba, AR)
- **Negocio**: Carpintería CNC, 2 personas, objetivo escalar 3→12 muebles/mes

---

## PROBLEMA INICIAL

### Situación actual (sin sistema)
- 3 muebles/mes máximo (con 2 personas)
- 45 minutos diseño por mueble (AutoCAD/Fusion → DXF manual → Aspire manual)
- Nesting manual en Aspire (30-40min adicionales)
- 25% desperdicio de material
- 5 errores cada 10 muebles (re-cortes)
- Accesorios sin cálculo automático
- Tiempo CNC estimado sin base histórica

### Cuello de botella
**Diseño y preparación**, no la máquina CNC. El tiempo entre "idea" y "G-code listo" era excesivo.

---

## SOLUCIÓN IMPLEMENTADA

### Enfoque: Sistema paramétrico + nesting automático

**Input**: Dimensiones (ancho, profundidad, altura, número de cajones)
**Output**: DXF(s) listos para Aspire con todas las piezas nesteadas optimalmente

### Cambio paradigmático clave
```
ANTES: Mueble único → múltiples DXFs separados → nesting manual
AHORA: Mueble único → DXF(s) de placa completa (nesting ya incluido)
```

Esto ahorró:
- 43 minutos por mueble (45 diseño → 2 diseño paramétrico)
- 30-40 minutos nesting manual (automático)
- **Total: 73 minutos por mueble = ~12h/mes ganadas**

---

## DECISIONES CLAVE TOMADAS

### 1. Lenguaje: Python 3.13
- Inicio rápido, sintaxis clara
- Librerías excelentes (ezdxf, rectpack, dataclasses)
- Fácil de mantener y evolucionar

### 2. Arquitectura modular
- `furniture_core.py` - base reutilizable (Pieza, Material, Operacion)
- `furniture_escritorio.py` - mueble específico (fácil duplicar para otros)
- `nesting_engine.py` - motor optimizado (rectpack MaxRects)
- `dxf_exporter.py` - exportador V8-compatible
- `cli.py` - interfaz (local, sin dependencias web)

**Ventaja**: Agregar nuevos muebles es duplicar 1 archivo, no reescribir el core.

### 3. DXF R2000 (AC1015) no R2018
**Problema encontrado**: Aspire V8.502 no abría R2018 ("Ningun dato ha sido importado")
**Solución**: Usar R2000, solo LINE + CIRCLE, sin LWPOLYLINE ni XDATA
**Validación**: Testeado en Aspire real, funciona perfectamente

### 4. Nesting integrado (no separado)
**Decisión**: Un DXF por placa con todas las piezas ya acomodadas
**Vs alternativa**: Múltiples DXFs de piezas individuales (descartado porque requería nesting manual en Aspire)
**Ganancia**: Usuario abre 1 DXF en Aspire, ya está el nesting resuelto

### 5. Margen configurable por mecha
**Parámetro**: `--mecha N` (4, 5, 6, 8mm según el usuario)
**Por qué**: Margen entre piezas depende de la mecha de corte
**Implementación**: Se suma a dimensiones en nesting, rectpack lo respeta

### 6. Placa estándar: 1830x2750mm
**Especificación de Matías**: Placa MDF estándar que usa
**Configurable**: `--placa-ancho`, `--placa-alto` si cambian
**Default sensato**: No requiere flags si usa estándar

### 7. Dos DXFs por proyecto si necesita múltiples placas
**Lógica**: 
- Escritorio ejecutivo (3 cajones) → 2 placas → `placa_1_de_2.dxf` + `placa_2_de_2.dxf`
- Escritorio estándar → 1 placa → `placa_1_de_1.dxf`
**Ventaja**: Usuario sabe cuántas placas cargar, en qué orden

---

## ARQUITECTURA TÉCNICA FINAL

### Stack
```
Python 3.13
├── ezdxf (generación DXF R2000)
├── rectpack (algoritmo nesting MaxRects)
└── dataclasses (estructuras clean)
```

### Estructura de código
```
Carpinteria2.0/
├── cli.py                              # Orquestador principal
├── src/
│   ├── furniture_core.py               # Enums, Material, Pieza, Operacion
│   ├── furniture_escritorio.py         # Clase Escritorio + factories
│   ├── furniture_estanteria.py         # Clase Estanteria + factories
│   ├── nesting_engine.py               # nesting_automatico() y PlacaNesteada
│   └── dxf_exporter.py                 # exportar_placa(), validar_dxf()
├── output/                             # DXFs generados por proyecto
├── docs/                               # Documentación
└── README.md                           # Guía rápida
```

### Pipeline de ejecución
```
CLI args → Mueble (factory)
    ↓
Generador.generar_piezas() → [Pieza, Pieza, ...]
    ↓
nesting_automatico() → [PlacaNesteada, PlacaNesteada, ...]
    ↓
Para cada placa:
    exportar_placa(piezas_posicionadas) → DXF R2000
    ↓
manifest.txt (info del proyecto)
```

---

## ESPECIFICACIONES TÉCNICAS FINALES

### Muebles soportados (MVP)
| Tipo | Preconfigurados | Customizable |
|------|-----------------|--------------|
| Escritorio | 4 (compacto, estándar, ejecutivo, gaming) | Sí (ancho, profundidad, altura, cajones) |
| Estantería | 3 (pequeña, media, grande) | Sí (ancho, alto, profundidad, estantes) |

### Algoritmo de nesting
- **Librería**: rectpack
- **Algoritmo**: MaxRects Best Short Side Fit (BSSF)
- **Orden**: SORT_AREA (grandes primero)
- **Rotación**: Automática (MDF sin veta)
- **Margen**: Configurable por mecha (default 4mm)
- **Salida**: Posición (x, y) + rotada (bool) para cada pieza

### DXF Export
- **Formato**: R2000 (AC1015) - máxima compatibilidad
- **Entidades**: LINE (contornos) + CIRCLE (agujeros)
- **Layers**: 6 + placa informativa
  - CONTORNO (rojo) - exterior
  - MINIFIX_15 (amarillo) - agujeros 15mm
  - TARUGO_8 (verde) - agujeros 8mm
  - MECHA_4 (cian) - agujeros 4mm
  - RANURA (magenta) - ranuras
  - GRABADO (blanco) - grabados
  - PLACA (gris) - informativo

### CLI
```
python cli.py listar                                    # Ver opciones
python cli.py usar escritorio_estandar --mecha 6 --exportar
python cli.py escritorio --ancho 1400 --mecha 6 --exportar
```

Parámetros nesting:
- `--mecha` (default 4)
- `--placa-ancho` (default 1830)
- `--placa-alto` (default 2750)
- `--exportar` (genera DXF, sino solo muestra nesting)

---

## RESULTADOS VALIDADOS

### Ejemplo: Escritorio estándar (120x60x75cm, 2 cajones)
```
Input:
  $ python cli.py usar escritorio_estandar --mecha 6 --exportar

Output:
  Piezas: 14 (tapa, laterales x2, espaldar, 6 cajón, 2 travesaños)
  Material: $81,599 ARS
  Tiempo CNC: 6.23 horas
  Nesting: 1 placa (1830x2750mm), 86.2% eficiencia
  
  Generado: placa_1_de_1.dxf (31KB, 60 LINE + 86 CIRCLE)
  Estado en Aspire: ✅ Abre perfectamente
```

### Ejemplo: Escritorio ejecutivo (150x75x75cm, 3 cajones)
```
Piezas: 18
Material: $134,349 ARS
Tiempo CNC: 9.36 horas
Nesting: 2 placas
  - Placa 1: 14 piezas, 84.2% eficiencia
  - Placa 2: 4 piezas, 59.3% eficiencia
```

---

## ROADMAP A FUTURO (Fases 2-4)

### FASE 2 (1-2 semanas)
- [ ] Nesting v2: heurísticas avanzadas (Simulated Annealing)
- [ ] Base de datos sobrantes: SQLite + consulta automática
- [ ] Histórico tiempos: calibración del estimador con datos reales
- [ ] Dashboard Streamlit: interfaz web local

### FASE 3 (1-2 meses)
- [ ] Agregar más muebles: mesita, cajonera, placard
- [ ] Integración Fusion 360: add-in para leer parámetros directamente
- [ ] Reporte PDF: cotizaciones + lista de accesorios

### FASE 4 (3-6 meses)
- [ ] IoT en CNC: Raspberry Pi monitoreando Mach3 en tiempo real
- [ ] ML: predicción de tiempos con histórico
- [ ] Dashboard producción: kanban digital de órdenes
- [ ] Posible comercialización

---

## LECCIONES APRENDIDAS

### Qué funcionó
1. **Separar generación de piezas del nesting** - Permite reutilizar ambos en otros contextos
2. **DXF R2000 + only LINE/CIRCLE** - Compatibilidad máxima con software viejo
3. **Margen configurable por mecha** - Refleja realidad: cada mecha es diferente
4. **Preconfigurados + customización** - 90% de casos resueltos rápido, 10% personalizables
5. **Un DXF por placa** - Flujo simplificado, nesting no requerido en Aspire

### Qué no funcionó (evitar)
1. ❌ **R2018 + LWPOLYLINE** - Aspire V8 no abrió
2. ❌ **Múltiples DXFs sin nesting** - Requería trabajo manual post-generación
3. ❌ **Estimador sin histórico** - Heurística simple es imprecisa (necesita data real)
4. ❌ **Asumir configuración sin preguntar** - Mecha, tamaño placa, rotación son críticos

---

## RIESGOS MITIGADOS

| Riesgo | Mitigación |
|--------|-----------|
| DXF no abre en Aspire | R2000 testeado, validación incluida |
| Nesting subóptimo | MaxRects BSSF es algorithm estándar, 86% eficiencia real |
| Material desperdiciado | Histórico + ML para optimización después |
| Mueble no cabe en placa | Validación + warning si piezas no se colocan |
| Equipo crece, necesita versión colaborativa | Git listo, estructura modular para equipos |

---

## CÓMO USAR ESTE DOCUMENTO

1. **Para onboarding**: Compartir con nuevo dev / socio que entre al proyecto
2. **Para decisiones futuras**: Releer "DECISIONES CLAVE" antes de cambios arquitectónicos
3. **Para roadmap**: Referencia de qué sigue (FASE 2, 3, 4)
4. **Para bugs**: "LECCIONES APRENDIDAS" qué funcionó vs qué no

---

## Contacto / Notas
- Versión actual: 1.0 (nesting integrado, DXF V8-compatible)
- Próxima versión: 1.1 (sobrantes DB, dashboard)
- Responsable: Claude AI (arquitectura) + Matías (validación CNC real)

