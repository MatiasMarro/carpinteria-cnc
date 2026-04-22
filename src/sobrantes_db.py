"""
sobrantes_db.py - Persistencia de sobrantes poligonales
========================================================
Base SQLite para sobrantes de placas. El polígono exterior (y opcionales
huecos interiores) se guardan como JSON de vértices en mm.

Uso:
    from sobrantes_db import init_db, Sobrante, insert, listar_disponibles

    init_db()
    s = Sobrante.from_polygon(poly, material_nombre="MDF 18mm",
                              material_espesor=18, origen_orden="orden_1",
                              origen_placa=1)
    sid = insert(s)
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from shapely.geometry import Polygon


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sobrantes.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS sobrantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vertices_json TEXT NOT NULL,
    interiores_json TEXT NOT NULL DEFAULT '[]',
    material_nombre TEXT NOT NULL,
    material_espesor REAL NOT NULL,
    area_mm2 REAL NOT NULL,
    ancho_bbox REAL NOT NULL,
    alto_bbox REAL NOT NULL,
    origen_orden TEXT,
    origen_placa INTEGER,
    fecha_creacion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'disponible'
        CHECK (estado IN ('disponible', 'usado', 'descartado')),
    usado_en_orden TEXT,
    notas TEXT
);

CREATE INDEX IF NOT EXISTS idx_estado_material
    ON sobrantes(estado, material_nombre, material_espesor);
"""


@dataclass
class Sobrante:
    id: Optional[int]
    vertices: list[tuple[float, float]]
    interiores: list[list[tuple[float, float]]]
    material_nombre: str
    material_espesor: float
    area_mm2: float
    ancho_bbox: float
    alto_bbox: float
    origen_orden: Optional[str]
    origen_placa: Optional[int]
    fecha_creacion: str
    estado: str
    usado_en_orden: Optional[str] = None
    notas: Optional[str] = None

    def to_polygon(self) -> Polygon:
        return Polygon(self.vertices, holes=self.interiores or None)

    @classmethod
    def from_polygon(
        cls,
        poly: Polygon,
        material_nombre: str,
        material_espesor: float,
        origen_orden: Optional[str] = None,
        origen_placa: Optional[int] = None,
        notas: Optional[str] = None,
    ) -> "Sobrante":
        exterior = [(round(x, 2), round(y, 2)) for x, y in poly.exterior.coords]
        interiores = [
            [(round(x, 2), round(y, 2)) for x, y in ring.coords]
            for ring in poly.interiors
        ]
        minx, miny, maxx, maxy = poly.bounds
        return cls(
            id=None,
            vertices=exterior,
            interiores=interiores,
            material_nombre=material_nombre,
            material_espesor=material_espesor,
            area_mm2=round(poly.area, 2),
            ancho_bbox=round(maxx - minx, 2),
            alto_bbox=round(maxy - miny, 2),
            origen_orden=origen_orden,
            origen_placa=origen_placa,
            fecha_creacion=datetime.now().isoformat(timespec="seconds"),
            estado="disponible",
            notas=notas,
        )


def _connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.executescript(SCHEMA)


def _row_to_sobrante(row: sqlite3.Row) -> Sobrante:
    return Sobrante(
        id=row["id"],
        vertices=[tuple(p) for p in json.loads(row["vertices_json"])],
        interiores=[
            [tuple(p) for p in ring] for ring in json.loads(row["interiores_json"])
        ],
        material_nombre=row["material_nombre"],
        material_espesor=row["material_espesor"],
        area_mm2=row["area_mm2"],
        ancho_bbox=row["ancho_bbox"],
        alto_bbox=row["alto_bbox"],
        origen_orden=row["origen_orden"],
        origen_placa=row["origen_placa"],
        fecha_creacion=row["fecha_creacion"],
        estado=row["estado"],
        usado_en_orden=row["usado_en_orden"],
        notas=row["notas"],
    )


def insert(sobrante: Sobrante, path: Path = DB_PATH) -> int:
    with _connect(path) as conn:
        cur = conn.execute(
            """
            INSERT INTO sobrantes (
                vertices_json, interiores_json, material_nombre, material_espesor,
                area_mm2, ancho_bbox, alto_bbox, origen_orden, origen_placa,
                fecha_creacion, estado, usado_en_orden, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(sobrante.vertices),
                json.dumps(sobrante.interiores),
                sobrante.material_nombre,
                sobrante.material_espesor,
                sobrante.area_mm2,
                sobrante.ancho_bbox,
                sobrante.alto_bbox,
                sobrante.origen_orden,
                sobrante.origen_placa,
                sobrante.fecha_creacion,
                sobrante.estado,
                sobrante.usado_en_orden,
                sobrante.notas,
            ),
        )
        return cur.lastrowid


def get(sobrante_id: int, path: Path = DB_PATH) -> Optional[Sobrante]:
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT * FROM sobrantes WHERE id = ?", (sobrante_id,)
        ).fetchone()
        return _row_to_sobrante(row) if row else None


def listar_disponibles(
    material_nombre: Optional[str] = None,
    material_espesor: Optional[float] = None,
    path: Path = DB_PATH,
) -> list[Sobrante]:
    query = "SELECT * FROM sobrantes WHERE estado = 'disponible'"
    params: list = []
    if material_nombre is not None:
        query += " AND material_nombre = ?"
        params.append(material_nombre)
    if material_espesor is not None:
        query += " AND material_espesor = ?"
        params.append(material_espesor)
    query += " ORDER BY area_mm2 DESC"

    with _connect(path) as conn:
        return [_row_to_sobrante(r) for r in conn.execute(query, params).fetchall()]


def listar_todos(path: Path = DB_PATH) -> list[Sobrante]:
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT * FROM sobrantes ORDER BY fecha_creacion DESC"
        ).fetchall()
        return [_row_to_sobrante(r) for r in rows]


def marcar_usado(sobrante_id: int, orden: str, path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute(
            "UPDATE sobrantes SET estado = 'usado', usado_en_orden = ? WHERE id = ?",
            (orden, sobrante_id),
        )


def marcar_descartado(sobrante_id: int, path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute(
            "UPDATE sobrantes SET estado = 'descartado' WHERE id = ?",
            (sobrante_id,),
        )


def actualizar_poligono(
    sobrante_id: int, nuevo_poly: Polygon, path: Path = DB_PATH
) -> None:
    exterior = [(round(x, 2), round(y, 2)) for x, y in nuevo_poly.exterior.coords]
    interiores = [
        [(round(x, 2), round(y, 2)) for x, y in ring.coords]
        for ring in nuevo_poly.interiors
    ]
    minx, miny, maxx, maxy = nuevo_poly.bounds
    with _connect(path) as conn:
        conn.execute(
            """
            UPDATE sobrantes
            SET vertices_json = ?, interiores_json = ?, area_mm2 = ?,
                ancho_bbox = ?, alto_bbox = ?
            WHERE id = ?
            """,
            (
                json.dumps(exterior),
                json.dumps(interiores),
                round(nuevo_poly.area, 2),
                round(maxx - minx, 2),
                round(maxy - miny, 2),
                sobrante_id,
            ),
        )


def stats(path: Path = DB_PATH) -> dict:
    with _connect(path) as conn:
        rows = conn.execute(
            """
            SELECT estado, COUNT(*) as n, COALESCE(SUM(area_mm2), 0) as area
            FROM sobrantes GROUP BY estado
            """
        ).fetchall()
    return {r["estado"]: {"cantidad": r["n"], "area_mm2": r["area"]} for r in rows}
