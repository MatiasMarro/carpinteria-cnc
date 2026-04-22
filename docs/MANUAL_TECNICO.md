# 📘 Manual Técnico del Proyecto — Carpintería CNC 2.0

> Generado el 2026-04-22  
> Versión analizada del código: estado actual del repositorio

---

## 1. Visión General

### Descripción del sistema
Sistema de fabricación de muebles paramétrico orientado a carpintería CNC. Toma parámetros de un mueble (dimensiones, material, tipo de unión), genera automáticamente todas sus piezas con la agujerería correcta, optimiza su disposición en placas de MDF (nesting), exporta archivos DXF compatibles con Aspire V8, y gestiona el stock de retazos sobrantes para reutilizarlos en órdenes futuras.

### Objetivo del proyecto
Eliminar el proceso manual de diseño pieza a pieza. El operador CNC recibe directamente los DXF listos para cargar en Aspire, con los toolpaths por layers (CONTORNO, MINIFIX_15, TARUGO_8, MECHA_4) y un manifest con instrucciones de trabajo.

### Stack tecnológico

| Librería | Versión | Propósito |
|---|---|---|
| `ezdxf` | ≥1.3 | Generación de archivos DXF R2000 |
| `rectpack` | ≥0.2.2 | Algoritmo bin-packing para nesting |
| `shapely` | ≥2.0 | Cálculo geométrico de sobrantes (polígonos) |
| SQLite (stdlib) | — | Persistencia de sobrantes |

---

## 2. Arquitectura

### Estructura de carpetas
```
Carpinteria2.0/
├── cli.py                      ← Punto de entrada. Orquesta todo el pipeline
├── requirements.txt
├── instalar.bat
│
├── src/
│   ├── furniture_core.py       ← Modelos base (Pieza, Material, Operacion, ...)
│   ├── furniture_escritorio.py ← Implementación: Escritorio
│   ├── furniture_estanteria.py ← Implementación: Estantería
│   ├── nesting_engine.py       ← Bin-packing (optimización de placas)
│   ├── dxf_exporter.py         ← Exportación DXF compatible Aspire V8
│   ├── sobrantes_db.py         ← CRUD SQLite de sobrantes
│   ├── sobrantes_geometry.py   ← Cálculo de polígonos sobrantes (Shapely)
│   ├── sobrantes_matcher.py    ← Matching pieza ↔ sobrante disponible
│   └── sobrantes_registrar.py  ← Coordinación sobrantes (registro + sugerencia)
│
├── data/
│   └── sobrantes.db            ← Base de datos SQLite (auto-creada)
│
└── output/
    └── P_{fecha}_{nombre}/     ← Archivos DXF + manifest por proyecto
        ├── placa_1_de_N.dxf
        └── manifest.txt
```

### Diagrama general de dependencias
```
cli.py
 ├──► furniture_core.py
 ├──► furniture_escritorio.py  ──► furniture_core.py
 ├──► furniture_estanteria.py  ──► furniture_core.py
 ├──► nesting_engine.py        ──► [rectpack]
 ├──► dxf_exporter.py          ──► [ezdxf]
 └──► sobrantes_registrar.py
        ├──► sobrantes_db.py        ──► [sqlite3, shapely]
        ├──► sobrantes_geometry.py  ──► [shapely]
        └──► sobrantes_matcher.py   ──► sobrantes_db.py, [shapely]
```

---

## 3. Módulos principales

---

### `furniture_core.py`

**Propósito:** Núcleo del sistema. Define las estructuras de datos que el resto de módulos comparte. No tiene lógica de negocio de ningún mueble concreto.

#### Enumeraciones

| Enum | Valores | Uso |
|---|---|---|
| `TipoUnion` | `MINIFIX`, `TORNILLO`, `TARUGO`, `ENCASTRE`, `NINGUNA` | Define cómo se unen las piezas |
| `TipoOperacion` | `CONTORNO_EXTERIOR`, `AGUJERO_PASANTE`, `AGUJERO_CIEGO`, `RANURA`, `GRABADO`, `ENCASTRE` | Tipo de operación CNC |
| `DireccionVeta` | `HORIZONTAL`, `VERTICAL`, `SIN_VETA` | Orientación visual de la veta del material |

