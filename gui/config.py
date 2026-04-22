"""
config.py — Configuración visual centralizada de la interfaz
=============================================================
Modificá este archivo para personalizar colores, etiquetas y copyright
sin necesidad de tocar el código de los paneles.
"""

# ===========================================================================
# COPYRIGHT
# ===========================================================================
COPYRIGHT = "© 2026 Carpintería CNC 2.0 — Todos los derechos reservados"

# ===========================================================================
# PALETA DE COLORES  (tema claro minimalista — Light + Orange CNC)
# Para cambiar el tema reemplazá los valores hex de esta sección.
# ===========================================================================
COLORES: dict[str, str] = {
    # Fondos
    "fondo_app":             "#F5F5F5",
    "fondo_panel":           "#FFFFFF",
    "fondo_input":           "#F0F0F0",
    "fondo_tarjeta":         "#FAFAFA",

    # Sidebar (ya no se usa como nav, se mantiene por compatibilidad)
    "sidebar_fondo":         "#FFFFFF",
    "sidebar_boton":         "#F5F5F5",
    "sidebar_boton_hover":   "#EBEBEB",
    "sidebar_boton_activo":  "#FF6B00",
    "sidebar_texto":         "#444444",
    "sidebar_texto_activo":  "#FFFFFF",

    # Texto
    "texto_primario":        "#1A1A1A",
    "texto_secundario":      "#666666",
    "texto_desactivado":     "#BBBBBB",

    # Acentos
    "acento_azul":           "#FF6B00",   # naranja CNC (token principal de la app)
    "acento_verde":          "#16A34A",
    "acento_amarillo":       "#CA8A04",
    "acento_rojo":           "#DC2626",
    "acento_morado":         "#7C3AED",
    "acento_naranja":        "#FF6B00",
    "acento_cyan":           "#0891B2",

    # Botones
    "boton_primario":        "#FF6B00",
    "boton_primario_hover":  "#E55F00",
    "boton_primario_texto":  "#FFFFFF",
    "boton_peligro":         "#DC2626",
    "boton_peligro_hover":   "#B91C1C",
    "boton_secundario":      "#EBEBEB",
    "boton_secundario_hover":"#DEDEDE",
    "boton_secundario_texto":"#333333",
    "boton_outline_borde":   "#FF6B00",
    "boton_outline_texto":   "#FF6B00",
    "boton_outline_hover":   "#FFF0E6",

    # Estados semánticos
    "exito":                 "#16A34A",
    "advertencia":           "#CA8A04",
    "error":                 "#DC2626",
    "info":                  "#0891B2",

    # Bordes
    "borde":                 "#E0E0E0",
    "borde_activo":          "#FF6B00",

    # Stepper
    "paso_bloqueado":        "#E5E5E5",
    "paso_bloqueado_texto":  "#AAAAAA",
    "paso_activo":           "#FF6B00",
    "paso_activo_texto":     "#FFFFFF",
    "paso_completado":       "#16A34A",
    "paso_completado_texto": "#FFFFFF",
    "paso_linea":            "#E0E0E0",
    "paso_linea_hecha":      "#16A34A",

    # ── Canvas de nesting ──────────────────────────────────────────────────
    "canvas_fondo":          "#1A1A1A",
    "canvas_placa_borde":    "#FF6B00",
    "canvas_placa_fondo":    "#262626",

    # Piezas por tipo (se usa el prefijo del nombre de la pieza)
    "pieza_tapa":            "#FF6B00",
    "pieza_lateral":         "#22C55E",
    "pieza_espaldar":        "#A855F7",
    "pieza_estante":         "#06B6D4",
    "pieza_cajon":           "#EAB308",
    "pieza_travesano":       "#F97316",
    "pieza_fondo":           "#EC4899",
    "pieza_frente":          "#8B5CF6",
    "pieza_default":         "#64748B",

    # Agujeros en canvas
    "agujero_minifix":       "#EAB308",
    "agujero_tarugo":        "#22C55E",
    "agujero_mecha4":        "#06B6D4",

    # Tabla sobrantes
    "tabla_header":          "#F0F0F0",
    "tabla_fila_par":        "#FFFFFF",
    "tabla_fila_impar":      "#F7F7F7",
    "tabla_seleccion":       "#FFF0E6",
}

