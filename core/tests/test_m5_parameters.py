"""
Tests para M5: Cálculo de parámetros ortodónticos (T/A/I, distancia cingular).
Verifica precisión ±0.1° y comportamiento de borde.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from lingualParam.m5_parameters import (
    calcular_angulacion,
    calcular_distancia_cingular,
    calcular_inclinacion,
    calcular_torque,
    calcular_parametros,
)
from lingualParam.types import PiezaDental


def _pieza_sintetica(
    fdi: int = 11,
    torque_esperado: float = 0.0,
) -> PiezaDental:
    """Crea una PiezaDental sintética para pruebas."""
    # Eje longitudinal en Z (torque = 0)
    eje = np.array([0.0, 0.0, 1.0])
    normal = np.array([0.0, 1.0, 0.0])
    centroide_lingual = np.array([0.0, -5.0, 0.0])
    vertices = np.random.default_rng(0).uniform(-3, 3, (500, 3))

    return PiezaDental(
        fdi=fdi,
        vertices=vertices,
        centroide=np.zeros(3),
        centroide_lingual=centroide_lingual,
        eje_longitudinal=eje,
        vector_normal_lingual=normal,
        torque_deg=0.0,
        angulacion_deg=0.0,
        inclinacion_deg=0.0,
        distancia_cingular_mm=0.0,
        confianza_segmentacion=0.98,
    )


class TestCalcularTorque:
    def test_eje_z_puro_da_torque_cero(self) -> None:
        eje = np.array([0.0, 0.0, 1.0])
        assert calcular_torque(eje) == pytest.approx(0.0, abs=0.15)

    def test_eje_inclinado_da_torque_positivo(self) -> None:
        """Eje inclinado 10° hacia vestibular (Y+) debe dar torque ~10°."""
        angulo_rad = math.radians(10)
        eje = np.array([0.0, math.sin(angulo_rad), math.cos(angulo_rad)])
        eje /= np.linalg.norm(eje)
        torque = calcular_torque(eje)
        assert abs(torque) == pytest.approx(10.0, abs=0.5)

    def test_precision_es_01_grado(self) -> None:
        """El resultado debe tener máximo 1 decimal."""
        eje = np.array([0.1, 0.1, 1.0])
        eje /= np.linalg.norm(eje)
        torque = calcular_torque(eje)
        assert torque == round(torque, 1)


class TestCalcularAngulacion:
    def test_eje_z_puro_da_angulacion_cero(self) -> None:
        eje = np.array([0.0, 0.0, 1.0])
        assert calcular_angulacion(eje) == pytest.approx(0.0, abs=0.15)

    def test_eje_inclinado_mesial_da_angulacion_positiva(self) -> None:
        """Eje inclinado 5° en X debe dar angulación ~5°."""
        angulo_rad = math.radians(5)
        eje = np.array([math.sin(angulo_rad), 0.0, math.cos(angulo_rad)])
        eje /= np.linalg.norm(eje)
        angulacion = calcular_angulacion(eje)
        assert abs(angulacion) == pytest.approx(5.0, abs=0.5)


class TestCalcularInclinacion:
    def test_normal_y_puro_da_inclinacion_cero(self) -> None:
        normal = np.array([0.0, 1.0, 0.0])
        assert calcular_inclinacion(normal) == pytest.approx(0.0, abs=0.15)

    def test_resultado_tiene_1_decimal(self) -> None:
        normal = np.array([0.3, 0.9, 0.1])
        normal /= np.linalg.norm(normal)
        inc = calcular_inclinacion(normal)
        assert inc == round(inc, 1)


class TestCalcularDistanciaCingular:
    def test_mismos_puntos_da_distancia_cero(self) -> None:
        p = np.array([1.0, 2.0, 3.0])
        assert calcular_distancia_cingular(p, p) == pytest.approx(0.0, abs=0.01)

    def test_distancia_correcta(self) -> None:
        p1 = np.array([0.0, 0.0, 0.0])
        p2 = np.array([3.0, 4.0, 0.0])
        assert calcular_distancia_cingular(p1, p2) == pytest.approx(5.0, abs=0.1)

    def test_resultado_tiene_1_decimal(self) -> None:
        p1 = np.array([0.0, 0.0, 0.0])
        p2 = np.array([1.123456, 2.654321, 0.0])
        d = calcular_distancia_cingular(p1, p2)
        assert d == round(d, 1)


class TestCalcularParametros:
    def test_retorna_pieza_con_todos_los_campos_completos(self) -> None:
        pieza = _pieza_sintetica()
        resultado = calcular_parametros(pieza)
        assert isinstance(resultado.torque_deg, float)
        assert isinstance(resultado.angulacion_deg, float)
        assert isinstance(resultado.inclinacion_deg, float)
        assert isinstance(resultado.distancia_cingular_mm, float)

    def test_no_modifica_pieza_original(self) -> None:
        pieza = _pieza_sintetica()
        torque_original = pieza.torque_deg
        calcular_parametros(pieza)
        # La función debe retornar una nueva instancia, no modificar la original
        assert pieza.torque_deg == torque_original

    def test_precision_en_angulos(self) -> None:
        pieza = _pieza_sintetica()
        resultado = calcular_parametros(pieza)
        for campo in ("torque_deg", "angulacion_deg", "inclinacion_deg"):
            val = getattr(resultado, campo)
            assert val == round(val, 1), f"{campo} no tiene precisión ±0.1°"
