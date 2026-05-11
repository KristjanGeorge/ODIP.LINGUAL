"""
M5: Cálculo de parámetros ortodónticos (Torque, Angulación, Inclinación, distancia cingular).
Precisión ±0.1°. RF-08, RF-09, RF-10, RF-11.
"""
from __future__ import annotations

import math
from typing import Final

import numpy as np

from lingualParam.types import PiezaDental

# Ejes de referencia del sistema de coordenadas oclusal normalizado
EJE_X: Final[np.ndarray] = np.array([1.0, 0.0, 0.0])  # mesiodistal
EJE_Y: Final[np.ndarray] = np.array([0.0, 1.0, 0.0])  # vestíbulo-lingual
EJE_Z: Final[np.ndarray] = np.array([0.0, 0.0, 1.0])  # ocluso-gingival

PRECISION_DECIMAL: Final[int] = 1  # ±0.1°


def _rad_a_grados(rad: float) -> float:
    """Convierte radianes a grados con precisión ±0.1°."""
    return round(math.degrees(rad), PRECISION_DECIMAL)


def _angulo_entre_vectores_en_plano(
    v: np.ndarray,
    referencia: np.ndarray,
    normal_plano: np.ndarray,
) -> float:
    """
    Calcula el ángulo con signo entre v y referencia proyectados sobre
    el plano definido por normal_plano.

    Returns:
        Ángulo en grados [-180, 180].
    """
    # Proyectar sobre el plano
    def proyectar(vec: np.ndarray) -> np.ndarray:
        return vec - np.dot(vec, normal_plano) * normal_plano

    v_proy = proyectar(v)
    ref_proy = proyectar(referencia)

    n_v = np.linalg.norm(v_proy)
    n_r = np.linalg.norm(ref_proy)
    if n_v < 1e-8 or n_r < 1e-8:
        return 0.0

    v_proy /= n_v
    ref_proy /= n_r

    cos_ang = np.clip(np.dot(v_proy, ref_proy), -1.0, 1.0)
    angulo = math.acos(cos_ang)

    # Signo mediante el producto cruzado
    cruz = np.cross(ref_proy, v_proy)
    if np.dot(cruz, normal_plano) < 0:
        angulo = -angulo

    return _rad_a_grados(angulo)


def calcular_torque(eje_longitudinal: np.ndarray) -> float:
    """
    RF-08: Torque — rotación del eje longitudinal en el plano vestíbulo-lingual
    (plano YZ), medida respecto al eje Z.
    Positivo = inclinación vestibular de la corona.
    """
    return _angulo_entre_vectores_en_plano(eje_longitudinal, EJE_Z, EJE_X)


def calcular_angulacion(eje_longitudinal: np.ndarray) -> float:
    """
    RF-09: Angulación — inclinación mesiodistal del eje longitudinal en el
    plano XZ, medida respecto al eje Z.
    Positivo = cara mesial inclinada hacia oclusal.
    """
    return _angulo_entre_vectores_en_plano(eje_longitudinal, EJE_Z, EJE_Y)


def calcular_inclinacion(vector_normal_lingual: np.ndarray) -> float:
    """
    RF-10: Inclinación — ángulo del vector normal lingual respecto al plano
    oclusal (plano XY). Medida en el plano sagital (XZ).
    Positivo = normal apunta hacia vestibular.
    """
    return _angulo_entre_vectores_en_plano(vector_normal_lingual, EJE_Y, EJE_X)


def calcular_distancia_cingular(
    centroide_lingual: np.ndarray,
    borde_bracket_referencia: np.ndarray,
) -> float:
    """
    RF-11: Distancia cingular en mm — distancia euclidiana entre el centroide
    lingual (zona cingular) y el punto de referencia del bracket.

    En la primera iteración, el borde_bracket_referencia se estima como
    centroide_lingual + offset estándar de 0.8 mm hacia oclusal.
    """
    return round(float(np.linalg.norm(centroide_lingual - borde_bracket_referencia)), PRECISION_DECIMAL)


def calcular_parametros(pieza: PiezaDental) -> PiezaDental:
    """
    RF-08..RF-11: Calcula todos los parámetros de la pieza y retorna
    una nueva instancia con los campos completados.
    """
    torque = calcular_torque(pieza.eje_longitudinal)
    angulacion = calcular_angulacion(pieza.eje_longitudinal)
    inclinacion = calcular_inclinacion(pieza.vector_normal_lingual)

    # Estimación del borde del bracket: 0.8 mm hacia oclusal desde el centroide lingual
    borde_bracket = pieza.centroide_lingual + np.array([0.0, 0.0, 0.8])
    distancia_cingular = calcular_distancia_cingular(pieza.centroide_lingual, borde_bracket)

    return PiezaDental(
        fdi=pieza.fdi,
        vertices=pieza.vertices,
        centroide=pieza.centroide,
        centroide_lingual=pieza.centroide_lingual,
        eje_longitudinal=pieza.eje_longitudinal,
        vector_normal_lingual=pieza.vector_normal_lingual,
        torque_deg=torque,
        angulacion_deg=angulacion,
        inclinacion_deg=inclinacion,
        distancia_cingular_mm=distancia_cingular,
        confianza_segmentacion=pieza.confianza_segmentacion,
    )
