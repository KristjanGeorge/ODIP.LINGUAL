"""
Tests para M4: Cálculo geométrico (PCA, centroide lingual, vector normal).
"""
from __future__ import annotations

import numpy as np
import pytest

from lingualParam.m4_geometry import (
    calcular_centroide_lingual,
    calcular_eje_longitudinal,
    calcular_vector_normal_lingual,
)


def _corona_sintetica(
    alto_mm: float = 10.0,
    ancho_mm: float = 6.0,
    n_puntos: int = 500,
    seed: int = 42,
) -> np.ndarray:
    """Genera una nube de puntos que simula una corona dental (elipsoide)."""
    rng = np.random.default_rng(seed)
    # Elipsoide: eje Z mayor (longitudinal), XY menores
    theta = rng.uniform(0, 2 * np.pi, n_puntos)
    phi = rng.uniform(0, np.pi, n_puntos)
    x = (ancho_mm / 2) * np.sin(phi) * np.cos(theta)
    y = (ancho_mm / 2) * np.sin(phi) * np.sin(theta)
    z = (alto_mm / 2) * np.cos(phi)
    return np.column_stack([x, y, z])


class TestCalcularEjeLongitudinal:
    def test_eje_apunta_en_z_para_corona_vertical(self) -> None:
        """Una corona orientada verticalmente debe tener eje ~[0, 0, 1]."""
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        assert eje.shape == (3,)
        # El eje Z debe dominar (componente Z > 0.8)
        assert abs(eje[2]) > 0.8

    def test_eje_es_vector_unitario(self) -> None:
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        assert abs(np.linalg.norm(eje) - 1.0) < 1e-6

    def test_eje_z_positivo_por_convencion(self) -> None:
        """Convención: el eje siempre apunta hacia +Z (oclusal)."""
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        assert eje[2] >= 0

    def test_pocos_vertices_retorna_eje_default(self) -> None:
        """Menos de 3 vértices → retorna [0, 0, 1] por defecto."""
        vertices = np.zeros((2, 3))
        eje = calcular_eje_longitudinal(vertices)
        np.testing.assert_array_equal(eje, [0.0, 0.0, 1.0])


class TestCalcularCentroideLingual:
    def test_centroide_lingual_esta_en_zona_palatina(self) -> None:
        """Para arcada superior, el centroide lingual debe tener Y < 0."""
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        centroide = calcular_centroide_lingual(vertices, eje, arcada="superior")
        assert centroide.shape == (3,)
        # Zona palatina: Y negativo
        assert centroide[1] < 0

    def test_centroide_lingual_inferior_tiene_y_positivo(self) -> None:
        """Para arcada inferior, el centroide lingual debe tener Y > 0."""
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        centroide = calcular_centroide_lingual(vertices, eje, arcada="inferior")
        assert centroide[1] > 0

    def test_centroide_en_zona_gingival(self) -> None:
        """El centroide cingular debe estar en el 30% inferior del rango Z."""
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        centroide = calcular_centroide_lingual(vertices, eje)
        z_min = vertices[:, 2].min()
        z_max = vertices[:, 2].max()
        umbral_30 = z_min + 0.30 * (z_max - z_min)
        assert centroide[2] <= umbral_30 + 0.1  # tolerancia pequeña


class TestCalcularVectorNormalLingual:
    def test_normal_es_vector_unitario(self) -> None:
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        centroide_lingual = calcular_centroide_lingual(vertices, eje)
        normal = calcular_vector_normal_lingual(vertices, centroide_lingual)
        assert abs(np.linalg.norm(normal) - 1.0) < 1e-5

    def test_normal_tiene_forma_correcta(self) -> None:
        vertices = _corona_sintetica()
        eje = calcular_eje_longitudinal(vertices)
        centroide_lingual = calcular_centroide_lingual(vertices, eje)
        normal = calcular_vector_normal_lingual(vertices, centroide_lingual)
        assert normal.shape == (3,)

    def test_normal_no_es_cero(self) -> None:
        vertices = _corona_sintetica(n_puntos=1000)
        eje = calcular_eje_longitudinal(vertices)
        centroide_lingual = calcular_centroide_lingual(vertices, eje)
        normal = calcular_vector_normal_lingual(vertices, centroide_lingual)
        assert np.linalg.norm(normal) > 0.5
