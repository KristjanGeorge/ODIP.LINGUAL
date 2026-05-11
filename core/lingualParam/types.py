"""
Contratos de tipo entre módulos LingualParam-CSM™.
Todos los módulos M1-M10 importan desde aquí.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import numpy as np


class EstadoCaso(str, Enum):
    IMPORTADO = "importado"
    PROCESADO = "procesado"
    APROBADO = "aprobado"
    EXPORTADO = "exportado"


class TipoPrescripcion(str, Enum):
    STB = "STb"
    WIECHMANN_2D = "2D"
    WIN = "WIN"
    PERSONALIZADA = "personalizada"


class FormatoArchivo(str, Enum):
    STL = "stl"
    PLY = "ply"
    OBJ = "obj"
    DCM = "dcm"


class TipoArcada(str, Enum):
    SUPERIOR = "superior"
    INFERIOR = "inferior"
    AMBAS = "ambas"


class TipoEvento(str, Enum):
    IMPORTACION = "importacion"
    PROCESAMIENTO = "procesamiento"
    AJUSTE_MANUAL = "ajuste_manual"
    EXPORTACION = "exportacion"
    CONSULTA = "consulta"
    ERROR = "error"


@dataclass
class MallaImportada:
    """Resultado de M1: malla 3D validada y lista para procesar."""
    ruta_origen: str
    formato: str          # stl | ply | obj | dcm
    vertices: np.ndarray  # shape (N, 3) float64, unidades mm
    caras: np.ndarray     # shape (M, 3) int32
    unidad_mm: bool
    arcada: str           # superior | inferior | ambas
    hash_origen: str      # SHA-256 del archivo original
    metadata: dict = field(default_factory=dict)


@dataclass
class PiezaDental:
    """Pieza individual segmentada con sus parámetros geométricos."""
    fdi: int                              # número FDI (11, 12, ..., 47)
    vertices: np.ndarray                  # shape (N, 3)
    centroide: np.ndarray                 # shape (3,) centroide global
    centroide_lingual: np.ndarray         # shape (3,) zona cingular
    eje_longitudinal: np.ndarray          # shape (3,) vector unitario PCA eje mayor
    vector_normal_lingual: np.ndarray     # shape (3,) normal promedio zona lingual
    torque_deg: float                     # rotación eje Z, precisión ±0.1°
    angulacion_deg: float                 # rotación eje Y, precisión ±0.1°
    inclinacion_deg: float                # rotación eje X, precisión ±0.1°
    distancia_cingular_mm: float          # distancia borde bracket ↔ cíngulo
    confianza_segmentacion: float         # 0.0 – 1.0


@dataclass
class ValoresPrescripcion:
    """Valores objetivo por pieza FDI según una prescripción estándar."""
    fdi: int
    torque_objetivo_deg: float
    angulacion_objetivo_deg: float
    inclinacion_objetivo_deg: float


@dataclass
class PrescripcionCompleta:
    """Prescripción completa con metadatos."""
    nombre: str
    tipo: TipoPrescripcion
    descripcion: str
    referencia_bibliografica: str
    piezas: list[ValoresPrescripcion] = field(default_factory=list)


@dataclass
class GeometriaBracket:
    """Resultado de M7: geometría individualizada del bracket."""
    fdi: int
    grosor_base_mm: float      # grosor de la base (pad) del bracket
    angulo_slot_deg: float     # ángulo del slot respecto a la base
    ancho_bracket_mm: float    # ancho mesiodistal
    alto_bracket_mm: float     # alto oclusogingival
    radio_base_mm: float       # radio de curvatura de la base


@dataclass
class ResultadoCalculo:
    """Resultado final por pieza: parámetros medidos + delta vs. prescripción."""
    pieza: PiezaDental
    prescripcion_fdi: int
    delta_t: float             # ΔTorque  = objetivo − actual
    delta_a: float             # ΔAngulación
    delta_i: float             # ΔInclinación
    grosor_base_mm: float
    angulo_slot_deg: float
    ajuste_manual: bool = False
    justificacion_ajuste: str = ""
    bracket: Optional[GeometriaBracket] = None


@dataclass
class ResultadoProcesamiento:
    """Resultado completo del pipeline M1-M8 para un caso."""
    id_caso: str
    estado: EstadoCaso
    malla: MallaImportada
    piezas: list[ResultadoCalculo] = field(default_factory=list)
    prescripcion: Optional[PrescripcionCompleta] = None
    hash_dataset: str = ""
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


@dataclass
class EventoBitacora:
    """Registro de auditoría cifrado."""
    tipo: TipoEvento
    autor: str
    id_caso: Optional[str]
    descripcion: str
    payload: dict = field(default_factory=dict)
