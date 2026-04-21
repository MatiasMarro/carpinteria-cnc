# Carpintería 2.0 - Sistema Paramétrico CNC

Sistema de automatización que genera muebles paramétricos listos para CNC.

Genera automáticamente:
- Piezas individuales (laterales, tapas, cajones, etc.)
- Archivos DXF compatibles con Vectric Aspire
- Cálculo de costos de material
- Estimación de tiempo CNC
- Lista de accesorios (minifix, tornillos, correderas)

## Instalación

```bash
# 1. Clonar repo
git clone https://github.com/TU_USUARIO/carpinteria-cnc.git
cd carpinteria-cnc

# 2. Instalar dependencias
pip install -r requirements.txt
```

## Uso rápido

```bash
# Ver muebles preconfigurados
python cli.py listar

# Generar escritorio estándar (120x60cm, 2 cajones)
python cli.py usar escritorio_estandar --exportar

# Personalizar dimensiones
python cli.py escritorio --ancho 1400 --profundidad 700 --exportar

# Estantería personalizada
python cli.py estanteria --ancho 1000 --alto 2000 --estantes 6 --exportar
```

## Estructura del proyecto

```
Carpinteria2.0/
├── cli.py                 # Interfaz de línea de comandos
├── src/
│   ├── furniture_core.py      # Clases base
│   ├── furniture_escritorio.py # Generador escritorios
│   ├── furniture_estanteria.py # Generador estanterías
│   └── dxf_exporter.py        # Exportador DXF
├── output/                # Proyectos generados (DXF)
├── data/                  # Datos históricos (DB, CSVs)
├── docs/                  # Documentación
└── requirements.txt       # Dependencias Python
```

## Flujo de trabajo

```
1. Ejecutar CLI  →  2. Archivos DXF  →  3. Aspire  →  4. G-code  →  5. Mach3
```

## Muebles disponibles

### Escritorios
- `escritorio_compacto` - 100x50cm, 2 cajones
- `escritorio_estandar` - 120x60cm, 2 cajones
- `escritorio_ejecutivo` - 150x75cm, 3 cajones
- `escritorio_gaming` - 140x70cm, 2 cajones

### Estanterías
- `estanteria_pequena` - 60x100cm, 4 estantes
- `estanteria_media` - 80x180cm, 5 estantes
- `estanteria_grande` - 100x200cm, 6 estantes

## Convención de layers DXF

El exportador genera archivos con layers predefinidos que Aspire reconoce:

| Layer | Color | Herramienta |
|-------|-------|-------------|
| CONTORNO_EXTERIOR | Rojo | Mecha 6mm |
| AGUJEROS_15MM | Amarillo | Mecha 15mm (minifix) |
| AGUJEROS_8MM | Verde | Mecha 8mm (tarugo) |
| AGUJEROS_4MM | Cian | Mecha 4mm |
| RANURAS | Magenta | Mecha 4mm |

## Próximas fases

- [ ] Nesting automático (rectpack)
- [ ] Base de datos de sobrantes
- [ ] Dashboard web (Streamlit)
- [ ] Integración Fusion 360

## Licencia

Privado - Todos los derechos reservados