#### Dataclasses principales

| Clase | Campos clave | Descripción |
|---|---|---|
| `Material` | `nombre`, `espesor`, `densidad`, `precio_m2` | Define las propiedades físicas y económicas de un material |
| `Operacion` | `tipo`, `posicion (x,y)`, `parametros`, `herramienta`, `profundidad` | Una operación individual que ejecuta la CNC |
| `Pieza` | `nombre`, `ancho`, `alto`, `material`, `cantidad`, `operaciones`, `permitir_rotacion` | Pieza individual de un mueble, con su agujerería |
| `ArregloPiezas` | `piezas [(pieza,x,y,rotada)]`, `placa_ancho/alto` | Helper para piezas ya posicionadas (interfaz con nesting) |

#### Protocolo `Mueble`

```python
@runtime_checkable
class Mueble(Protocol):
    def generar_piezas(self) -> list[Pieza]: ...
    def validar(self) -> list[str]: ...
    def costo_material(self) -> float: ...
    def tiempo_cnc_estimado(self) -> float: ...
```

Contrato que deben cumplir `Escritorio` y `Estanteria`. Permite polimorfismo estructural sin herencia forzada (duck typing + verificación en runtime).

#### Constantes globales

- `MATERIALES`: dict con `MDF_18`, `MDF_25`, `HDF`, `MELAMINA_18` preconfigurados.
- `HERRAMIENTAS_ESTANDAR`: dict con velocidades y avances por diámetro de mecha.

---

### `furniture_escritorio.py`

**Propósito:** Implementación del mueble `Escritorio`. Genera todas sus piezas con operaciones CNC automáticas.

#### Clase `Escritorio`

```
Parámetros de configuración:
  ancho: float           (mm, eje X)
  profundidad: float     (mm, eje Z)
  altura_trabajo: float  (default 750mm)
  num_cajones: int       (2 o 3)
  material: Material     (default MDF_18)
  tipo_union: TipoUnion  (default MINIFIX)
  incluir_espaldar: bool (default True)
  altura_cajon: float    (default 150mm)
```

**Piezas generadas por `generar_piezas()`:**
```
ESTRUCTURA PRINCIPAL:
  - tapa               (ancho × profundidad, qty=1)
  - lateral            (profundidad × altura_lateral, qty=2)
  - espaldar           (ancho × altura_lateral, qty=1) [condicional]
  - travesano_frontal  (ancho-2e × e, qty=1)
  - travesano_posterior(ancho-2e × e, qty=1)

POR CADA CAJÓN (× num_cajones):
  - cajon_N_frente     (ancho-2e × altura_cajon, qty=1)
  - cajon_N_lateral    (profundidad_cajon × altura_cajon, qty=2)
  - cajon_N_fondo      ((ancho-2e-20) × (profundidad-e-70), qty=1)
```

**Fábricas preconfiguradas:**

| Función | Dimensiones (mm) | Cajones | Notas |
|---|---|---|---|
| `escritorio_compacto()` | 1000×500×750 | 2 | Sin espaldar |
| `escritorio_estandar()` | 1200×600×750 | 2 | Con espaldar |
| `escritorio_ejecutivo()` | 1500×750×750 | 3 | Con espaldar |
| `escritorio_gaming()` | — | — | Definida en fábricas |

---

### `furniture_estanteria.py`

**Propósito:** Implementación del mueble `Estanteria`.

#### Clase `Estanteria`

```
Parámetros:
  ancho: float
  alto: float
  profundidad: float
  num_estantes: int    (1-20)
  material: Material
  tipo_union: TipoUnion
  espaciado_agujeros: float  (auto-calculado si None)
```

**Piezas generadas:**
```
  - lateral   (profundidad × alto, qty=2)
  - tapa      (ancho × profundidad, qty=2)  ← representa tapa + base
  - estante   ((ancho-2e) × profundidad, qty=num_estantes)
  - espaldar  (ancho × alto, qty=1) [solo si alto>1500mm y profundidad>300mm]
```

