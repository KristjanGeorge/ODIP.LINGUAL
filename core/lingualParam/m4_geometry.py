"""
M4: Cálculo geométrico por pieza dental.
PCA para eje longitudinal, centroide lingual (zona cingular), vector normal lingual.
RF-05, RF-06, RF-07.
"""
from __future__ import annotations

import numpy as np
import open3d as o3d
from sklearn.decomposition import PCA

from lingualParam.m3_segmenter import SegmentoFDI
from lingualParam.types import PiezaDental

# Fracción gingival para definir zona cingular (20% ocluso-gingival)
FRACCION_CINGULAR: float = 0.20
# Radio de búsqueda para promedio de normales (mm)
RADIO_NORMAL_MM: float = 3.0
# Número de vecinos para estimación de normales
K_VECINOS_NORMAL: int = 30


def calcular_eje_longitudinal(vertices: np.ndarray) -> np.ndarray:
    """
    RF-05: Calcula el eje longitudinal mediante PCA.
    El primer componente principal (eje mayor de varianza) corresponde al
    eje longitudinal de la corona.

    Args:
        vertices: shape (N, 3).

    Returns:
        Vector unitario del eje longitudinal, shape (3,).
    """
    if len(vertices) < 3:
        return np.array([0.0, 0.0, 1.0])

    pca = PCA(n_components=3)
    pca.fit(vertices)
    eje = pca.components_[0]  # componente de mayor varianza

    # Convención: el eje apunta hacia oclusal (+Z)
    if eje[2] < 0:
        eje = -eje

    return eje / np.linalg.norm(eje)


def _seleccionar_zona_cingular(
    vertices: np.ndarray,
    eje: np.ndarray,
    fraccion: float = FRACCION_CINGULAR,
) -> np.ndarray:
    """
    Selecciona la zona cingular: el 20% gingival de la corona proyectado
    sobre el eje longitudinal.
    """
    proyecciones = vertices @ eje
    p_min, p_max = proyecciones.min(), proyecciones.max()
    umbral = p_min + fraccion * (p_max - p_min)
    mascara = proyecciones <= umbral
    return vertices[mascara]


def _seleccionar_cara_lingual(vertices: np.ndarray, arcada: str) -> np.ndarray:
    """
    Filtra la cara lingual de la corona.
    Para arcada superior: la cara lingual apunta hacia –Y (palatino).
    Para arcada inferior: la cara lingual apunta hacia +Y (lingual).
    """
    centroide = vertices.mean(axis=0)
    if arcada == "superior":
        # Cara palatina: Y < centroide_Y
        mascara = vertices[:, 1] < centroide[1]
    else:
        # Cara lingual inferior: Y > centroide_Y
        mascara = vertices[:, 1] > centroide[1]
    resultado = vertices[mascara]
    return resultado if len(resultado) > 10 else vertices


def calcular_centroide_lingual(
    vertices: np.ndarray,
    eje_longitudinal: np.ndarray,
    arcada: str = "superior",
) -> np.ndarray:
    """
    RF-06: Calcula el centroide lingual en la zona cingular.
    1. Filtra la cara lingual.
    2. Selecciona la zona cingular (20% gingival).
    3. Retorna el centroide de esos puntos.

    Args:
        vertices: shape (N, 3).
        eje_longitudinal: vector unitario del eje PCA, shape (3,).
        arcada: 'superior' o 'inferior'.

    Returns:
        Centroide lingual, shape (3,).
    """
    cara_lingual = _seleccionar_cara_lingual(vertices, arcada)
    zona_cingular = _seleccionar_zona_cingular(cara_lingual, eje_longitudinal)

    if len(zona_cingular) < 5:
        zona_cingular = cara_lingual

    return zona_cingular.mean(axis=0)


def calcular_vector_normal_lingual(
    vertices: np.ndarray,
    centroide_lingual: np.ndarray,
    radio_mm: float = RADIO_NORMAL_MM,
) -> np.ndarray:
    """
    RF-07: Estima el vector normal en la cara lingual.
    1. Construye nube de puntos con Open3D.
    2. Estima normales con KNN.
    3. Promedia las normales en la vecindad del centroide lingual.

    Args:
        vertices: shape (N, 3).
        centroide_lingual: shape (3,).
        radio_mm: radio de búsqueda en mm.

    Returns:
        Vector normal unitario, shape (3,).
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(vertices)
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamKNN(knn=K_VECINOS_NORMAL)
    )
    # Orientar normales consistentemente hacia afuera
    pcd.orient_normals_consistent_tangent_plane(k=K_VECINOS_NORMAL)

    normales = np.asarray(pcd.normals, dtype=np.float64)
    distancias = np.linalg.norm(vertices - centroide_lingual, axis=1)
    vecinos = distancias < radio_mm

    if vecinos.sum() < 3:
        # Ampliar radio si no hay suficientes vecinos
        vecinos = distancias < radio_mm * 3

    if vecinos.sum() == 0:
        return np.array([0.0, -1.0, 0.0])

    normal_promedio = normales[vecinos].mean(axis=0)
    norma = np.linalg.norm(normal_promedio)
    if norma < 1e-8:
        return np.array([0.0, -1.0, 0.0])
    return normal_promedio / norma


def calcular_geometria_pieza(
    segmento: SegmentoFDI,
    arcada: str = "superior",
    torque_deg: float = 0.0,
    angulacion_deg: float = 0.0,
    inclinacion_deg: float = 0.0,
    distancia_cingular_mm: float = 0.0,
) -> PiezaDental:
    """
    RF-05, RF-06, RF-07: Calcula todos los vectores geométricos de una pieza.
    Los ángulos T/A/I se completan en M5; aquí se pasan en 0.0 por defecto.
    """
    v = segmento.vertices
    centroide_global = v.mean(axis=0)
    eje = calcular_eje_longitudinal(v)
    centroide_lingual = calcular_centroide_lingual(v, eje, arcada)
    normal_lingual = calcular_vector_normal_lingual(v, centroide_lingual)

    return PiezaDental(
        fdi=segmento.fdi,
        vertices=v,
        centroide=centroide_global,
        centroide_lingual=centroide_lingual,
        eje_longitudinal=eje,
        vector_normal_lingual=normal_lingual,
        torque_deg=torque_deg,
        angulacion_deg=angulacion_deg,
        inclinacion_deg=inclinacion_deg,
        distancia_cingular_mm=distancia_cingular_mm,
        confianza_segmentacion=segmento.confianza,
    )
