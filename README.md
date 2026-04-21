# Carpintería 2.0 - Sistema Paramétrico CNC

Sistema que genera muebles paramétricos con **nesting automático** listo para CNC.

## Features principales

- Generación paramétrica de muebles (escritorios, estanterías)
- **Nesting automático**: acomoda piezas en placas optimizando uso
- **Un DXF por placa**: todo el nesting ya resuelto
- Compatible con Aspire V8.502 (DXF R2000)
- Configurable: mecha, tamaño de placa, rotación
- Cálculo automático de costos y tiempos

## Flujo de trabajo

```
CLI → nesting automático → DXF(s) por placa → Aspire → G-code → Mach3
```

Un solo comando y tenés el/los archivo(s) DXF listos para abrir en Aspire con todas las piezas ya acomodadas en las placas.

## Instalación

```bash
# 1. Clonar repo
git clone https://github.com/TU_USUARIO/carpinteria-cnc.git
cd carpinteria-cnc

# 2. Instalar dependencias
pip install -r requirements.txt
```

Dependencias:
- `ezdxf` - generación de archivos DXF
- `rectpack` - algoritmo de nesting

## Uso

### Ver muebles preconfigurados
```bash
python cli.py listar
```

### Generar un mueble con nesting automático
```bash
# Escritorio estándar, mecha 6mm
python cli.py usar escritorio_estandar --mecha 6 --exportar

# Escritorio personalizado
python cli.py escritorio --ancho 1400 --profundidad 700 --mecha 6 --exportar

# Estantería
python cli.py estanteria --ancho 1000 --alto 2000 --estantes 6 --mecha 4 --exportar
```

### Parámetros de nesting

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `--mecha` | 4 | Tamaño de mecha en mm (margen entre piezas) |
| `--placa-ancho` | 1830 | Ancho de placa MDF en mm |
| `--placa-alto` | 2750 | Alto de placa MDF en mm |
| `--exportar` | - | Genera los DXF (sino solo muestra nesting) |

## Output

Cada proyecto genera:
```
output/P_20260421_154200_escritorio_estandar/
├── placa_1_de_1.dxf       # Una placa con todas las piezas
└── manifest.txt           # Info del proyecto e instrucciones
```

Si el mueble requiere más de una placa:
```
output/P_20260421_154218_escritorio_ejecutivo/
├── placa_1_de_2.dxf
├── placa_2_de_2.dxf
└── manifest.txt
```

## Convención de layers DXF

El exportador genera archivos con layers que Aspire reconoce:

| Layer | Color | Herramienta sugerida |
|-------|-------|---------------------|
| CONTORNO | Rojo | Mecha 6mm (contorno exterior) |
| MINIFIX_15 | Amarillo | Mecha 15mm (agujeros minifix) |
| TARUGO_8 | Verde | Mecha 8mm (agujeros tarugo) |
| MECHA_4 | Cian | Mecha 4mm (agujeros pequeños) |
| RANURA | Magenta | Mecha 4mm (ranuras) |
| PLACA | Gris | Informativo (contorno placa, no cortar) |

## Muebles disponibles

### Escritorios
- `escritorio_compacto` - 100x50x75cm, 2 cajones
- `escritorio_estandar` - 120x60x75cm, 2 cajones
- `escritorio_ejecutivo` - 150x75x75cm, 3 cajones
- `escritorio_gaming` - 140x70x78cm, 2 cajones

### Estanterías
- `estanteria_pequena` - 60x100x35cm, 4 estantes
- `estanteria_media` - 80x180x35cm, 5 estantes
- `estanteria_grande` - 100x200x35cm, 6 estantes

## Estructura del proyecto

```
Carpinteria2.0/
├── cli.py                          # Interfaz CLI
├── src/
│   ├── furniture_core.py           # Clases base
│   ├── furniture_escritorio.py     # Generador escritorios
│   ├── furniture_estanteria.py     # Generador estanterías
│   ├── nesting_engine.py           # Motor de nesting (rectpack)
│   └── dxf_exporter.py             # Exportador DXF V8-compatible
├── output/                         # DXFs generados por proyecto
├── data/                           # Datos históricos (futuro)
├── docs/                           # Documentación extendida
├── requirements.txt
├── instalar.bat                    # Setup Windows
└── setup_git.bat                   # Setup GitHub
```

## Compatibilidad DXF

Los DXF generados usan formato **R2000 (AC1015)** que es el más compatible con software antiguo como Aspire V8.502. Solo usa entidades básicas:
- LINE (para contornos)
- CIRCLE (para agujeros)

No usa LWPOLYLINE ni XDATA que podrían confundir a versiones viejas.

## Próximas fases

- [ ] Base de datos de sobrantes
- [ ] Dashboard web (Streamlit)
- [ ] Integración Fusion 360
- [ ] Generación directa de G-code (sin Aspire)
- [ ] IoT en CNC (tracking tiempos reales)
