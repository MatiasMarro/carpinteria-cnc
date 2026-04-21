"""
cli.py - Interfaz de línea de comandos
Uso:
    python cli.py listar
    python cli.py usar escritorio_estandar --exportar
    python cli.py escritorio --ancho 1200 --profundidad 600 --exportar
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from furniture_core import MATERIALES, TipoUnion
from furniture_escritorio import (
    Escritorio, escritorio_compacto, escritorio_estandar,
    escritorio_ejecutivo, escritorio_gaming
)
from furniture_estanteria import (
    Estanteria, estanteria_pequena, estanteria_media, estanteria_grande
)
from dxf_exporter import exportar_proyecto


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


def cmd_generar_escritorio(args):
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
        piezas = escritorio.generar_piezas()
        resumen = escritorio.resumen()
        
        print(f"OK: {escritorio}")
        print(f"Piezas: {len(piezas)}")
        print(f"Costo material: ${resumen['costos']['material_estimado']:,}")
        print(f"Tiempo CNC: {resumen['produccion']['tiempo_cnc_horas']:.2f} horas")
        
        if resumen['validaciones']:
            print("\nVALIDACIONES:")
            for warning in resumen['validaciones']:
                print(f"! {warning}")
        
        if args.exportar:
            proyecto_id = generar_id_proyecto()
            output_dir = Path(__file__).parent / "output" / f"{proyecto_id}_escritorio"
            exportar_proyecto(piezas, str(output_dir))
            print(f"\nOK: Exportado a: {output_dir}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_generar_estanteria(args):
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
        piezas = estanteria.generar_piezas()
        resumen = estanteria.resumen()
        
        print(f"OK: {estanteria}")
        print(f"Piezas: {len(piezas)}")
        print(f"Costo material: ${resumen['costos']['material_estimado']:,}")
        print(f"Tiempo CNC: {resumen['produccion']['tiempo_cnc_horas']:.2f} horas")
        
        if args.exportar:
            proyecto_id = generar_id_proyecto()
            output_dir = Path(__file__).parent / "output" / f"{proyecto_id}_estanteria"
            exportar_proyecto(piezas, str(output_dir))
            print(f"\nOK: Exportado a: {output_dir}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def cmd_usar_preconfigurado(args):
    if args.nombre not in MUEBLES_PRECONFIGURADOS:
        print(f"ERROR: Mueble '{args.nombre}' no encontrado")
        print(f"Disponibles: {', '.join(MUEBLES_PRECONFIGURADOS.keys())}")
        sys.exit(1)
    
    factory = MUEBLES_PRECONFIGURADOS[args.nombre]
    mueble = factory()
    imprimir_titulo(f"{args.nombre.upper()}")
    print(f"OK: {mueble}")
    piezas = mueble.generar_piezas()
    print(f"Piezas: {len(piezas)}")
    print(f"Material: ${mueble.costo_material():,}")
    print(f"CNC: {mueble.tiempo_cnc_estimado()/60:.2f} horas")
    
    if args.exportar:
        proyecto_id = generar_id_proyecto()
        output_dir = Path(__file__).parent / "output" / f"{proyecto_id}_{args.nombre}"
        exportar_proyecto(piezas, str(output_dir))
        print(f"\nOK: Exportado a: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Sistema parametrico de muebles CNC")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("listar", help="Lista muebles preconfigurados")
    
    gen_escritorio = subparsers.add_parser("escritorio", help="Genera escritorio personalizado")
    gen_escritorio.add_argument("--ancho", type=float, default=1200)
    gen_escritorio.add_argument("--profundidad", type=float, default=600)
    gen_escritorio.add_argument("--altura-trabajo", type=float, default=750)
    gen_escritorio.add_argument("--num-cajones", type=int, default=2, choices=[2, 3])
    gen_escritorio.add_argument("--altura-cajon", type=float, default=150)
    gen_escritorio.add_argument("--con-espaldar", action="store_true", default=True)
    gen_escritorio.add_argument("--material", default="MDF_18")
    gen_escritorio.add_argument("--exportar", action="store_true")
    
    gen_estanteria = subparsers.add_parser("estanteria", help="Genera estanteria personalizada")
    gen_estanteria.add_argument("--ancho", type=float, default=800)
    gen_estanteria.add_argument("--alto", type=float, default=1800)
    gen_estanteria.add_argument("--profundidad", type=float, default=350)
    gen_estanteria.add_argument("--estantes", type=int, default=5)
    gen_estanteria.add_argument("--material", default="MDF_18")
    gen_estanteria.add_argument("--exportar", action="store_true")
    
    preconfig = subparsers.add_parser("usar", help="Usa un mueble preconfigurado")
    preconfig.add_argument("nombre")
    preconfig.add_argument("--exportar", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "listar":
        cmd_listar()
    elif args.command == "escritorio":
        cmd_generar_escritorio(args)
    elif args.command == "estanteria":
        cmd_generar_estanteria(args)
    elif args.command == "usar":
        cmd_usar_preconfigurado(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