**Fábricas preconfiguradas:** `estanteria_pequena()`, `estanteria_media()`, `estanteria_grande()`

---

### `nesting_engine.py`

**Propósito:** Optimizar la disposición de piezas en placas de MDF minimizando el desperdicio. Utiliza la librería `rectpack` con el algoritmo **MaxRects BSSF** (Best Short Side Fit).

#### Clase `PlacaNesteada`

Almacena el resultado de una placa: número, dimensiones, lista de `(pieza, x, y, rotada)`, y propiedades calculadas `eficiencia`, `area_usada`, `num_piezas`.

#### Clase `ResultadoNesting`

Agrega las placas y metadatos globales: `num_placas`, `eficiencia_promedio`, `total_piezas_colocadas`, `piezas_no_colocadas`.

#### Función `nesting_automatico()`

```
Parámetros:
  piezas: list[Pieza]      ← objetos con .ancho, .alto, .cantidad
  placa_ancho: float       ← default 1830mm
  placa_alto: float        ← default 2750mm
  margen_corte: float      ← default 4mm (espacio entre piezas = ancho de mecha)
  permitir_rotacion: bool  ← si True, intenta rotar 90°
  max_placas: int          ← límite de placas (default 10)

Retorna: ResultadoNesting
```

---

### `dxf_exporter.py`

**Propósito:** Generar archivos DXF en formato R2000 (AC1015) totalmente compatibles con Aspire V8.502. El DXF usa únicamente entidades `LINE` y `CIRCLE` para máxima compatibilidad (sin LWPOLYLINE con XDATA).

#### Layers generados

| Layer | Color Aspire | Contenido |
|---|---|---|
| `CONTORNO` | 1 (rojo) | Contorno exterior de cada pieza |
| `MINIFIX_15` | 2 (amarillo) | Agujeros minifix (∅15mm) |
| `TARUGO_8` | 3 (verde) | Agujeros tarugo (∅8mm) |
| `MECHA_4` | 4 (cian) | Agujeros pequeños (∅4mm) |
| `RANURA` | 5 | Ranuras |
| `GRABADO` | 6 | Grabados |
| `PLACA` | 8 (gris) | Contorno informativo de la placa |

#### Funciones públicas

| Función | Descripción |
|---|---|
| `exportar_placa(piezas_con_posicion, path, placa_ancho, placa_alto, dibujar_contorno_placa)` | Exporta una placa nesteada completa |
| `exportar_pieza_simple(pieza, path)` | Exporta una pieza individual sin nesting |
| `validar_dxf(ruta_dxf)` | Verifica que el DXF sea legible y retorna estadísticas de entidades |

---

### `sobrantes_db.py`

**Propósito:** Persistencia de sobrantes (retazos) en SQLite. Cada sobrante es un polígono definido por vértices (exterior + posibles huecos interiores), almacenado como JSON.

#### Esquema de tabla `sobrantes`

```sql
id               INTEGER PRIMARY KEY
vertices_json    TEXT     -- lista de [(x,y), ...] del polígono exterior
interiores_json  TEXT     -- lista de anillos de agujeros
material_nombre  TEXT
material_espesor REAL
area_mm2         REAL
ancho_bbox       REAL     -- bounding box para pre-filtrado rápido
alto_bbox        REAL
origen_orden     TEXT     -- ID del proyecto que generó el sobrante
origen_placa     INTEGER
fecha_creacion   TEXT
estado           TEXT     -- CHECK IN ('disponible', 'usado', 'descartado')
usado_en_orden   TEXT
notas            TEXT
```

#### API principal

| Función | Descripción |
|---|---|
| `init_db()` | Crea la DB y tabla si no existen |
| `insert(sobrante)` | Inserta un nuevo sobrante, retorna ID |
| `get(id)` | Obtiene un sobrante por ID |
| `listar_disponibles(material_nombre, material_espesor)` | Lista sobrantes `disponible`, filtrados por material |
| `listar_todos()` | Lista todos los sobrantes |
| `marcar_usado(id, orden)` | Cambia estado a `usado` |
| `marcar_descartado(id)` | Cambia estado a `descartado` |
| `actualizar_poligono(id, nuevo_poly)` | Actualiza el polígono tras usar parcialmente un sobrante |

