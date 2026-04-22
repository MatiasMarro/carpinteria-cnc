"""
cli.py - Interfaz de línea de comandos con NESTING INTEGRADO
=============================================================

Uso:
    python cli.py listar
    python cli.py usar escritorio_estandar --exportar
    python cli.py escritorio --ancho 1200 --profundidad 600 --mecha 6 --exportar
    python cli.py estanteria --ancho 800 --alto 1800 --mecha 4 --exportar
    
Parámetros de nesting:
    --mecha N          Tamaño de mecha en mm (define margen entre piezas)
    --placa-ancho N    Ancho de placa (default 1830)
    --placa-alto N     Alto de placa (default 2750)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from furniture_core import MATERIALES, TipoUnion
from furniture_escritorio import (
    Escritorio, escritorio_compacto, escritorio_estandar,
    escritorio_ejecutivo, escritorio_gaming
)
from furniture_estanteria import (
    Estanteria, estanteria_pequena, estanteria_media, estanteria_grande
)
from dxf_exporter import exportar_placa, exportar_pieza_simple
from nesting_engine import nesting_automatico, resumen_nesting
from sobrantes_registrar import registrar_sobrantes_de_resultado, sugerir_uso_sobrantes


MUEBLES_PRECONFIGURADOS = {
    "escritorio_compacto": escritorio_compacto,
    "escritorio_estandar": escritorio_estandar,
    "escritorio_ejecutivo": escritorio_ejecutivo,
    "escritorio_gaming": escritorio_gaming,
    "estanteria_pequena": estanteria_pequena,
    "estanteria_media": estanteria_media,
    "estanteria_grande": estanteria_grande,
}


def imprimir_titulo(texto):
    print("\n" + "=" * 80)
    print(texto.center(80))
    print("=" * 80 + "\n")


def generar_id_proyecto() -> str:
    return f"P_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def procesar_mueble_con_nesting(mueble, nombre_proyecto: str, args):
    """
    Pipeline completo: mueble -> piezas -> nesting -> DXF por placa
    """
    # 1. Generar piezas
    piezas = mueble.generar_piezas()
    resumen = mueble.resumen()
    
    print(f"MUEBLE: {mueble}")
    print(f"Piezas generadas: {len(piezas)} tipos")
    print(f"Costo material: ${resumen['costos']['material_estimado']:,}")
    print(f"Tiempo CNC estimado: {resumen['produccion']['tiempo_cnc_horas']:.2f} horas")
    
    if resumen.get('validaciones'):
        print("\nVALIDACIONES:")
        for warning in resumen['validaciones']:
            print(f"  ! {warning}")
    
    # 2. Sugerir uso de sobrantes existentes (interactivo)
    proyecto_id = generar_id_proyecto()
    orden_label = f"{proyecto_id}_{nombre_proyecto}"
    asignaciones_sobrantes = []
    if not getattr(args, "no_sugerir_sobrantes", False):
        piezas, asignaciones_sobrantes = sugerir_uso_sobrantes(
            piezas=piezas,
            margen_corte=args.mecha,
            orden_label=orden_label,
        )
        if asignaciones_sobrantes:
            print(f"\n  --> {len(asignaciones_sobrantes)} pieza(s) asignada(s) a sobrantes existentes.")

    # 3. Nesting con piezas restantes
    print(f"\nNESTING (mecha {args.mecha}mm, placa {args.placa_ancho}x{args.placa_alto}mm):")
    print("-" * 80)

    resultado = nesting_automatico(
        piezas=piezas,
        placa_ancho=args.placa_ancho,
        placa_alto=args.placa_alto,
        margen_corte=args.mecha,
        permitir_rotacion=True,
        max_placas=10
    )
    
    print(resumen_nesting(resultado))
    
    # 4. Exportar DXF por placa
    if args.exportar:
        output_dir = Path(__file__).parent / "output" / orden_label
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nEXPORTANDO:")
        print("-" * 80)
        
        for placa in resultado.placas:
            nombre_dxf = f"placa_{placa.numero}_de_{resultado.num_placas}.dxf"
            ruta_dxf = output_dir / nombre_dxf
            
            exportar_placa(
                piezas_con_posicion=placa.piezas,
                path=str(ruta_dxf),
                placa_ancho=placa.ancho,
                placa_alto=placa.alto,
                dibujar_contorno_placa=True
            )
            print(f"  {nombre_dxf} - {placa.num_piezas} piezas ({placa.eficiencia:.1f}% eficiencia)")
        
        # Generar manifest
        manifest = output_dir / "manifest.txt"
        with open(manifest, "w", encoding="utf-8") as f:
            f.write(f"PROYECTO: {nombre_proyecto}\n")
            f.write(f"FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"MUEBLE: {mueble}\n")
            f.write("\n")
            f.write(f"PLACA: {args.placa_ancho}x{args.placa_alto}mm\n")
            f.write(f"MECHA: {args.mecha}mm (margen entre piezas)\n")
            f.write(f"PLACAS NECESARIAS: {resultado.num_placas}\n")
            f.write(f"EFICIENCIA: {resultado.eficiencia_promedio:.1f}%\n")
            f.write("\n")
            f.write("INSTRUCCIONES PARA ASPIRE:\n")
            f.write("1. File > Open Vector File > selecciona placa_X.dxf\n")
            f.write("2. Configura material: MDF 18mm, dimensiones placa\n")
            f.write("3. Layers importados:\n")
            f.write("   - CONTORNO (rojo): contorno exterior -> mecha 6mm\n")
            f.write("   - MINIFIX_15 (amarillo): agujeros minifix -> mecha 15mm\n")
            f.write("   - TARUGO_8 (verde): agujeros tarugos -> mecha 8mm\n")
            f.write("   - MECHA_4 (cian): agujeros pequeños -> mecha 4mm\n")
            f.write("4. Genera toolpaths por cada layer\n")
            f.write("5. Exporta G-code\n")
            f.write("6. Carga en Mach3 y ejecuta\n")
        
        # Apéndice del manifest con piezas cortadas de sobrantes
        if asignaciones_sobrantes:
            with open(manifest, "a", encoding="utf-8") as f:
                f.write("\nPIEZAS DE SOBRANTES (cortar manualmente):\n")
                for a in asignaciones_sobrantes:
                    f.write(f"  - {a['pieza_nombre']} ({a['pieza_ancho']:.0f}x{a['pieza_alto']:.0f}mm) "
                            f"-> sobrante #{a['sobrante_id']} en ({a['pos_x']:.0f},{a['pos_y']:.0f})"
                            f"{' rotada' if a['rotada'] else ''}\n")

        print(f"\nProyecto exportado en: {output_dir}")
        print(f"Manifest guardado: manifest.txt")

        # 5. Auto-registrar sobrantes nuevos en DB
        if not getattr(args, "no_registrar_sobrantes", False):
            ids = registrar_sobrantes_de_resultado(resultado, orden_label)
            if ids:
                print(f"\nSOBRANTES registrados en DB: {len(ids)} (IDs {ids[0]}-{ids[-1]})")


def cmd_listar():
    imprimir_titulo("MUEBLES PRECONFIGURADOS DISPONIBLES")
    for nombre, factory in MUEBLES_PRECONFIGURADOS.items():
        mueble = factory()
        piezas = mueble.generar_piezas()
        print(f"\n- {nombre}")
        print(f"  {mueble}")
        print(f"  Piezas: {len(piezas)}")
        print(f"  Material: ${mueble.costo_material():,.0f}")
        print(f"  CNC: {mueble.tiempo_cnc_estimado()/60:.2f} horas")


def cmd_escritorio(args):
    imprimir_titulo(f"ESCRITORIO {args.ancho}x{args.profundidad}x{args.altura_trabajo}mm")
    try:
        material = MATERIALES.get(args.material, MATERIALES["MDF_18"])
        escritorio = Escritorio(
            ancho=args.ancho,
            profundidad=args.profundidad,
            altura_trabajo=args.altura_trabajo,
            num_cajones=args.num_cajones,
            material=material,
            tipo_union=TipoUnion.MINIFIX,
            incluir_espaldar=args.con_espaldar,
            altura_cajon=args.altura_cajon
        )
        procesar_mueble_con_nesting(escritorio, "escritorio", args)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_estanteria(args):
    imprimir_titulo(f"ESTANTERIA {args.ancho}x{args.alto}x{args.profundidad}mm")
    try:
        material = MATERIALES.get(args.material, MATERIALES["MDF_18"])
        estanteria = Estanteria(
            ancho=args.ancho,
            alto=args.alto,
            profundidad=args.profundidad,
            num_estantes=args.estantes,
            material=material,
            tipo_union=TipoUnion.MINIFIX
        )
        procesar_mueble_con_nesting(estanteria, "estanteria", args)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_usar(args):
    if args.nombre not in MUEBLES_PRECONFIGURADOS:
        print(f"ERROR: '{args.nombre}' no encontrado")
        print(f"Disponibles: {', '.join(MUEBLES_PRECONFIGURADOS.keys())}")
        sys.exit(1)
    
    factory = MUEBLES_PRECONFIGURADOS[args.nombre]
    mueble = factory()
    imprimir_titulo(f"{args.nombre.upper()}")
    procesar_mueble_con_nesting(mueble, args.nombre, args)


def agregar_args_nesting(parser):
    """Agrega argumentos comunes de nesting a un parser"""
    parser.add_argument("--mecha", type=float, default=4,
                       help="Tamaño de mecha en mm (margen entre piezas). Default: 4")
    parser.add_argument("--placa-ancho", type=float, default=1830,
                       help="Ancho de placa en mm. Default: 1830")
    parser.add_argument("--placa-alto", type=float, default=2750,
                       help="Alto de placa en mm. Default: 2750")
    parser.add_argument("--exportar", action="store_true",
                       help="Exportar DXF por placa")
    parser.add_argument("--no-registrar-sobrantes", action="store_true",
                       help="No auto-registrar sobrantes en DB (útil para pruebas)")
    parser.add_argument("--no-sugerir-sobrantes", action="store_true",
                       help="No preguntar por uso de sobrantes existentes")


def main():
    parser = argparse.ArgumentParser(
        description="Sistema paramétrico de muebles CNC con nesting integrado",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # Comando: listar
    subparsers.add_parser("listar", help="Lista muebles preconfigurados")
    
    # Comando: escritorio
    p_esc = subparsers.add_parser("escritorio", help="Genera escritorio personalizado")
    p_esc.add_argument("--ancho", type=float, default=1200)
    p_esc.add_argument("--profundidad", type=float, default=600)
    p_esc.add_argument("--altura-trabajo", type=float, default=750)
    p_esc.add_argument("--num-cajones", type=int, default=2, choices=[2, 3])
    p_esc.add_argument("--altura-cajon", type=float, default=150)
    p_esc.add_argument("--con-espaldar", action="store_true", default=True)
    p_esc.add_argument("--material", default="MDF_18")
    agregar_args_nesting(p_esc)
    
    # Comando: estanteria
    p_est = subparsers.add_parser("estanteria", help="Genera estantería personalizada")
    p_est.add_argument("--ancho", type=float, default=800)
    p_est.add_argument("--alto", type=float, default=1800)
    p_est.add_argument("--profundidad", type=float, default=350)
    p_est.add_argument("--estantes", type=int, default=5)
    p_est.add_argument("--material", default="MDF_18")
    agregar_args_nesting(p_est)
    
    # Comando: usar
    p_usar = subparsers.add_parser("usar", help="Usa un mueble preconfigurado")
    p_usar.add_argument("nombre")
    agregar_args_nesting(p_usar)
    
    args = parser.parse_args()
    
    if args.command == "listar":
        cmd_listar()
    elif args.command == "escritorio":
        cmd_escritorio(args)
    elif args.command == "estanteria":
        cmd_estanteria(args)
    elif args.command == "usar":
        cmd_usar(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