# ===========================================================================
# ETIQUETAS / TEXTOS
# Cambiá cualquier string aquí para adaptar el idioma o la terminología.
# ===========================================================================
LABELS: dict[str, str] = {
    # App
    "app_nombre":               "Carpintería MyM 2.0",
    "app_subtitulo":            "Muebles paramétricos para CNC",

    # Stepper
    "paso_1_titulo":            "Mueble",
    "paso_1_sub":               "Configuración",
    "paso_2_titulo":            "Nesting",
    "paso_2_sub":               "Optimización",
    "paso_3_titulo":            "Exportar",
    "paso_3_sub":               "DXF / Manifest",

    # Navegación lateral (compatibilidad)
    "nav_mueble":               "Mueble",
    "nav_nesting":              "Nesting",
    "nav_sobrantes":            "Sobrantes",
    "nav_exportar":             "Exportar",

    # Footer
    "btn_continuar":            "Continuar  →",
    "btn_volver":               "←  Volver",

    # Panel Mueble
    "mueble_titulo":            "Configuración del Mueble",
    "mueble_preconfig":         "Preconfigurado",
    "mueble_custom":            "Personalizado",
    "mueble_generar":           "Generar Piezas",
    "mueble_resumen_titulo":    "Resumen del Mueble",
    "mueble_sin_generar":       "Configurá el mueble y presioná «Generar Piezas».",

    # Panel Nesting
    "nesting_titulo":           "Optimización de Placas",
    "nesting_params":           "Parámetros de placa",
    "nesting_calcular":         "Calcular Nesting",
    "nesting_calculando":       "Calculando…",
    "nesting_resultado":        "Resultado",
    "nesting_sin_mueble":       "Primero generá un mueble en el paso anterior.",
    "nesting_sin_calcular":     "Configurá los parámetros y presioná «Calcular Nesting».",
    "nesting_sobrantes_btn":    "Usar sobrantes…",
    "nesting_sobrantes_tip":    "No hay sobrantes disponibles en la base de datos",

    # Panel Sobrantes (diálogo)
    "sobrantes_titulo":         "Sobrantes disponibles",
    "sobrantes_actualizar":     "Actualizar",
    "sobrantes_descartar":      "Descartar",
    "sobrantes_sin_datos":      "No hay sobrantes registrados en la base de datos.",

    # Panel Exportar
    "exportar_titulo":          "Exportar DXF",
    "exportar_carpeta":         "Carpeta de salida:",
    "exportar_explorar":        "Explorar…",
    "exportar_boton":           "Exportar DXF",
    "exportar_exportando":      "Exportando…",
    "exportar_exito":           "¡Exportación completada!",
    "exportar_sin_nesting":     "Primero calculá el nesting en el paso anterior.",
    "exportar_registrar":       "Registrar sobrantes automáticamente en DB",
    "exportar_abrir_carpeta":   "Abrir carpeta",
    "exportar_manifest":        "Vista previa del manifest",

    # Diálogo sobrante
    "dialogo_titulo":           "Sobrante disponible",
    "dialogo_usar":             "Usar",
    "dialogo_descartar":        "Descartar",
    "dialogo_saltar":           "Saltar",

    # Columnas tabla sobrantes
    "col_id":                   "ID",
    "col_material":             "Material",
    "col_bbox":                 "BBox (mm)",
    "col_area":                 "Área cm²",
    "col_origen":               "Origen",
    "col_placa":                "Placa",
    "col_fecha":                "Fecha",
    "col_estado":               "Estado",
    "col_acciones":             "Acciones",
}

# ===========================================================================
# DIMENSIONES Y FUENTES
# ===========================================================================
DIMENSIONES: dict[str, int] = {
    "sidebar_ancho":        220,
    "ventana_min_ancho":    1100,
    "ventana_min_alto":     700,
    "ventana_ancho":        1340,
    "ventana_alto":         820,
    "stepper_alto":         72,
    "footer_alto":          60,
}

FUENTES: dict[str, object] = {
    "familia":              "IBM Plex Sans",
    "familia_fallback":     "Segoe UI",
    "familia_mono":         "IBM Plex Mono",
    "familia_mono_fallback":"Consolas",
    "size_normal":          10,
    "size_titulo":          14,
    "size_subtitulo":       11,
    "size_pequeño":         9,
}
