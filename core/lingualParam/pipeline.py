"""
Orquestador del pipeline M1-M8.
Coordina la ejecución secuencial de los módulos y genera el ResultadoProcesamiento.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from lingualParam import m1_importer, m2_preprocessor, m3_segmenter, m4_geometry
from lingualParam import m5_parameters, m6_prescription, m7_bracket, m8_exporter
from lingualParam.types import (
    EstadoCaso,
    ResultadoCalculo,
    ResultadoProcesamiento,
    TipoPrescripcion,
)

logger = logging.getLogger(__name__)


def ejecutar_pipeline(
    ruta_archivo: str,
    tipo_prescripcion: TipoPrescripcion = TipoPrescripcion.STB,
    ruta_prescripcion_personalizada: Optional[str] = None,
    ruta_modelo_cnn: Optional[str] = None,
    id_caso: Optional[str] = None,
) -> ResultadoProcesamiento:
    """
    Pipeline completo M1 → M8.

    Args:
        ruta_archivo: Ruta al archivo 3D (.stl, .ply, .obj, .dcm).
        tipo_prescripcion: Prescripción estándar a aplicar.
        ruta_prescripcion_personalizada: Si no es None, sobreescribe tipo_prescripcion.
        ruta_modelo_cnn: Ruta al modelo CNN serializado (opcional).
        id_caso: ID único del caso; se genera uno si no se provee.

    Returns:
        ResultadoProcesamiento con todos los resultados.
    """
    _id_caso = id_caso or str(uuid.uuid4())
    errores: list[str] = []
    advertencias: list[str] = []

    # M1: Importar
    logger.info("[M1] Importando archivo: %s", ruta_archivo)
    try:
        malla = m1_importer.importar_archivo(ruta_archivo)
    except m1_importer.ErrorImportacion as exc:
        return ResultadoProcesamiento(
            id_caso=_id_caso,
            estado=EstadoCaso.IMPORTADO,
            malla=None,  # type: ignore[arg-type]
            errores=[str(exc)],
        )

    # M2: Pre-procesar
    logger.info("[M2] Pre-procesando malla.")
    resultado_preproceso = m2_preprocessor.preprocesar(malla)
    malla_procesada = resultado_preproceso.malla_procesada
    if resultado_preproceso.vertices_removidos_sor > 0:
        advertencias.append(
            f"SOR eliminó {resultado_preproceso.vertices_removidos_sor} vértices atípicos."
        )

    # M3: Segmentar
    logger.info("[M3] Segmentando piezas dentales.")
    segmentos = m3_segmenter.segmentar(malla_procesada, ruta_modelo_cnn)
    logger.info("[M3] %d piezas detectadas.", len(segmentos))

    # M4 + M5: Geometría y parámetros por pieza
    logger.info("[M4+M5] Calculando geometría y parámetros.")
    piezas_calculadas: list[ResultadoCalculo] = []

    # M6: Cargar prescripción
    logger.info("[M6] Cargando prescripción: %s", tipo_prescripcion)
    if ruta_prescripcion_personalizada:
        prescripcion = m6_prescription.cargar_prescripcion_json(ruta_prescripcion_personalizada)
    else:
        prescripcion = m6_prescription.cargar_prescripcion_estandar(tipo_prescripcion)

    for segmento in segmentos:
        try:
            # M4: Geometría
            pieza_base = m4_geometry.calcular_geometria_pieza(
                segmento, arcada=malla_procesada.arcada
            )
            # M5: Parámetros T/A/I
            pieza_con_params = m5_parameters.calcular_parametros(pieza_base)
            # M6: Prescripción + deltas
            resultado = m6_prescription.aplicar_prescripcion(pieza_con_params, prescripcion)
            # M7: Geometría bracket
            bracket = m7_bracket.calcular_geometria_bracket(resultado)
            resultado.bracket = bracket
            resultado.grosor_base_mm = bracket.grosor_base_mm
            resultado.angulo_slot_deg = bracket.angulo_slot_deg
            piezas_calculadas.append(resultado)
        except Exception as exc:
            msg = f"Error en pieza FDI {segmento.fdi}: {exc}"
            logger.error(msg)
            errores.append(msg)

    procesamiento = ResultadoProcesamiento(
        id_caso=_id_caso,
        estado=EstadoCaso.PROCESADO,
        malla=malla_procesada,
        piezas=piezas_calculadas,
        prescripcion=prescripcion,
        errores=errores,
        advertencias=advertencias,
    )

    logger.info(
        "[Pipeline] Caso %s procesado: %d piezas, %d errores.",
        _id_caso, len(piezas_calculadas), len(errores),
    )
    return procesamiento