---

### `sobrantes_geometry.py`

**Propósito:** Calcular los polígonos de sobrantes reales de una placa nesteada usando geometría computacional con Shapely.

#### Función `calcular_sobrantes()`

```
Entrada:
  placa_ancho, placa_alto: float
  piezas_colocadas: [(pieza, x, y, rotada), ...]
  margen_corte: float

Algoritmo:
  1. Crea polígono de la placa completa (box)
  2. Por cada pieza, crea rect reservado = (ancho+margen) × (alto+margen)
  3. Une todos los rects con unary_union
  4. sobrante = placa.difference(union_rects)
  5. Aplica set_precision(1.0mm) y buffer(0) para reparar topología
  6. Filtra geometrías < AREA_MINIMA_MM2 (100cm²)

Retorna: list[Polygon]
```

#### Función `descontar_pieza_de_sobrante()`

Calcula el polígono residual tras cortar una pieza de un sobrante. Usado para actualizar el sobrante en DB después de un uso parcial.

---

### `sobrantes_matcher.py`

**Propósito:** Para cada pieza nueva, buscar en qué sobrante disponible de la DB puede encajar.

#### Función `_buscar_posicion()`

Algoritmo de grid-sweep: recorre el bounding box del polígono sobrante en pasos de 20mm (`PASO_BUSQUEDA_MM`), prueba si el rectángulo `(pieza+margen)` cabe en la posición usando `poly.contains(candidato)`. Complejidad aproximada: `O((W × H) / paso²)` donde `W, H` son las dimensiones del bounding box del sobrante.

**Retorna:** `(x, y)` de la esquina inferior-izquierda donde cabe la pieza, o `None`.

#### Función `buscar_sobrante_para_pieza()`

1. Consulta `listar_disponibles()` filtrando por material y espesor.
2. Para cada sobrante disponible, intenta posicionar la pieza (sin rotar).
3. Si no cabe, intenta rotar 90° (si `pieza.permitir_rotacion`).
4. Ordena matches por `desperdicio_mm2` (menor = mejor ajuste).

#### Función `buscar_sobrantes_para_piezas()`

Versión batch que evita asignar el mismo sobrante a dos piezas distintas. Mantiene un `set usados` de IDs ya asignados.

---

### `sobrantes_registrar.py`

**Propósito:** Módulo de orquestación que conecta el flujo de sobrantes en dos momentos del pipeline.

#### Función `registrar_sobrantes_de_resultado()`

Se llama **después** del nesting. Para cada placa del resultado, calcula los polígonos sobrantes con `calcular_sobrantes()` y los persiste en la DB como `disponible`.

#### Función `sugerir_uso_sobrantes()`

Se llama **antes** del nesting. Flujo interactivo (CLI):

1. Para cada pieza, busca matches en DB.
2. Si hay match, imprime información del sobrante y pregunta `[u]sar / [d]escartar / [s]kip`.
3. Si `usar`: marca el sobrante como `usado` en DB, descuenta 1 unidad de la pieza.
4. Si `descartar`: marca el sobrante como `descartado` permanentemente.
5. Retorna `(piezas_restantes, asignaciones)` donde `piezas_restantes` va al nesting.

---

### `cli.py`

**Propósito:** Punto de entrada. Parsea argumentos, instancia muebles y orquesta el pipeline completo.

#### Subcomandos

| Comando | Acción |
|---|---|
| `listar` | Lista los 7 muebles preconfigurados con estadísticas |
| `escritorio [opciones]` | Crea escritorio con dimensiones personalizadas |
| `estanteria [opciones]` | Crea estantería con dimensiones personalizadas |
| `usar <nombre> [opciones]` | Usa un mueble preconfigurado |

#### Flags comunes (todos los subcomandos excepto `listar`)

```
--mecha N                   Margen entre piezas en mm (default 4)
--placa-ancho N             Ancho de placa en mm (default 1830)
--placa-alto N              Alto de placa en mm (default 2750)
--exportar                  Genera DXF + manifest en output/
--no-registrar-sobrantes    No guarda sobrantes en DB
--no-sugerir-sobrantes      No pregunta por sobrantes previos
```

