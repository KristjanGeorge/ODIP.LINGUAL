"""
M1: Importación y validación de archivos 3D.
Soporta STL, PLY, OBJ y DICOM (DCM).
RF-01, RF-02.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Final

import numpy as np
import open3d as o3d

from lingualParam.types import FormatoArchivo, MallaImportada, TipoArcada

FORMATOS_SOPORTADOS: Final[set[str]] = {"stl", "ply", "obj", "dcm"}
MIN_VERTICES: Final[int] = 1_000
MIN_CARAS: Final[int] = 500
TOLERANCIA_UNIDAD_MM: Final[float] = 500.0  # coordenada máxima razonable en mm


class ErrorImportacion(Exception):
    """Error de importación o validación de archivo 3D."""


def _calcular_hash_archivo(ruta: str) -> str:
    """Calcula el SHA-256 del archivo en disco."""
    sha256 = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65_536), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def _detectar_formato(ruta: str) -> FormatoArchivo:
    """Infiere el formato a partir de la extensión."""
    ext = Path(ruta).suffix.lower().lstrip(".")
    if ext not in FORMATOS_SOPORTADOS:
        raise ErrorImportacion(
            f"Formato '{ext}' no soportado. Use: {FORMATOS_SOPORTADOS}"
        )
    return FormatoArchivo(ext)


def _cargar_malla_open3d(ruta: str) -> o3d.geometry.TriangleMesh:
    """Carga la malla usando Open3D (STL, PLY, OBJ)."""
    mesh = o3d.io.read_triangle_mesh(ruta)
    if not mesh.has_vertices():
        raise ErrorImportacion(f"No se pudieron leer vértices de: {ruta}")
    return mesh


def _cargar_dcm(ruta: str) -> o3d.geometry.TriangleMesh:
    """
    Carga un archivo DICOM y extrae la superficie como malla.
    Requiere vtk o pydicom + marching cubes.
    """
    try:
        import vtk
        from vtk.util.numpy_support import vtk_to_numpy

        reader = vtk.vtkDICOMImageReader()
        reader.SetFileName(ruta)
        reader.Update()
        mc = vtk.vtkMarchingCubes()
        mc.SetInputConnection(reader.GetOutputPort())
        mc.SetValue(0, 400)  # umbral HU para hueso
        mc.Update()
        poly = mc.GetOutput()
        pts = vtk_to_numpy(poly.GetPoints().GetData()).astype(np.float64)
        cells = vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
        mesh = o3d.geometry.TriangleMesh(
            o3d.utility.Vector3dVector(pts),
            o3d.utility.Vector3iVector(cells.astype(np.int32)),
        )
        return mesh
    except ImportError as e:
        raise ErrorImportacion(
            "vtk no disponible para procesar DCM. Instale vtk>=9.0."
        ) from e


def _validar_geometria(
    vertices: np.ndarray, caras: np.ndarray, ruta: str
) -> None:
    """RF-02: valida integridad, densidad y unidades."""
    if len(vertices) < MIN_VERTICES:
        raise ErrorImportacion(
            f"Malla insuficiente: {len(vertices)} vértices (mínimo {MIN_VERTICES})."
        )
    if len(caras) < MIN_CARAS:
        raise ErrorImportacion(
            f"Malla insuficiente: {len(caras)} caras (mínimo {MIN_CARAS})."
        )
    coord_max = np.max(np.abs(vertices))
    if coord_max > TOLERANCIA_UNIDAD_MM:
        raise ErrorImportacion(
            f"Coordenadas fuera de rango mm ({coord_max:.1f}). "
            "Verifique que el archivo esté en milímetros."
        )
    if np.any(np.isnan(vertices)) or np.any(np.isinf(vertices)):
        raise ErrorImportacion("El archivo contiene valores NaN o infinito.")


def _inferir_arcada(vertices: np.ndarray) -> TipoArcada:
    """
    Heurística simple: si hay dos grupos claramente separados en Y, son ambas arcadas.
    """
    y_min, y_max = float(vertices[:, 1].min()), float(vertices[:, 1].max())
    rango_y = y_max - y_min
    if rango_y > 80:
        return TipoArcada.AMBAS
    centroide_y = float(vertices[:, 1].mean())
    return TipoArcada.SUPERIOR if centroide_y > 0 else TipoArcada.INFERIOR


def importar_archivo(ruta: str) -> MallaImportada:
    """
    RF-01 + RF-02: Importa y valida un archivo 3D dental.

    Args:
        ruta: Ruta absoluta al archivo (.stl, .ply, .obj, .dcm).

    Returns:
        MallaImportada con vértices en mm y metadatos.

    Raises:
        ErrorImportacion: Si el archivo no es válido o no se puede leer.
    """
    if not os.path.exists(ruta):
        raise ErrorImportacion(f"Archivo no encontrado: {ruta}")

    formato = _detectar_formato(ruta)
    hash_origen = _calcular_hash_archivo(ruta)

    if formato == FormatoArchivo.DCM:
        mesh = _cargar_dcm(ruta)
    else:
        mesh = _cargar_malla_open3d(ruta)

    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    caras = np.asarray(mesh.triangles, dtype=np.int32)

    _validar_geometria(vertices, caras, ruta)

    arcada = _inferir_arcada(vertices)

    return MallaImportada(
        ruta_origen=ruta,
        formato=formato.value,
        vertices=vertices,
        caras=caras,
        unidad_mm=True,
        arcada=arcada.value,
        hash_origen=hash_origen,
        metadata={
            "n_vertices": len(vertices),
            "n_caras": len(caras),
            "bbox_mm": {
                "x": [float(vertices[:, 0].min()), float(vertices[:, 0].max())],
                "y": [float(vertices[:, 1].min()), float(vertices[:, 1].max())],
                "z": [float(vertices[:, 2].min()), float(vertices[:, 2].max())],
            },
        },
    )
