"""
M3: Segmentación dental por numeración FDI.
CNN 3D stub (modelo entrenado externo, ≥98% accuracy) con fallback geométrico.
RF-04.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import open3d as o3d

from lingualParam.types import MallaImportada, TipoArcada

logger = logging.getLogger(__name__)

# Piezas FDI estándar por arcada
PIEZAS_SUPERIOR: list[int] = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27]
PIEZAS_INFERIOR: list[int] = [31, 32, 33, 34, 35, 36, 37, 41, 42, 43, 44, 45, 46, 47]
TODAS_LAS_PIEZAS: list[int] = PIEZAS_SUPERIOR + PIEZAS_INFERIOR


@dataclass
class SegmentoFDI:
    """Segmento de malla asignado a una pieza FDI."""
    fdi: int
    indices_vertices: np.ndarray    # índices en la malla global
    vertices: np.ndarray            # shape (N, 3)
    caras_locales: np.ndarray       # shape (M, 3) reindexadas localmente
    confianza: float                # 0.0 – 1.0


class ModeloCNN3DStub:
    """
    Stub del modelo CNN 3D para segmentación dental.
    En producción, se reemplaza por el modelo entrenado cargado con PyTorch.
    Accuracy objetivo: ≥98% sobre dataset de validación.
    """

    def __init__(self, ruta_modelo: Optional[str] = None) -> None:
        self.ruta_modelo = ruta_modelo
        self._disponible = False
        if ruta_modelo and Path(ruta_modelo).exists():
            self._cargar_modelo(ruta_modelo)

    def _cargar_modelo(self, ruta: str) -> None:
        """Carga el modelo PyTorch serializado."""
        try:
            import torch
            self._modelo = torch.jit.load(ruta, map_location="cpu")
            self._modelo.eval()
            self._disponible = True
            logger.info("Modelo CNN 3D cargado desde %s", ruta)
        except Exception as exc:
            logger.warning("No se pudo cargar el modelo CNN 3D: %s", exc)

    @property
    def disponible(self) -> bool:
        return self._disponible

    def predecir(self, vertices: np.ndarray) -> np.ndarray:
        """
        Predice la etiqueta FDI por vértice.

        Args:
            vertices: shape (N, 3).

        Returns:
            etiquetas: shape (N,) con el código FDI de cada vértice.
        """
        if not self._disponible:
            raise RuntimeError("Modelo CNN no disponible.")
        import torch
        tensor = torch.tensor(vertices, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            logits = self._modelo(tensor)
            etiquetas = logits.argmax(dim=-1).squeeze(0).numpy()
        return etiquetas


def _segmentacion_geometrica_fallback(
    malla: MallaImportada,
) -> list[SegmentoFDI]:
    """
    Fallback geométrico cuando la CNN no está disponible.
    Usa clustering DBSCAN sobre la nube de puntos para separar dientes
    y asigna números FDI por posición mesiodistal.

    Confianza estimada: ~0.70 (inferior a CNN).
    """
    from sklearn.cluster import DBSCAN

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(malla.vertices)

    # Densidad típica entre dientes: ~1.5 mm de separación
    clustering = DBSCAN(eps=2.5, min_samples=50)
    etiquetas_cluster = clustering.fit_predict(malla.vertices)

    clusters_unicos = sorted(set(etiquetas_cluster) - {-1})
    if not clusters_unicos:
        logger.warning("DBSCAN no encontró clusters; usando diente único.")
        clusters_unicos = [0]
        etiquetas_cluster = np.zeros(len(malla.vertices), dtype=int)

    # Determinar arcada
    arcada = TipoArcada(malla.arcada) if malla.arcada in TipoArcada._value2member_map_ else TipoArcada.AMBAS
    if arcada == TipoArcada.SUPERIOR:
        lista_fdi = PIEZAS_SUPERIOR
    elif arcada == TipoArcada.INFERIOR:
        lista_fdi = PIEZAS_INFERIOR
    else:
        lista_fdi = TODAS_LAS_PIEZAS

    # Ordenar clusters por coordenada X (mesiodistal)
    centroides_x = [
        malla.vertices[etiquetas_cluster == c, 0].mean()
        for c in clusters_unicos
    ]
    clusters_ordenados = [c for _, c in sorted(zip(centroides_x, clusters_unicos))]

    segmentos: list[SegmentoFDI] = []
    for idx_cluster, cluster_id in enumerate(clusters_ordenados):
        if idx_cluster >= len(lista_fdi):
            break
        fdi = lista_fdi[idx_cluster]
        indices = np.where(etiquetas_cluster == cluster_id)[0]
        vertices_diente = malla.vertices[indices]

        # Reindexar caras locales
        mapa = {int(viejo): nuevo for nuevo, viejo in enumerate(indices)}
        caras_validas = []
        for cara in malla.caras:
            if all(int(v) in mapa for v in cara):
                caras_validas.append([mapa[int(v)] for v in cara])

        segmentos.append(SegmentoFDI(
            fdi=fdi,
            indices_vertices=indices,
            vertices=vertices_diente,
            caras_locales=np.array(caras_validas, dtype=np.int32) if caras_validas else np.empty((0, 3), dtype=np.int32),
            confianza=0.70,
        ))

    logger.info("Fallback geométrico: %d piezas detectadas.", len(segmentos))
    return segmentos


def segmentar(
    malla: MallaImportada,
    ruta_modelo_cnn: Optional[str] = None,
) -> list[SegmentoFDI]:
    """
    RF-04: Segmenta las piezas dentales de la malla por numeración FDI.
    Intenta usar la CNN; si no está disponible, usa el fallback geométrico.

    Args:
        malla: Malla pre-procesada (output de M2).
        ruta_modelo_cnn: Ruta al modelo CNN serializado (.pt o .torchscript).

    Returns:
        Lista de SegmentoFDI, uno por diente detectado.
    """
    cnn = ModeloCNN3DStub(ruta_modelo_cnn)

    if cnn.disponible:
        logger.info("Usando modelo CNN 3D para segmentación.")
        etiquetas = cnn.predecir(malla.vertices)
        fdi_unicos = sorted(set(etiquetas.tolist()) - {0})
        segmentos: list[SegmentoFDI] = []
        for fdi in fdi_unicos:
            indices = np.where(etiquetas == fdi)[0]
            vertices_diente = malla.vertices[indices]
            mapa = {int(v): i for i, v in enumerate(indices)}
            caras_validas = [
                [mapa[int(v)] for v in cara]
                for cara in malla.caras
                if all(int(v) in mapa for v in cara)
            ]
            segmentos.append(SegmentoFDI(
                fdi=int(fdi),
                indices_vertices=indices,
                vertices=vertices_diente,
                caras_locales=np.array(caras_validas, dtype=np.int32) if caras_validas else np.empty((0, 3), dtype=np.int32),
                confianza=0.98,
            ))
        return segmentos
    else:
        logger.info("CNN no disponible; usando fallback geométrico DBSCAN.")
        return _segmentacion_geometrica_fallback(malla)