---

## 4. Funciones clave

---

### `procesar_mueble_con_nesting(mueble, nombre_proyecto, args)`

**Ubicación:** `cli.py`

**Descripción:** Pipeline completo desde un objeto mueble hasta los archivos DXF en disco.

**Flujo paso a paso:**
```
1. mueble.generar_piezas()       → list[Pieza]
2. mueble.resumen()              → imprime costos, tiempos, validaciones
3. sugerir_uso_sobrantes()       → interactivo, reduce piezas que van al nesting
4. nesting_automatico()          → distribuye piezas en placas
5. resumen_nesting()             → imprime estadísticas por placa
6. [si --exportar]:
   a. exportar_placa() × N       → genera placa_K_de_N.dxf
   b. genera manifest.txt con instrucciones para Aspire
   c. registrar_sobrantes_de_resultado() → guarda sobrantes en DB
```

---

### `Escritorio.generar_piezas()` / `Estanteria.generar_piezas()`

**Descripción:** Método principal de los muebles. Calcula dimensiones reales de cada pieza (descontando espesores), crea objetos `Pieza` con sus `Operacion` de agujerería, y retorna la lista completa.

**Patrón común:**
```python
e = self.material.espesor   # espesor del material (18mm en MDF_18)

# Las piezas que van adentro de la estructura siempre miden:
# ancho_exterior - 2 * e  (para encastrar entre laterales)

lateral = Pieza(nombre="lateral", ancho=self.profundidad, alto=...)
lateral.agregar_agujero_minifix(x, y)  # agrega Operacion a la lista
```

**Efecto secundario:** `costo_material()`, `tiempo_cnc_estimado()` y `resumen()` llaman a `generar_piezas()` internamente. Las piezas se recalculan cada vez (sin caché).

---

### `nesting_automatico(piezas, placa_ancho, placa_alto, margen_corte, ...)`

**Ubicación:** `nesting_engine.py`

**Descripción:** Wrapper sobre `rectpack` que acomoda piezas en bins (placas).

**Flujo interno:**
```
1. Crea packer: PackingMode.Offline + BFF + MaxRectsBssf + SORT_AREA
2. Expande piezas por .cantidad: pieza con qty=3 → 3 rects independientes
3. Suma margen_corte a cada dimensión: (w+margen) × (h+margen)
4. Agrega max_placas bins al packer
5. packer.pack()  ← ejecuta el algoritmo
6. Itera abin en packer: reconstruye PlacaNesteada con posiciones
7. Detecta rotación: si rect.width ≈ pieza.alto, la pieza fue rotada
8. Detecta piezas no colocadas: IDs no presentes en ningún bin
```

---

### `calcular_sobrantes(placa_ancho, placa_alto, piezas_colocadas, margen_corte)`

**Ubicación:** `sobrantes_geometry.py`

**Descripción:** Usa operaciones de geometría computacional para calcular las zonas libres de una placa tras el nesting.

**Dependencias externas:** `shapely.geometry.box`, `shapely.ops.unary_union`, `shapely.set_precision`

**Nota:** El sobrante calculado ya incluye el ancho de mecha como espacio no usable. El resultado representa área realmente cortable.

---

### `_buscar_posicion(poly, pieza_w, pieza_h, margen, paso=20)`

**Ubicación:** `sobrantes_matcher.py`

**Descripción:** Algoritmo de colocación por grid-sweep. Complejidad aproximada `O((W × H) / paso²)` donde `W, H` son las dimensiones del bounding box del sobrante.

**Retorna:** `(x, y)` de la esquina inferior-izquierda donde cabe la pieza, o `None`.

---

## 5. Flujos principales

---

### Flujo 1: Generar mueble preconfigurado y exportar DXF

