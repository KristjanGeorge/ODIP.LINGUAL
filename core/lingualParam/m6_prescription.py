"""
M6: Gestión de prescripciones ortodónticas.
Carga STb, 2D Wiechmann, WIN y prescripciones personalizadas.
Calcula deltas de corrección. RF-12, RF-13, RF-24.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from lingualParam.types import (
    PiezaDental,
    PrescripcionCompleta,
    ResultadoCalculo,
    TipoPrescripcion,
    ValoresPrescripcion,
)

# Directorio de prescripciones incluidas en el paquete
_DIR_PRESCRIPCIONES = Path(__file__).parent.parent.parent / "prescriptions"


class ErrorPrescripcion(Exception):
    """Error al cargar o aplicar una prescripción."""


def _ruta_prescripcion(tipo: TipoPrescripcion) -> Path:
    """Retorna la ruta del archivo JSON para la prescripción estándar."""
    mapeo = {
        TipoPrescripcion.STB: "STb.json",
        TipoPrescripcion.WIECHMANN_2D: "2D_Wiechmann.json",
        TipoPrescripcion.WIN: "WIN_WildSmile.json",
    }
    nombre = mapeo.get(tipo)
    if nombre is None:
        raise ErrorPrescripcion(f"Prescripción '{tipo}' no tiene archivo predefinido.")
    return _DIR_PRESCRIPCIONES / nombre


def cargar_prescripcion_json(ruta: Union[str, Path]) -> PrescripcionCompleta:
    """
    RF-12: Carga una prescripción desde un archivo JSON.
    El JSON debe seguir el schema: {nombre, tipo, descripcion, referencia, piezas: [{fdi, T, A, I}]}.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorPrescripcion(f"Archivo de prescripción no encontrado: {ruta}")

    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)

    piezas = [
        ValoresPrescripcion(
            fdi=int(p["fdi"]),
            torque_objetivo_deg=float(p["T"]),
            angulacion_objetivo_deg=float(p["A"]),
            inclinacion_objetivo_deg=float(p["I"]),
        )
        for p in datos.get("piezas", [])
    ]

    tipo_str = datos.get("tipo", "personalizada")
    try:
        tipo = TipoPrescripcion(tipo_str)
    except ValueError:
        tipo = TipoPrescripcion.PERSONALIZADA

    return PrescripcionCompleta(
        nombre=datos.get("nombre", ruta.stem),
        tipo=tipo,
        descripcion=datos.get("descripcion", ""),
        referencia_bibliografica=datos.get("referencia", ""),
        piezas=piezas,
    )


def cargar_prescripcion_estandar(tipo: TipoPrescripcion) -> PrescripcionCompleta:
    """RF-12: Carga una prescripción estándar (STb, 2D, WIN)."""
    ruta = _ruta_prescripcion(tipo)
    return cargar_prescripcion_json(ruta)


def obtener_valores_para_pieza(
    prescripcion: PrescripcionCompleta,
    fdi: int,
) -> Optional[ValoresPrescripcion]:
    """Busca los valores de la prescripción para una pieza FDI específica."""
    for p in prescripcion.piezas:
        if p.fdi == fdi:
            return p
    return None


def calcular_deltas(
    pieza: PiezaDental,
    valores_obj: ValoresPrescripcion,
) -> tuple[float, float, float]:
    """
    RF-13: Calcula las diferencias de corrección.
    ΔT = objetivo − actual, ΔA = objetivo − actual, ΔI = objetivo − actual.
    Precisión ±0.1°.
    """
    delta_t = round(valores_obj.torque_objetivo_deg - pieza.torque_deg, 1)
    delta_a = round(valores_obj.angulacion_objetivo_deg - pieza.angulacion_deg, 1)
    delta_i = round(valores_obj.inclinacion_objetivo_deg - pieza.inclinacion_deg, 1)
    return delta_t, delta_a, delta_i


def aplicar_prescripcion(
    pieza: PiezaDental,
    prescripcion: PrescripcionCompleta,
    grosor_base_estandar_mm: float = 0.5,
    angulo_slot_estandar_deg: float = 0.0,
) -> ResultadoCalculo:
    """
    RF-12 + RF-13: Aplica la prescripción a una pieza y genera el ResultadoCalculo.
    Si la pieza no está en la prescripción, usa valores neutros (0°).
    """
    valores_obj = obtener_valores_para_pieza(prescripcion, pieza.fdi)

    if valores_obj is None:
        valores_obj = ValoresPrescripcion(
            fdi=pieza.fdi,
            torque_objetivo_deg=0.0,
            angulacion_objetivo_deg=0.0,
            inclinacion_objetivo_deg=0.0,
        )

    delta_t, delta_a, delta_i = calcular_deltas(pieza, valores_obj)

    return ResultadoCalculo(
        pieza=pieza,
        prescripcion_fdi=pieza.fdi,
        delta_t=delta_t,
        delta_a=delta_a,
        delta_i=delta_i,
        grosor_base_mm=grosor_base_estandar_mm,
        angulo_slot_deg=angulo_slot_estandar_deg + delta_t,
    )


def guardar_prescripcion_personalizada(
    prescripcion: PrescripcionCompleta,
    ruta_destino: Union[str, Path],
) -> None:
    """RF-24: Guarda una prescripción personalizada en formato JSON."""
    ruta_destino = Path(ruta_destino)
    datos = {
        "nombre": prescripcion.nombre,
        "tipo": prescripcion.tipo.value,
        "descripcion": prescripcion.descripcion,
        "referencia": prescripcion.referencia_bibliografica,
        "piezas": [
            {
                "fdi": p.fdi,
                "T": p.torque_objetivo_deg,
                "A": p.angulacion_objetivo_deg,
                "I": p.inclinacion_objetivo_deg,
            }
            for p in prescripcion.piezas
        ],
    }
    with open(ruta_destino, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
