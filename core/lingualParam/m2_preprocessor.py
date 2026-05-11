"""
M2: Pre-procesamiento de malla 3D.
Aplica Statistical Outlier Removal, suavizado Laplaciano y normalización al
plano oclusal. RF-03.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import open3d as o3d

from lingualParam.types import MallaImportada

# Parámetros SOR (Statistical Outlier Removal)
NB_NEIGHBORS_SOR: Final[int] = 30
STD_RATIO_SOR: Final[float] = 2.0

# Suavizado Laplaciano
ITER_LAPLACIANO: Final[int] = 5
LAMBDA_LAPLACIANO: Final[float] = 0.5


@dataclass
class ResultadoPreProceso:
    """Malla pre-procesada con métricas de calidad."""
    malla_procesada: MallaImportada
    vertices_removidos_sor: int
    iteraciones_suavizado: int
    normal_plano_oclusal: np.ndarray   # shape (3,)
    traslacion_aplicada: np.ndarray    # shape (3,)
    rotacion_aplicada: np.ndarray      # shape (3, 3) matriz de rotación


def _malla_a_o3d(malla: MallaImportada) -> o3d.geometry.TriangleMesh:
    """Convierte MallaImportada a TriangleMesh de Open3D."""
    mesh = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(malla.vertices),
        o3d.utility.Vector3iVector(malla.caras),
    )
    mesh.compute_vertex_normals()
    return mesh


def _o3d_a_arrays(mesh: o3d.geometry.TriangleMesh) -> tuple[np.ndarray, np.ndarray]:
    """Extrae vértices y caras de TriangleMesh."""
    return (
        np.asarray(mesh.vertices, dtype=np.float64),
        np.asarray(mesh.triangles, dtype=np.int32),
    )


def aplicar_sor(malla: MallaImportada) -> tuple[MallaImportada, int]:
    """
    Statistical Outlier Removal: elimina puntos estadísticamente atípicos.
    Trabaja sobre la nube de puntos para detectar outliers y luego
    filtra las caras correspondientes.
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(malla.vertices)

    _, indices_validos = pcd.remove_statistical_outlier(
        nb_neighbors=NB_NEIGHBORS_SOR,
        std_ratio=STD_RATIO_SOR,
    )
    indices_validos_set = set(indices_validos)
    vertices_removidos = len(malla.vertices) - len(indices_validos)

    # Reindexar vértices y filtrar caras
    mapa_indices = {viejo: nuevo for nuevo, viejo in enumerate(indices_validos)}
    nuevos_vertices = malla.vertices[indices_validos]
    caras_validas = []
    for cara in malla.caras:
        if all(int(v) in indices_validos_set for v in cara):
            caras_validas.append([mapa_indices[int(v)] for v in cara])

    nueva_malla = MallaImportada(
        ruta_origen=malla.ruta_origen,
        formato=malla.formato,
        vertices=nuevos_vertices,
        caras=np.array(caras_validas, dtype=np.int32) if caras_validas else np.empty((0, 3), dtype=np.int32),
        unidad_mm=malla.unidad_mm,
        arcada=malla.arcada,
        hash_origen=malla.hash_origen,
        metadata={**malla.metadata, "sor_aplicado": True},
    )
    return nueva_malla, vertices_removidos


def aplicar_suavizado_laplaciano(malla: MallaImportada) -> MallaImportada:
    """Suavizado Laplaciano para reducir ruido de alta frecuencia."""
    mesh_o3d = _malla_a_o3d(malla)
    mesh_suavizado = mesh_o3d.filter_smooth_laplacian(
        number_of_iterations=ITER_LAPLACIANO,
        lambda_filter=LAMBDA_LAPLACIANO,
    )
    nuevos_vertices, nuevas_caras = _o3d_a_arrays(mesh_suavizado)
    return MallaImportada(
        ruta_origen=malla.ruta_origen,
        formato=malla.formato,
        vertices=nuevos_vertices,
        caras=nuevas_caras,
        unidad_mm=malla.unidad_mm,
        arcada=malla.arcada,
        hash_origen=malla.hash_origen,
        metadata={**malla.metadata, "suavizado_laplaciano": True},
    )


def _estimar_plano_oclusal(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Estima el plano oclusal mediante RANSAC sobre la nube de puntos.
    Retorna (normal, centroide_plano).
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(vertices)

    # RANSAC para encontrar el plano dominante (oclusal)
    plano_modelo, _ = pcd.segment_plane(
        distance_threshold=1.5,
        ransac_n=3,
        num_iterations=1000,
    )
    a, b, c, _ = plano_modelo
    normal = np.array([a, b, c], dtype=np.float64)
    normal /= np.linalg.norm(normal)
    centroide = np.mean(vertices, axis=0)
    return normal, centroide


def normalizar_plano_oclusal(malla: MallaImportada) -> tuple[MallaImportada, np.ndarray, np.ndarray, np.ndarray]:
    """
    Rota la malla para que el plano oclusal quede perpendicular al eje Z.

    Returns:
        (malla_normalizada, normal_plano, traslacion, rotacion)
    """
    normal_oclusal, centroide_plano = _estimar_plano_oclusal(malla.vertices)
    eje_z = np.array([0.0, 0.0, 1.0])

    # Calcular rotación de normal → eje Z
    eje_rotacion = np.cross(normal_oclusal, eje_z)
    norma_eje = np.linalg.norm(eje_rotacion)
    if norma_eje < 1e-6:
        # Ya alineado
        R = np.eye(3)
    else:
        eje_rotacion /= norma_eje
        angulo = float(np.arccos(np.clip(np.dot(normal_oclusal, eje_z), -1.0, 1.0)))
        # Rodrigues
        K = np.array([
            [0, -eje_rotacion[2], eje_rotacion[1]],
            [eje_rotacion[2], 0, -eje_rotacion[0]],
            [-eje_rotacion[1], eje_rotacion[0], 0],
        ])
        R = np.eye(3) + np.sin(angulo) * K + (1 - np.cos(angulo)) * (K @ K)

    # Aplicar traslación al origen + rotación
    vertices_centrados = malla.vertices - centroide_plano
    vertices_rotados = (R @ vertices_centrados.T).T

    nueva_malla = MallaImportada(
        ruta_origen=malla.ruta_origen,
        formato=malla.formato,
        vertices=vertices_rotados,
        caras=malla.caras.copy(),
        unidad_mm=malla.unidad_mm,
        arcada=malla.arcada,
        hash_origen=malla.hash_origen,
        metadata={**malla.metadata, "normalizado_oclusal": True},
    )
    return nueva_malla, normal_oclusal, centroide_plano, R


def preprocesar(malla: MallaImportada) -> ResultadoPreProceso:
    """
    RF-03: Pipeline completo de pre-procesamiento.
    1. SOR → 2. Suavizado Laplaciano → 3. Normalización plano oclusal.
    """
    malla_sor, n_removidos = aplicar_sor(malla)
    malla_suavizada = aplicar_suavizado_laplaciano(malla_sor)
    malla_norm, normal_oclusal, traslacion, rotacion = normalizar_plano_oclusal(malla_suavizada)

    return ResultadoPreProceso(
        malla_procesada=malla_norm,
        vertices_removidos_sor=n_removidos,
        iteraciones_suavizado=ITER_LAPLACIANO,
        normal_plano_oclusal=normal_oclusal,
        traslacion_aplicada=traslacion,
        rotacion_aplicada=rotacion,
    )