```
$ python cli.py usar escritorio_estandar --exportar --mecha 6

cli.py::main()
  └─► cmd_usar(args)
        └─► factory()  →  Escritorio(1200, 600, 750, ...)
              └─► procesar_mueble_con_nesting(escritorio, "escritorio_estandar", args)
                    ├─[1] escritorio.generar_piezas()
                    │         → [tapa, lateral×2, espaldar, frente×2, lateral_cajon×4,
                    │            fondo×2, travesano×2]  (≈11 piezas)
                    │
                    ├─[2] escritorio.resumen()  → imprime costos y validaciones
                    │
                    ├─[3] sugerir_uso_sobrantes(piezas, margen=6, ...)
                    │         → consulta DB SQLite
                    │         → pregunta interactiva por cada match
                    │         → retorna piezas_restantes (sin las usadas de sobrantes)
                    │
                    ├─[4] nesting_automatico(piezas_restantes, 1830, 2750, margen=6)
                    │         → rectpack MaxRects BSSF
                    │         → retorna ResultadoNesting (1-N placas)
                    │
                    ├─[5] exportar_placa() × N_placas
                    │         → ezdxf R2000
                    │         → output/P_{fecha}_escritorio_estandar/placa_1_de_N.dxf
                    │
                    ├─[6] genera manifest.txt
                    │
                    └─[7] registrar_sobrantes_de_resultado()
                              → shapely difference (placa - piezas)
                              → insert() × M sobrantes en SQLite
```

---

### Flujo 2: Reutilización de sobrantes

```
PROYECTO ANTERIOR:
  nesting → ResultadoNesting
    └─► registrar_sobrantes_de_resultado()
          ├─ calcular_sobrantes() → polígonos residuales
          └─ insert() → sobrantes.db (estado='disponible')

PROYECTO NUEVO:
  cli.py: procesar_mueble_con_nesting()
    └─► sugerir_uso_sobrantes(piezas)
          └─► buscar_sobrante_para_pieza(pieza)
                ├─ listar_disponibles(material)  ← DB query
                ├─ pieza.to_polygon()
                └─ _buscar_posicion(poly, w, h, margen)  ← grid-sweep
                      [si encontró]
                      ├─ pregunta al usuario: [u]sar / [d]escartar / [s]kip
                      ├─ [u]: marcar_usado(id) + descontar pieza del batch
                      └─ [d]: marcar_descartado(id)
```

---

### Flujo 3: Creación de mueble con dimensiones personalizadas

```
$ python cli.py escritorio --ancho 1400 --profundidad 700 --num-cajones 3 --exportar

 → cmd_escritorio(args)
      → Escritorio(ancho=1400, profundidad=700, num_cajones=3, ...)
           → __post_init__: valida altura_cajon * num_cajones <= altura_trabajo - 100
           → generar_piezas() → calcula todas las piezas con dimensiones relativas
      → procesar_mueble_con_nesting(...)  [ver Flujo 1]
```

---

## 6. Problemas detectados y mejoras sugeridas

### P1. `generar_piezas()` se llama múltiples veces sin caché

**Ubicación:** `furniture_escritorio.py`, `furniture_estanteria.py`

`costo_material()`, `tiempo_cnc_estimado()` y `resumen()` cada uno invoca `generar_piezas()` internamente. En `procesar_mueble_con_nesting` se llama `mueble.generar_piezas()` directamente y luego `mueble.resumen()` (que lo llama de nuevo). Para muebles simples el impacto es mínimo, pero representa trabajo redundante.

**Mejora sugerida:** Cachear el resultado con `functools.cached_property`.

---

### P2. Detección de rotación en nesting es frágil

**Ubicación:** `nesting_engine.py`

```python
rotada = abs(ancho_rect_sin_margen - pieza_original.alto) < 1
```

Para piezas cuadradas (`pieza.ancho == pieza.alto`) la detección es ambigua. El DXF puede dibujar los agujeros en posiciones incorrectas si la rotación se detecta mal.

**Mejora sugerida:** Almacenar el flag de rotación explícitamente junto al `rect.rid` durante el packing.

---

### P3. `sugerir_uso_sobrantes()` sin modo batch

El parámetro `input_fn=input` permite inyección para tests. Sin embargo, si se quiere automatizar el pipeline sin interacción, la única opción es `--no-sugerir-sobrantes`. No hay un modo `auto_accept`.

**Mejora sugerida:** Agregar un modo `--aceptar-sobrantes` que use automáticamente el primer match disponible.

