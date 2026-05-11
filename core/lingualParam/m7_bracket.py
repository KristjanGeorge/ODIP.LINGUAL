"""
M7: Cálculo de geometría bracket individualizada.
Stub pybind11 con fallback Python puro. RF-14.
El módulo C++17 compilado se llama bracket_geom.so / bracket_geom.pyd.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

from lingualParam.types import GeometriaBracket, ResultadoCalculo

logger = logging.getLogger(__name__)

# Parámetros geométricos base del bracket lingual (valores clínicos estándar)
GROSOR_BASE_MINIMO_MM: float = 0.3
GROSOR_BASE_MAXIMO_MM: float = 1.2
ANCHO_BRACKET_BASE_MM: float = 3.5
ALTO_BRACKET_BASE_MM: float = 2.8
RADIO_BASE_REFERENCIA_MM: float = 12.0  # radio de curvatura del arco dental medio

# Factor de corrección entre ΔTorque y grosor base (mm por grado)
FACTOR_GROSOR_POR_GRADO: float = 0.01


def _intentar_cargar_modulo_cpp() -> Optional[object]:
    """
    Intenta importar el módulo C++17 compilado con pybind11.
    Retorna el módulo o None si no está disponible.
    """
    try:
        import bracket_geom  # type: ignore[import]
        logger.info("Módulo C++17 bracket_geom cargado correctamente.")
        return bracket_geom
    except ImportError:
        logger.warning(
            "Módulo bracket_geom (C++17) no disponible; usando implementación Python."
        )
        return None


_MODULO_CPP = _intentar_cargar_modulo_cpp()


def _grosor_base_desde_delta(delta_t: float, distancia_cingular_mm: float) -> float:
    """
    Calcula el grosor de la base del bracket en función del ΔTorque.
    Mayor ΔT positivo → mayor grosor (más material de compensación).
    """
    grosor = 0.5 + FACTOR_GROSOR_POR_GRADO * abs(delta_t) + 0.02 * distancia_cingular_mm
    return round(min(GROSOR_BASE_MAXIMO_MM, max(GROSOR_BASE_MINIMO_MM, grosor)), 2)


def _angulo_slot_desde_delta(delta_t: float) -> float:
    """
    Ángulo del slot del bracket respecto a la base.
    El slot ya trae el ΔTorque incorporado.
    """
    return round(delta_t, 1)


def _radio_base_individual(fdi: int) -> float:
    """
    Estima el radio de curvatura de la base según la posición de la pieza
    (piezas anteriores tienen radio mayor, posteriores menor).
    FDI 11-13 / 21-23 / 31-33 / 41-43 → radio más grande.
    """
    posicion = fdi % 10  # 1..7
    radio = RADIO_BASE_REFERENCIA_MM - (posicion - 1) * 1.5
    return round(max(radio, 6.0), 1)


def calcular_geometria_cpp(resultado: ResultadoCalculo) -> GeometriaBracket:
    """Usa el módulo C++17 si está disponible."""
    assert _MODULO_CPP is not None
    geom = _MODULO_CPP.calcular_bracket(  # type: ignore[union-attr]
        fdi=resultado.pieza.fdi,
        delta_t=resultado.delta_t,
        delta_a=resultado.delta_a,
        delta_i=resultado.delta_i,
        distancia_cingular_mm=resultado.pieza.distancia_cingular_mm,
    )
    return GeometriaBracket(
        fdi=resultado.pieza.fdi,
        grosor_base_mm=float(geom.grosor_base_mm),
        angulo_slot_deg=float(geom.angulo_slot_deg),
        ancho_bracket_mm=float(geom.ancho_bracket_mm),
        alto_bracket_mm=float(geom.alto_bracket_mm),
        radio_base_mm=float(geom.radio_base_mm),
    )


def calcular_geometria_python(resultado: ResultadoCalculo) -> GeometriaBracket:
    """Implementación Python pura como fallback de C++17."""
    fdi = resultado.pieza.fdi
    grosor_base = _grosor_base_desde_delta(
        resultado.delta_t, resultado.pieza.distancia_cingular_mm
    )
    angulo_slot = _angulo_slot_desde_delta(resultado.delta_t)
    radio_base = _radio_base_individual(fdi)

    # Ancho mesiodistal: anterior 3.5 mm, posterior 4.2 mm
    posicion = fdi % 10
    ancho = 3.5 if posicion <= 3 else 4.2

    return GeometriaBracket(
        fdi=fdi,
        grosor_base_mm=grosor_base,
        angulo_slot_deg=angulo_slot,
        ancho_bracket_mm=round(ancho, 1),
        alto_bracket_mm=ALTO_BRACKET_BASE_MM,
        radio_base_mm=radio_base,
    )


def calcular_geometria_bracket(resultado: ResultadoCalculo) -> GeometriaBracket:
    """
    RF-14: Calcula la geometría individualizada del bracket.
    Usa C++17 si está disponible; Python puro como fallback.
    """
    if _MODULO_CPP is not None:
        return calcular_geometria_cpp(resultado)
    return calcular_geometria_python(resultado)
