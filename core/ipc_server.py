"""
Servidor IPC FastAPI para comunicación con Electron.
Expone endpoints REST que el proceso principal de Electron consume via HTTP local.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lingualParam.m10_audit import GestorBitacora, anonimizar_paciente
from lingualParam.m6_prescription import (
    cargar_prescripcion_estandar,
    cargar_prescripcion_json,
    guardar_prescripcion_personalizada,
)
from lingualParam.m8_exporter import exportar_todo
from lingualParam.pipeline import ejecutar_pipeline
from lingualParam.types import (
    EstadoCaso,
    ResultadoProcesamiento,
    TipoPrescripcion,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LingualParam-CSM™ IPC Server",
    version="0.1.0",
    description="API local para comunicación Electron ↔ Python",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "app://"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado en memoria (un caso por sesión; extensible a múltiples)
_casos: dict[str, ResultadoProcesamiento] = {}
_bitacora = GestorBitacora()


# ------------------------------------------------------------------
# Schemas Pydantic
# ------------------------------------------------------------------

class SolicitudProcesar(BaseModel):
    id_caso: str
    tipo_prescripcion: str = "STb"
    ruta_prescripcion_personalizada: Optional[str] = None
    ruta_modelo_cnn: Optional[str] = None


class SolicitudExportar(BaseModel):
    id_caso: str
    nombre_paciente: str
    fecha_nacimiento: str
    rut_u_id: str
    directorio_destino: str


class SolicitudAjusteManual(BaseModel):
    id_caso: str
    fdi: int
    campo: str          # "torque_deg" | "angulacion_deg" | "inclinacion_deg"
    valor_nuevo: float
    autor: str
    justificacion: str


class SolicitudPrescripcionPersonalizada(BaseModel):
    nombre: str
    descripcion: str
    referencia: str
    piezas: list[dict]  # [{fdi, T, A, I}]
    ruta_destino: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """Verificación de estado del servidor."""
    return {"estado": "activo", "version": "0.1.0"}


@app.post("/importar")
async def importar(archivo: UploadFile = File(...)) -> dict:
    """
    RF-01, RF-02: Recibe un archivo 3D, lo guarda temporalmente y lo importa.
    """
    from lingualParam.m1_importer import importar_archivo, ErrorImportacion

    sufijo = Path(archivo.filename or "archivo.stl").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        contenido = await archivo.read()
        tmp.write(contenido)
        ruta_tmp = tmp.name

    try:
        malla = importar_archivo(ruta_tmp)
        _bitacora.registrar_evento(
            tipo="importacion",
            autor="sistema",
            descripcion=f"Archivo importado: {archivo.filename}",
            payload={"ruta_tmp": ruta_tmp, "formato": malla.formato},
        )
        return {
            "ok": True,
            "ruta_tmp": ruta_tmp,
            "formato": malla.formato,
            "n_vertices": int(malla.metadata.get("n_vertices", 0)),
            "n_caras": int(malla.metadata.get("n_caras", 0)),
            "arcada": malla.arcada,
            "hash_origen": malla.hash_origen,
        }
    except ErrorImportacion as exc:
        os.unlink(ruta_tmp)
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/procesar")
def procesar(solicitud: SolicitudProcesar) -> dict:
    """
    RF-03..RF-14: Ejecuta el pipeline completo sobre el archivo ya importado.
    """
    # Recuperar ruta del archivo importado desde bitácora o solicitud
    # En este modelo simplificado, el id_caso actúa como clave
    ruta = solicitud.ruta_prescripcion_personalizada  # puede ser None

    try:
        tipo = TipoPrescripcion(solicitud.tipo_prescripcion)
    except ValueError:
        tipo = TipoPrescripcion.PERSONALIZADA

    # La ruta del archivo 3D se recupera del primer evento de importación
    # En una implementación completa, se almacenaría en DB
    raise HTTPException(
        status_code=501,
        detail="Endpoint /procesar requiere ruta_archivo. Use /procesar-con-ruta.",
    )


@app.post("/procesar-con-ruta")
def procesar_con_ruta(
    ruta_archivo: str,
    id_caso: str,
    tipo_prescripcion: str = "STb",
    ruta_modelo_cnn: Optional[str] = None,
) -> dict:
    """Pipeline completo con ruta de archivo explícita."""
    try:
        tipo = TipoPrescripcion(tipo_prescripcion)
    except ValueError:
        tipo = TipoPrescripcion.PERSONALIZADA

    resultado = ejecutar_pipeline(
        ruta_archivo=ruta_archivo,
        tipo_prescripcion=tipo,
        ruta_modelo_cnn=ruta_modelo_cnn,
        id_caso=id_caso,
    )
    _casos[id_caso] = resultado
    _bitacora.registrar_evento(
        tipo="procesamiento",
        autor="sistema",
        descripcion=f"Pipeline ejecutado para caso {id_caso}",
        id_caso=id_caso,
        payload={"n_piezas": len(resultado.piezas), "errores": resultado.errores},
    )
    return {
        "ok": True,
        "id_caso": id_caso,
        "estado": resultado.estado.value,
        "n_piezas": len(resultado.piezas),
        "errores": resultado.errores,
        "advertencias": resultado.advertencias,
    }


@app.get("/caso/{id_caso}")
def obtener_caso(id_caso: str) -> dict:
    """RF-15: Retorna los resultados de un caso procesado."""
    if id_caso not in _casos:
        raise HTTPException(status_code=404, detail=f"Caso {id_caso} no encontrado.")
    caso = _casos[id_caso]

    piezas_serializadas = []
    for r in caso.piezas:
        p = r.pieza
        piezas_serializadas.append({
            "fdi": p.fdi,
            "torque_deg": p.torque_deg,
            "angulacion_deg": p.angulacion_deg,
            "inclinacion_deg": p.inclinacion_deg,
            "distancia_cingular_mm": p.distancia_cingular_mm,
            "delta_t": r.delta_t,
            "delta_a": r.delta_a,
            "delta_i": r.delta_i,
            "grosor_base_mm": r.grosor_base_mm,
            "angulo_slot_deg": r.angulo_slot_deg,
            "ajuste_manual": r.ajuste_manual,
            "justificacion_ajuste": r.justificacion_ajuste,
            "confianza_segmentacion": p.confianza_segmentacion,
            "centroide_lingual": p.centroide_lingual.tolist(),
            "eje_longitudinal": p.eje_longitudinal.tolist(),
            "vector_normal_lingual": p.vector_normal_lingual.tolist(),
        })

    return {
        "id_caso": caso.id_caso,
        "estado": caso.estado.value,
        "prescripcion": caso.prescripcion.nombre if caso.prescripcion else None,
        "piezas": piezas_serializadas,
        "errores": caso.errores,
    }


@app.post("/ajuste-manual")
def ajuste_manual(solicitud: SolicitudAjusteManual) -> dict:
    """RF-16: Aplica un ajuste manual con justificación."""
    if solicitud.id_caso not in _casos:
        raise HTTPException(status_code=404, detail=f"Caso {solicitud.id_caso} no encontrado.")

    caso = _casos[solicitud.id_caso]
    for resultado in caso.piezas:
        if resultado.pieza.fdi == solicitud.fdi:
            valor_original = getattr(resultado.pieza, solicitud.campo, None)
            if valor_original is None:
                raise HTTPException(status_code=400, detail=f"Campo '{solicitud.campo}' no válido.")

            setattr(resultado.pieza, solicitud.campo, round(solicitud.valor_nuevo, 1))
            resultado.ajuste_manual = True
            resultado.justificacion_ajuste = solicitud.justificacion

            _bitacora.registrar_evento(
                tipo="ajuste_manual",
                autor=solicitud.autor,
                descripcion=f"Ajuste FDI {solicitud.fdi}: {solicitud.campo}",
                id_caso=solicitud.id_caso,
                payload={
                    "fdi": solicitud.fdi,
                    "campo": solicitud.campo,
                    "valor_original": valor_original,
                    "valor_nuevo": solicitud.valor_nuevo,
                    "justificacion": solicitud.justificacion,
                },
            )
            return {"ok": True, "fdi": solicitud.fdi, "campo": solicitud.campo}

    raise HTTPException(status_code=404, detail=f"Pieza FDI {solicitud.fdi} no encontrada.")


@app.post("/exportar")
def exportar(solicitud: SolicitudExportar) -> dict:
    """RF-17..RF-21: Exporta el caso en todos los formatos con firma SHA-256."""
    if solicitud.id_caso not in _casos:
        raise HTTPException(status_code=404, detail=f"Caso {solicitud.id_caso} no encontrado.")

    caso = _casos[solicitud.id_caso]
    id_paciente = anonimizar_paciente(
        solicitud.nombre_paciente,
        solicitud.fecha_nacimiento,
        solicitud.rut_u_id,
    )

    Path(solicitud.directorio_destino).mkdir(parents=True, exist_ok=True)
    hashes = exportar_todo(caso, id_paciente, solicitud.directorio_destino)

    caso.hash_dataset = hashes["dataset"]
    caso.estado = EstadoCaso.EXPORTADO

    _bitacora.registrar_evento(
        tipo="exportacion",
        autor="sistema",
        descripcion=f"Caso {solicitud.id_caso} exportado.",
        id_caso=solicitud.id_caso,
        payload={"hashes": hashes, "directorio": solicitud.directorio_destino},
    )
    return {"ok": True, "id_paciente_anonimizado": id_paciente, "hashes": hashes}


@app.get("/historico")
def historico(
    id_caso: Optional[str] = None,
    tipo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limite: int = 100,
) -> dict:
    """RF-25: Consulta el histórico de eventos de la bitácora."""
    eventos = _bitacora.consultar_historico(
        id_caso=id_caso,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limite=limite,
    )
    return {"total": len(eventos), "eventos": eventos}


@app.get("/prescripciones")
def listar_prescripciones() -> dict:
    """Lista las prescripciones estándar disponibles."""
    return {
        "prescripciones": [
            {"tipo": t.value, "nombre": t.value}
            for t in TipoPrescripcion
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