---

### P4. Agujeros de cajón potencialmente fuera del margen de seguridad

**Ubicación:** `furniture_escritorio.py`

```python
lateral_cajon.agregar_agujero_tarugo(x, 10, diametro=8)
lateral_cajon.agregar_agujero_tarugo(x, self.altura_cajon - 10, diametro=8)
```

Un cajón con `altura_cajon=25mm` generaría agujeros en `y=10` y `y=15`, ambos dentro del margen prohibido de 20mm. `Pieza.validar()` solo emite advertencias, no bloquea.

**Mejora sugerida:** Agregar validación explícita de `altura_cajon >= 50mm` en `Escritorio.__post_init__`.

---

### P5. `escritorio_gaming()` posiblemente no definida

La función `escritorio_gaming` se importa en `cli.py` pero no estaba presente en el código analizado. Si está ausente, causará un `ImportError` al iniciar.

**Acción:** Verificar que `furniture_escritorio.py` incluye la definición de `escritorio_gaming()`.

---

### P6. El espaldar puede usar un material inconsistente con el mueble principal

**Ubicación:** `furniture_escritorio.py`, `furniture_estanteria.py`

```python
material=MATERIALES.get("HDF", self.material)
```

Si el mueble usa `MELAMINA_18` pero `HDF` no está en `MATERIALES`, el fallback es `self.material`. Si `HDF` sí está, el espaldar siempre usa HDF independientemente del material configurado para el mueble.

**Mejora sugerida:** Agregar un parámetro `material_espaldar: Optional[Material] = None` en el constructor.

---

### P7. Sin transacción atómica en el flujo de sobrantes

`sugerir_uso_sobrantes()` llama `marcar_usado()` de inmediato al elegir `[u]sar`. Si el proceso se interrumpe antes de completar el nesting o la exportación, el sobrante queda marcado como `usado` aunque nunca se haya cortado físicamente.

**Mejora sugerida:** Usar un estado intermedio `reservado` durante el pipeline y confirmar a `usado` solo al finalizar exitosamente.

---

## 7. Recomendaciones

### R1. Cachear `generar_piezas()`

```python
from functools import cached_property

@cached_property
def _piezas(self) -> list[Pieza]:
    return self._calcular_piezas()

def generar_piezas(self) -> list[Pieza]:
    return list(self._piezas)  # copia defensiva
```

### R2. Separar el módulo de sobrantes en una capa de servicio

Actualmente `sobrantes_registrar.py` mezcla lógica de negocio con I/O interactiva. Separar en:

- `SobrantesService`: lógica pura (registrar, buscar, marcar).
- Capa CLI: solo el input/output interactivo.

Esto facilita testing y posible migración a API/web.

### R3. Agregar tests unitarios mínimos

Los módulos `sobrantes_geometry.py` y `nesting_engine.py` son los más críticos y más fáciles de testear de forma determinista:

```python
def test_nesting_una_placa():
    piezas = [Pieza("test", 300, 200, MATERIALES["MDF_18"], cantidad=4)]
    r = nesting_automatico(piezas, 1830, 2750, margen_corte=4)
    assert r.num_placas == 1
    assert r.total_piezas_colocadas == 4
```

### R4. Usar `pathlib.Path` consistentemente en `dxf_exporter.py`

El módulo mezcla `os.makedirs` con `Path(path).parent`. Unificar:

```python
Path(path).parent.mkdir(parents=True, exist_ok=True)
```

### R5. Advertencia explícita si hay piezas no colocadas al exportar

Si `len(resultado.piezas_no_colocadas) > 0` y `--exportar` está activo, el manifest debe incluir una sección de advertencia y/o el proceso debería retornar código de salida no-cero.

### R6. Evitar colisión de IDs de proyecto en ejecución batch

`generar_id_proyecto()` genera `P_YYYYMMDD_HHMMSS`. Dos proyectos iniciados en el mismo segundo sobreescriben el mismo directorio en `output/`. Agregar un sufijo único:

```python
import uuid
def generar_id_proyecto() -> str:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    uid = uuid.uuid4().hex[:4]
    return f"P_{ts}_{uid}"
```
